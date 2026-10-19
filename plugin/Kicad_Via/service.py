"""Propriété des couches, régénération, fusion et export du tableau .md."""
import json
import os
import string
from pathlib import Path
import tempfile
import pcbnew as p
from .geometry import prepare,uid,polygons,bounds,leader_obstacles
from .model import Options,markdown_path

from .ownership import ownership_root,persist,stage_output

USER_LAYERS=[getattr(p,'User_'+str(i)) for i in range(1,46) if hasattr(p,'User_'+str(i))]


def state(board):
    # BOARD.GetProperties n'est pas un stockage durable fiable sur une carte
    # associée à un projet : SaveBoard le resynchronise. Le registre local
    # est indexé par UUID de groupe et ne dépend ni du chemin ni du nom du PCB.
    data={'schema':1,'faces':{}}
    objects={uid(it):it for it in all_objects(board)}
    present=set(objects)
    group_ids={uid(g) for g in board.Groups()}
    for path in ownership_root().glob('*.json'):
        try: owner=json.loads(path.read_text(encoding='utf-8'))
        except (OSError,ValueError):
            if path.stem in group_ids: raise ValueError('Registre de ce repérage illisible : '+str(path))
            continue
        if owner.get('schema')!=1: raise ValueError('Registre Kicad_Via non reconnu : '+str(path))
        record=owner['record']
        # Un tableau entièrement fantôme possède un groupe vide identifié.
        if not present.intersection(record['ids']) and not (
                not record['ids'] and record.get('group') in group_ids): continue
        # Annuler/rétablir une fusion déplace les mêmes UUID entre User et Silk.
        # Déduire leur état effectif au lieu de supposer le registre synchronisé
        # avec l'historique natif (qui n'annule pas les fichiers externes).
        layers={objects[i].GetLayer() for i in present.intersection(record['ids'])}
        kind=owner['kind']
        if len(layers)==1:
            actual=next(iter(layers))
            target=p.F_SilkS if owner['side']=='Top' else p.B_SilkS
            if actual in USER_LAYERS: kind='preview';record=dict(record,layer=actual)
            elif actual==target: kind='merged';record=dict(record,layer=actual)
        face=data['faces'].setdefault(owner['side'],{})
        if kind in face: raise ValueError('Plusieurs repérages concurrents pour cette face.')
        face[kind]=record
    return data


def all_objects(board):
    return (list(board.GetDrawings())+list(board.GetTracks())+list(board.Zones())+
            [it for fp in board.GetFootprints() for it in list(fp.GraphicalItems())+list(fp.GetFields())+list(fp.Pads())])


def layer_objects(board,layer):
    return [it for it in all_objects(board) if it.IsOnLayer(layer)]


def excluded_ids(data,side):
    face=data['faces'].get(side,{})
    return [i for key in ('preview','merged') for i in face.get(key,{}).get('ids',[])]


def validate_record(board,record,strict_layer=False):
    if not record: return [],None
    objects={uid(it):it for it in all_objects(board)}
    ids=set(record['ids'])
    if not ids.issubset(objects):
        raise ValueError('Un ancien objet Kicad_Via manque. Annulez sa suppression ou utilisez une autre carte.')
    items=[objects[i] for i in record['ids']]
    if any(it.GetLayer()!=record['layer'] for it in items):
        raise ValueError('Des objets Kicad_Via ont changé de couche séparément : opération refusée.')
    if strict_layer and {uid(it) for it in layer_objects(board,record['layer'])}!=ids:
        raise ValueError('La couche contient des objets étrangers à Kicad_Via : opération refusée.')
    groups={uid(g):g for g in board.Groups()}
    group=groups.get(record.get('group'))
    if group is not None and {uid(it) for it in group.GetItems()}!=ids:
        raise ValueError('Le groupe contient des objets étrangers ou a été modifié : opération refusée.')
    # Un groupe dissocié manuellement est permis : les UUID des graphismes
    # restent la référence de propriété, jamais le nom de la couche seul.
    for g in board.Groups():
        if group is not None and uid(g)==uid(group): continue
        if any(uid(it) in ids for it in g.GetItems()):
            raise ValueError('Un repère appartient à un autre groupe : opération refusée.')
    return items,group


def available_layers(board,side):
    data=state(board); result=[]
    for layer in USER_LAYERS:
        existing=layer_objects(board,layer)
        record=data['faces'].get(side,{}).get('preview',{})
        owned=record and record.get('layer')==layer
        if existing and not owned: continue
        if owned:
            try: validate_record(board,record,True)
            except ValueError: continue
        # Une couche vide réservée à l'autre face ne devient pas disponible.
        if any(f!=side and v.get('preview',{}).get('layer')==layer for f,v in data['faces'].items()):
            continue
        result.append(layer)
    return result


def remove_record(board,record):
    items,group=validate_record(board,record)
    if group is not None: board.Remove(group)
    for it in items: board.Remove(it)
    return items,group


def restore_record(board,removed):
    if not removed: return
    items,group=removed
    for it in items: board.Add(it)
    if group is not None: board.Add(group)


def generate(board,layer,opt,path):
    if layer not in available_layers(board,opt.side):
        raise ValueError('Choisissez une couche utilisateur libre ou appartenant à ce repérage.')
    data=state(board); face=data['faces'].get(opt.side,{})
    previous=face.get('preview')
    if previous: validate_record(board,previous,True)
    plan=prepare(board,layer,opt,excluded_ids(data,opt.side))
    if not plan['rows']:
        raise ValueError('Aucun via découvert et accessible sur cette face. Carte et fichier inchangés.')
    output,staged=stage_output(path,opt.side,plan['rows'],plan['bounds'])
    name='Kicad_Via_'+opt.side.upper()
    merged=face.get('merged',{})
    old_layer=previous['layer'] if previous else merged.get('source_layer')
    if not previous and old_layer is not None and layer_objects(board,old_layer):
        # Le nom ne suffit pas : ne pas récupérer une ancienne couche qui a
        # reçu entre-temps du contenu étranger après la fusion.
        old_layer=None
    # Une migration peut conserver un aperçu ancien ET un repérage fusionné.
    # La source vide de ce dernier garde alors le nom réservé. Seule cette
    # couche connue du registre et restée vide peut rendre son ancien nom.
    reserved=merged.get('source_layer')
    if (reserved not in USER_LAYERS or reserved in (layer,old_layer)
            or layer_objects(board,reserved) or board.GetLayerName(reserved)!=name):
        reserved=None
    if any(l not in (layer,old_layer,reserved) and board.GetLayerName(l)==name for l in USER_LAYERS):
        staged.unlink(missing_ok=True)
        raise ValueError('Ce nom de couche est déjà utilisé ailleurs : '+name)
    enabled=p.LSET(board.GetEnabledLayers()); visible=p.LSET(board.GetVisibleLayers())
    old_name=board.GetLayerName(layer); removed=None; group=None; added=[]
    previous_layer_name=board.GetLayerName(old_layer) if old_layer is not None else None
    reserved_name=board.GetLayerName(reserved) if reserved is not None else None
    try:
        # Renommer n'est pas proposé par IPC dans KiCad 10.0.7 : API native.
        layers=board.GetEnabledLayers(); layers.AddLayer(layer); board.SetEnabledLayers(layers)
        if previous: removed=remove_record(board,previous)
        if old_layer is not None and old_layer!=layer:
            board.SetLayerName(old_layer,(previous or merged)['previous_name'])
        if reserved is not None:
            if not board.SetLayerName(reserved,merged['previous_name']):
                raise ValueError('KiCad refuse de libérer le nom de l’ancienne couche vide.')
        if not board.SetLayerName(layer,name): raise ValueError('KiCad refuse le nom de couche.')
        for it in plan['items']: board.Add(it); added.append(it)
        group=p.PCB_GROUP(board); group.SetName(name)
        for it in added: group.AddItem(it)
        board.Add(group)
        face['preview']=dict(layer=layer,ids=[uid(it) for it in added],group=uid(group),
                             source_layer=layer,
                             rows=plan['rows'],bounds=plan['bounds'],output=str(output),
                             leader_vias=plan['leader_vias'],
                             previous_name=previous.get('previous_name',old_name) if previous and previous['layer']==layer else old_name)
        shown=board.GetVisibleLayers(); shown.AddLayer(layer); board.SetVisibleLayers(shown)
        # Enregistrer la propriété avant de publier le tableau. Si la deuxième
        # publication échoue, la nouvelle entrée est retirée lors du rollback.
        persist(opt.side,'preview',face['preview'])
        os.replace(staged,output)
    except BaseException:
        if group is not None: board.Remove(group)
        for it in added: board.Remove(it)
        restore_record(board,removed)
        if group is not None: (ownership_root()/(uid(group)+'.json')).unlink(missing_ok=True)
        board.SetLayerName(layer,old_name)
        if old_layer is not None and old_layer!=layer: board.SetLayerName(old_layer,previous_layer_name)
        if reserved is not None: board.SetLayerName(reserved,reserved_name)
        board.SetEnabledLayers(enabled); board.SetVisibleLayers(visible)
        staged.unlink(missing_ok=True)
        raise
    return dict(points=len(plan['rows']),labels=plan['printed'],layer=name,output=str(output))


def merge(board,layer,side):
    data=state(board); face=data['faces'].get(side,{})
    record=face.get('preview')
    if not record or record['layer']!=layer:
        raise ValueError('Cette couche ne contient pas un repérage Kicad_Via de cette face.')
    items,group=validate_record(board,record,True)
    target=p.F_SilkS if side=='Top' else p.B_SilkS
    old_final=face.get('merged')
    if old_final: validate_record(board,old_final)
    # Vérifier le placement réel, y compris les déplacements manuels effectués
    # après génération. Ne pas reconstruire le plan : conserver ces ajustements.
    obstacles=prepare(board,layer,Options(side=side),excluded_ids(data,side),obstacles_only=True)
    via_obstacles={}
    for it in items:
        if isinstance(it,p.PCB_TEXT): shape=bounds(it)
        elif isinstance(it,p.PCB_SHAPE):
            poly=p.SHAPE_POLY_SET()
            it.TransformShapeToPolygon(poly,layer,0,p.FromMM(.005),p.ERROR_OUTSIDE)
            shape=polygons(poly)
        else: raise ValueError('Objet non graphique dans le repérage.')
        occupied=obstacles['occupied']
        via_id=record.get('leader_vias',{}).get(uid(it))
        if via_id:
            if not isinstance(it,p.PCB_SHAPE) or it.GetShape()!=p.SHAPE_T_SEGMENT:
                raise ValueError('Trait de rappel modifié : segment attendu.')
            if via_id not in obstacles['via_apertures']:
                raise ValueError('Le via désigné a disparu ou son accès a changé. Régénérez les labels.')
            if via_id not in via_obstacles:
                via_obstacles[via_id]=leader_obstacles(obstacles['fixed'],obstacles['via_apertures'],via_id,obstacles['solid'])
            occupied=via_obstacles[via_id]
        if not obstacles['safe'].covers(shape) or occupied.intersects(shape):
            raise ValueError('Un repère chevauche un obstacle ou la sérigraphie de destination. Ajustez-le avant fusion.')
    removed=None
    mirrors={uid(it):it.IsMirrored() for it in items if isinstance(it,p.PCB_TEXT)}
    try:
        if old_final: removed=remove_record(board,old_final)
        for it in items:
            it.SetLayer(target)
            if isinstance(it,p.PCB_TEXT): it.SetMirrored(side=='Bottom')
        face['merged']=dict(record,layer=target,source_layer=record['layer'])
        del face['preview']; persist(side,'merged',face['merged'])
    except BaseException:
        for it in items:
            it.SetLayer(layer)
            if isinstance(it,p.PCB_TEXT): it.SetMirrored(mirrors[uid(it)])
        restore_record(board,removed); raise
    return dict(points=len(record['rows']),labels=sum(r['imprime'] for r in record['rows']),
                layer=board.GetLayerName(target),output=record['output'])
