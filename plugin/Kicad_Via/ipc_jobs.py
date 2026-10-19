"""Préparation sur le fil GUI ; IPC effectue les écritures dans un fil dédié."""
import os
import uuid
from pathlib import Path
import pcbnew as p
from . import service
from .geometry import uid
from .ipc_native import encode


def generation(board,layer,opt,path):
    if layer not in service.available_layers(board,opt.side):
        raise ValueError('Choisissez une couche utilisateur libre ou appartenant à ce repérage.')
    data=service.state(board); face=data['faces'].get(opt.side,{})
    previous=face.get('preview')
    if previous: service.validate_record(board,previous,True)
    plan=service.prepare(board,layer,opt,service.excluded_ids(data,opt.side))
    if not plan['rows']:
        raise ValueError('Aucun via découvert et accessible sur cette face. Carte et fichier inchangés.')
    name='Kicad_Via_'+opt.side.upper()
    merged=face.get('merged',{})
    old_layer=previous['layer'] if previous else merged.get('source_layer')
    if not previous and old_layer is not None and service.layer_objects(board,old_layer):
        # Le nom ne suffit pas : ne pas récupérer une ancienne couche qui a
        # reçu entre-temps du contenu étranger après la fusion.
        old_layer=None
    # Une migration peut conserver un aperçu ancien ET un repérage fusionné.
    # La source vide de ce dernier garde alors le nom réservé. Seule cette
    # couche connue du registre et restée vide peut rendre son ancien nom.
    reserved=merged.get('source_layer')
    if (reserved not in service.USER_LAYERS or reserved in (layer,old_layer)
            or service.layer_objects(board,reserved) or board.GetLayerName(reserved)!=name):
        reserved=None
    if any(l not in (layer,old_layer,reserved) and board.GetLayerName(l)==name for l in service.USER_LAYERS):
        raise ValueError('Ce nom de couche est déjà utilisé ailleurs : '+name)
    names={layer:name}
    if old_layer is not None and old_layer!=layer:names[old_layer]=(previous or merged)['previous_name']
    if reserved is not None:names[reserved]=merged['previous_name']
    group=str(uuid.uuid4());items=[encode(it) for it in plan['items']]
    output,staged=service.stage_output(path,opt.side,plan['rows'],plan['bounds'])
    record=dict(layer=layer,ids=[uid(it) for it in plan['items']],group=group,
                source_layer=layer,rows=plan['rows'],bounds=plan['bounds'],output=str(output),
                leader_vias=plan['leader_vias'],
                previous_name=previous.get('previous_name',board.GetLayerName(layer))
                if previous and previous['layer']==layer else board.GetLayerName(layer))
    job=dict(mode='génération',name=name,group=group,items=items,updates=[],
             remove_ids=previous['ids'] if previous else [],
             remove_group=previous.get('group') if previous and any(uid(g)==previous.get('group') for g in board.Groups()) else None)
    return Prepared(board,job,opt.side,'preview',record,names,output,staged)


class Prepared:
    def __init__(self,board,job,side,kind,record,names,output=None,staged=None):
        self.board=board;self.job=job;self.side=side;self.kind=kind;self.record=record
        self.names=names;self.old_names={layer:board.GetLayerName(layer) for layer in names}
        self.output=output;self.staged=staged
        self.owner=service.ownership_root()/(record['group']+'.json')
        self.backups={path:path.read_bytes() if path.exists() else None
                      for path in (self.owner,output) if path is not None}
        from kipy.proto.board.board_types_pb2 import BoardLayer
        name=p.BOARD.GetStandardLayerName(record['layer'])
        mapping={'F.Silkscreen':'BL_F_SilkS','B.Silkscreen':'BL_B_SilkS'}
        self.job['target_layers']=[BoardLayer.Value(mapping.get(name,'BL_'+name.replace('.','_')))]
        self.job['expected_vias']={uid(v):(v.GetPosition().x,v.GetPosition().y)
                                   for v in board.GetTracks() if isinstance(v,p.PCB_VIA)}
        self.result=dict(points=len(record['rows']),labels=sum(r['imprime'] for r in record['rows']),
                         layer=names.get(record['layer'],board.GetLayerName(record['layer'])),output=record['output'])

    def rename(self):
        # Seule mutation de carte conservée en natif : noms des couches.
        # Le coordinateur appelle cette méthode sur le fil GUI de KiCad.
        if p.GetBoard() is not None and p.GetBoard()!=self.board:
            raise ValueError('Le document actif a changé.')
        for layer,name in self.names.items():
            if not self.board.SetLayerName(layer,name):raise ValueError('Renommage de couche refusé.')

    def finalize(self):
        if not self.job.get('group'):return
        # Les nouveaux objets IPC n'existent dans BOARD qu'après push_commit.
        objects={uid(it):it for it in self.board.GetDrawings()}
        if not set(self.record['ids']).issubset(objects):
            raise ValueError('Dessins IPC absents du document natif.')
        group=p.PCB_GROUP(self.board);group.SetUuid(p.KIID(self.record['group']))
        group.SetName(self.job['name'])
        for item_id in self.record['ids']:group.AddItem(objects[item_id])
        self.board.Add(group)

    def rollback(self):
        for layer,name in self.old_names.items():self.board.SetLayerName(layer,name)
        for path,content in self.backups.items():
            if content is None:path.unlink(missing_ok=True)
            else:path.write_bytes(content)

    def publish(self):
        service.persist(self.side,self.kind,self.record)
        if self.staged is not None:os.replace(self.staged,self.output)

    def cleanup(self):
        if self.staged is not None:self.staged.unlink(missing_ok=True)


def merging(board,layer,side):
    data=service.state(board); face=data['faces'].get(side,{})
    record=face.get('preview')
    if not record or record['layer']!=layer:
        raise ValueError('Cette couche ne contient pas un repérage Kicad_Via de cette face.')
    items,group=service.validate_record(board,record,True)
    target=p.F_SilkS if side=='Top' else p.B_SilkS
    old_final=face.get('merged')
    if old_final: service.validate_record(board,old_final)
    # Vérifier le placement réel, y compris les déplacements manuels effectués
    # après génération. Ne pas reconstruire le plan : conserver ces ajustements.
    obstacles=service.prepare(board,layer,service.Options(side=side),service.excluded_ids(data,side),obstacles_only=True)
    via_obstacles={}
    for it in items:
        if isinstance(it,p.PCB_TEXT): shape=service.bounds(it)
        elif isinstance(it,p.PCB_SHAPE):
            poly=p.SHAPE_POLY_SET()
            it.TransformShapeToPolygon(poly,layer,0,p.FromMM(.005),p.ERROR_OUTSIDE)
            shape=service.polygons(poly)
        else: raise ValueError('Objet non graphique dans le repérage.')
        occupied=obstacles['occupied']
        via_id=record.get('leader_vias',{}).get(uid(it))
        if via_id:
            if not isinstance(it,p.PCB_SHAPE) or it.GetShape()!=p.SHAPE_T_SEGMENT:
                raise ValueError('Trait de rappel modifié : segment attendu.')
            if via_id not in obstacles['via_apertures']:
                raise ValueError('Le via désigné a disparu ou son accès a changé. Régénérez les labels.')
            if via_id not in via_obstacles:
                via_obstacles[via_id]=service.leader_obstacles(obstacles['fixed'],obstacles['via_apertures'],via_id,obstacles['solid'])
            occupied=via_obstacles[via_id]
        if not obstacles['safe'].covers(shape) or occupied.intersects(shape):
            raise ValueError('Un repère chevauche un obstacle ou la sérigraphie de destination. Ajustez-le avant fusion.')
    updates=[]
    for it in items:
        message=encode(it)
        from kipy.proto.board.board_types_pb2 import BoardLayer
        message.layer=BoardLayer.BL_F_SilkS if side=='Top' else BoardLayer.BL_B_SilkS
        if isinstance(it,p.PCB_TEXT):message.attributes.mirrored=side=='Bottom'
        updates.append(message)
    final=dict(record,layer=target,source_layer=record['layer'])
    job=dict(mode='fusion',name='Kicad_Via_'+side.upper(),items=[],updates=updates,
             remove_ids=old_final['ids'] if old_final else [],
             remove_group=old_final.get('group') if old_final and any(uid(g)==old_final.get('group') for g in board.Groups()) else None)
    return Prepared(board,job,side,'merged',final,{})
