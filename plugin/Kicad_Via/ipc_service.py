"""Service externe IPC : propriété des objets et transactions, sans SWIG."""
import copy
import json
import os
import uuid
from pathlib import Path
from . import ownership,ipc_capture,ipc_drawing
from .placement import choose,layout,leader_obstacles
from .model import Options
from .ipc_adapter import IPCAdapter,CheckedClient
from shapely.ops import unary_union
from shapely.geometry import box


class Session:
    def __init__(self,client):
        self.client=client;self.board=client.get_board()
        self.board._kicad=CheckedClient(self.board._kicad)
        self.refresh()

    def refresh(self):
        from kipy.proto.board.board_types_pb2 import BoardLayer as L
        self.source=self.board.get_as_string()
        root=ipc_capture.sexpr(self.source)
        import hashlib
        self.board_id=hashlib.sha256('|'.join(sorted(v.id.value for v in self.board.get_vias())).encode()).hexdigest()
        self.native_to_ipc={};self.ipc_to_native={};self.names={}
        for entry in ipc_capture.child(root,'layers',[])[1:]:
            name=entry[1];enum=L.Value('BL_'+name.replace('.','_'))
            native=int(entry[0]);self.native_to_ipc[native]=enum;self.ipc_to_native[enum]=native
            self.names[enum]=entry[3] if len(entry)>3 else name
        self.user_layers=[v for v in self.names if L.Name(v).startswith('BL_User_')]
        self.groups={g.id.value:g for g in self.board.get_groups()}
        all_items=list(self.board.get_shapes())+list(self.board.get_text())
        for method in ('get_textboxes','get_text_boxes','get_dimensions'):
            if hasattr(self.board,method):all_items.extend(getattr(self.board,method)())
        for footprint in self.board.get_footprints():
            all_items.extend(footprint.definition.items)
            all_items.extend(it.text if hasattr(it,'text') else it for it in footprint.texts_and_fields)
        self.objects={it.id.value:it for it in all_items if hasattr(it,'id') and hasattr(it,'layer')}
        self.faces={}
        for path in ownership.ownership_root().glob('*.json'):
            try:owner=json.loads(path.read_text(encoding='utf-8'))
            except (OSError,ValueError):
                if path.stem in self.groups:raise ValueError('Registre illisible : '+str(path))
                continue
            if owner.get('schema')!=1:raise ValueError('Registre inconnu : '+str(path))
            record=owner['record'];ids=set(record['ids']);present=ids.intersection(self.objects)
            if not present and not (not ids and (record['group'] in self.groups or
                    (record.get('board_id') and record.get('board_id')==self.board_id))):continue
            layer=self.native_to_ipc.get(record['layer'])
            observed={self.objects[i].layer for i in present}
            kind=owner['kind']
            if len(observed)==1:
                actual=next(iter(observed))
                if actual in self.user_layers:kind='preview';layer=actual
                elif actual==(L.BL_F_SilkS if owner['side']=='Top' else L.BL_B_SilkS):kind='merged';layer=actual
            record=dict(record,layer=self.ipc_to_native[layer])
            face=self.faces.setdefault(owner['side'],{})
            if kind in face:raise ValueError('Plusieurs repérages concurrents pour cette face.')
            face[kind]=record

    def validate(self,record,strict=False):
        ids=set(record['ids']);layer=self.native_to_ipc[record['layer']]
        if not ids.issubset(self.objects):raise ValueError('Un ancien dessin manque : remplacement refusé.')
        items=[self.objects[i] for i in record['ids']]
        if any(it.layer!=layer for it in items):raise ValueError('Des repères ont changé de couche séparément.')
        if strict and {i.id.value for i in self.objects.values() if i.layer==layer}!=ids:
            raise ValueError('La couche contient des objets étrangers.')
        group=self.groups.get(record['group'])
        if group and {v.value for v in group.proto.items}!=ids:raise ValueError('Le groupe a été modifié.')
        for other in self.groups.values():
            if other.id.value!=record['group'] and ids.intersection(v.value for v in other.proto.items):
                raise ValueError('Des repères appartiennent à un groupe étranger.')
        return items

    def available_layers(self,side):
        result=[];record=self.faces.get(side,{}).get('preview')
        for layer in self.user_layers:
            if self.names[layer]!='Kicad_Via_'+side.upper():continue
            objects=[it for it in self.objects.values() if it.layer==layer]
            if objects and not (record and self.native_to_ipc[record['layer']]==layer):continue
            if record and self.native_to_ipc[record['layer']]==layer:
                try:self.validate(record,True)
                except ValueError:continue
            result.append(layer)
        return result

    def excluded(self,side):
        return [item for record in self.faces.get(side,{}).values() for item in record['ids']]

    def apply(self,job,record,side,kind,staged=None,output=None):
        from kipy.board_types import Group
        from kipy.proto.common.types import KIID
        owner=ownership.ownership_root()/(record['group']+'.json')
        backups={p:p.read_bytes() if p.exists() else None for p in (owner,output) if p is not None}
        def publish():
            ownership.persist(side,kind,record)
            if staged:os.replace(staged,output)
        def restore():
            for p,data in backups.items():
                if data is None:p.unlink(missing_ok=True)
                else:p.write_bytes(data)
        def finalize():
            if not job['items']:return
            # Build 2520 : les membres sont résolus uniquement après push.
            group=Group();group.id.value=record['group'];group.proto.name='Kicad_Via_'+side.upper()
            group.proto.items.extend(KIID(value=i) for i in record['ids'])
            self.board.create_items(group)
            actual={g.id.value:g for g in self.board.get_groups()}.get(record['group'])
            if actual is None or {i.value for i in actual.proto.items}!=set(record['ids']):
                raise RuntimeError('Groupe IPC incomplet.')
        job['expected_vias']={v.id.value:(v.position.x,v.position.y) for v in self.board.get_vias()}
        # Détecter les modifications entre lecture et application, y compris les
        # composants/masques. Aucune commande ne recharge ni ne sauvegarde la carte.
        if self.board.get_as_string()!=self.source:raise ValueError('La carte a changé pendant le calcul. Relancez.')
        try:IPCAdapter(self.board).apply(job,rollback=restore,publish=publish,finalize=finalize)
        finally:
            if staged:staged.unlink(missing_ok=True)
        self.refresh()
        return dict(points=len(record['rows']),labels=sum(r['imprime'] for r in record['rows']),output=record['output'])

    def generate(self,side,layer,size,grid,path):
        self.refresh();opt=Options(side=side,label_size=size,grid=grid)
        if layer not in self.available_layers(side):raise ValueError('Renommez une couche libre Kicad_Via_'+side.upper()+' dans KiCad, puis actualisez.')
        previous=self.faces.get(side,{}).get('preview')
        if previous:self.validate(previous,True)
        snapshot=ipc_capture.capture(self.client,self.board,opt,self.excluded(side))
        selected=choose(snapshot,opt)
        if not selected:raise ValueError('Aucun via découvert accessible sur cette face.')
        plan=layout(snapshot,selected,ipc_drawing.measure_texts(self.client,snapshot,selected,opt),opt)
        material=ipc_drawing.materialize(plan,layer,opt)
        output,staged=ownership.stage_output(path,side,plan['rows'],plan['bounds'])
        record=dict(layer=self.ipc_to_native[layer],source_layer=self.ipc_to_native[layer],
                    ids=[it.id.value for it in material['items']],group=str(uuid.uuid4()),
                    board_id=self.board_id,rows=plan['rows'],bounds=plan['bounds'],output=str(output),
                    leader_vias=material['leader_vias'],previous_name=self.names[layer])
        job=dict(mode='génération IPC',items=material['items'],updates=[],target_layers=[layer],
                 remove_ids=previous['ids'] if previous else [],
                 remove_group=previous['group'] if previous and previous['group'] in self.groups else None)
        return self.apply(job,record,side,'preview',staged,output)

    def merge(self,side,layer):
        from kipy.board_types import BoardText
        from kipy.proto.board.board_types_pb2 import BoardLayer as L
        self.refresh();record=self.faces.get(side,{}).get('preview')
        if not record or self.native_to_ipc[record['layer']]!=layer:raise ValueError('Aucun aperçu sur cette couche.')
        items=self.validate(record,True);old=self.faces.get(side,{}).get('merged')
        if old:self.validate(old)
        snapshot=ipc_capture.capture(self.client,self.board,Options(side=side),self.excluded(side))
        occupied=unary_union([snapshot.fixed]+list(snapshot.via_apertures.values()));safe=snapshot.area.buffer(-.3)
        target=L.BL_F_SilkS if side=='Top' else L.BL_B_SilkS
        updates=[]
        for it in items:
            if isinstance(it,BoardText):
                bb=self.board.get_item_bounding_box(it)
                shape=box(bb.pos.x/1e6,bb.pos.y/1e6,(bb.pos.x+bb.size.x)/1e6,(bb.pos.y+bb.size.y)/1e6)
            else:shape=ipc_capture.shape_geometry(it)
            test=occupied;via=record.get('leader_vias',{}).get(it.id.value)
            if via:
                if via not in snapshot.via_apertures:raise ValueError('Accès du via modifié ; régénérez.')
                test=leader_obstacles(snapshot.fixed,snapshot.via_apertures,via,snapshot.solid)
            if not safe.covers(shape) or test.intersects(shape):raise ValueError('Repère en collision : ajustez avant fusion.')
            item=copy.deepcopy(it);item.layer=target
            if isinstance(item,BoardText):item.attributes.mirrored=side=='Bottom'
            updates.append(item)
        final=dict(record,layer=self.ipc_to_native[target],source_layer=record['layer'])
        job=dict(mode='fusion IPC',items=[],updates=updates,target_layers=[target],remove_ids=old['ids'] if old else [],
                 remove_group=old['group'] if old and old['group'] in self.groups else None)
        return self.apply(job,final,side,'merged')
