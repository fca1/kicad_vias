"""Lecture IPC et reconstruction géométrique, sans chargement de pcbnew.

Les formes inconnues sont refusées : ne jamais omettre silencieusement un obstacle.
"""
import json
import math
import re
from shapely.geometry import Point,Polygon,LineString,box
from shapely.ops import unary_union,polygonize_full
from .board_data import BoardSnapshot,ViaData


def sexpr(source):
    stack=[];root=None
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',source):
        if token=='(':
            node=[]
            if stack:stack[-1].append(node)
            else:root=node
            stack.append(node)
        elif token==')':
            if not stack:raise ValueError('Document IPC mal formé.')
            stack.pop()
        else:
            if not stack:raise ValueError('Document IPC mal formé.')
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    if stack or root is None:raise ValueError('Document IPC incomplet.')
    return root


def child(node,key,default=None):
    return next((v for v in node if isinstance(v,list) and v and v[0]==key),default)


def xy(v):return v.x/1000000,v.y/1000000


def curve_points(item):
    a,m,z=xy(item.start),xy(item.mid),xy(item.end)
    d=2*(a[0]*(m[1]-z[1])+m[0]*(z[1]-a[1])+z[0]*(a[1]-m[1]))
    if abs(d)<1e-15:return [a,z]
    qa=sum(v*v for v in a);qm=sum(v*v for v in m);qz=sum(v*v for v in z)
    cx=(qa*(m[1]-z[1])+qm*(z[1]-a[1])+qz*(a[1]-m[1]))/d
    cy=(qa*(z[0]-m[0])+qm*(a[0]-z[0])+qz*(m[0]-a[0]))/d
    r=math.hypot(a[0]-cx,a[1]-cy)
    angles=[math.atan2(v[1]-cy,v[0]-cx) for v in (a,m,z)]
    span=(angles[2]-angles[0])%(2*math.pi)
    if (angles[1]-angles[0])%(2*math.pi)>span:span-=2*math.pi
    step=2*math.acos(max(-1,min(1,1-.001/max(r,.001))))
    count=max(2,math.ceil(abs(span)/max(step,.001)))
    return [a]+[(cx+r*math.cos(angles[0]+span*i/count),cy+r*math.sin(angles[0]+span*i/count)) for i in range(1,count)]+[z]


def polygon(poly):
    def ring(line):
        result=[]
        for node in line.nodes:
            if node.point is None:raise ValueError('Arc de polygone IPC non pris en charge.')
            result.append(xy(node.point))
        return result
    points=ring(poly.outline)
    return Polygon(points,[ring(h) for h in poly.holes]).buffer(0) if len(points)>=3 else Polygon()


def shape_geometry(item,outline=False):
    kind=type(item).__name__.removeprefix('Board')
    width=item.attributes.stroke.width/1000000
    filled=item.attributes.fill.filled
    if kind=='Segment':base=LineString([xy(item.start),xy(item.end)])
    elif kind=='Arc':base=LineString(curve_points(item))
    elif kind=='Rectangle':
        a=xy(item.top_left);z=xy(item.bottom_right);region=box(min(a[0],z[0]),min(a[1],z[1]),max(a[0],z[0]),max(a[1],z[1]))
        base=region if filled and not outline else region.boundary
    elif kind=='Circle':
        region=Point(xy(item.center)).buffer(item.radius()/1000000,resolution=128)
        base=region if filled and not outline else region.boundary
    elif kind=='Polygon':
        region=unary_union([polygon(v) for v in item.polygons]);base=region if filled and not outline else region.boundary
    else:raise ValueError('Forme IPC non prise en charge : '+kind)
    return base if outline else base.buffer(width/2) if width else base


def text_geometry(client,item):
    from kipy.common_types import Text
    return unary_union([shape_geometry(g) for shape in client.get_text_as_shapes(Text(item.proto.text)) for g in shape])


def capture(client,board,opt,exclude=()):
    from kipy.proto.board.board_types_pb2 import BoardLayer as L,SolderMaskMode,PadType
    side=opt.side;front=side=='Top';copper=L.BL_F_Cu if front else L.BL_B_Cu
    mask=L.BL_F_Mask if front else L.BL_B_Mask;silk=L.BL_F_SilkS if front else L.BL_B_SilkS
    shapes=board.get_shapes();texts=board.get_text();footprints=board.get_footprints();vias=board.get_vias()
    source=sexpr(board.get_as_string());setup=child(source,'setup',[])
    expansion=float(child(setup,'pad_to_mask_clearance',['',0])[1])
    tent=child(setup,'tenting',[]);default_tented=child(tent,'front' if front else 'back',['','yes'])[1]=='yes'
    edges=[shape_geometry(it,True) for it in shapes if it.layer==L.BL_Edge_Cuts]
    regions,cuts,dangles,invalid=polygonize_full(edges)
    if not edges or regions.is_empty or not cuts.is_empty or not dangles.is_empty or not invalid.is_empty:
        raise ValueError('Le PCB doit avoir un contour Edge.Cuts fermé et non ambigu.')
    # XOR des anneaux : les contours emboîtés représentent les découpes.
    area=Polygon()
    rings={Polygon(r.exterior).wkb:Polygon(r.exterior) for r in regions.geoms}
    for region in sorted(rings.values(),key=lambda r:-r.area):area=area.symmetric_difference(region)
    bodies=[];apertures=[];silhouettes=[]
    for fp in footprints:
        pads=list(fp.definition.pads);body=[]
        if fp.layer==copper and not fp.reference_field.text.value.upper().startswith(('TP','MH','FID')) and any(p.pad_type!=PadType.PT_NPTH for p in pads):
            body.extend(shape_geometry(it) for it in fp.definition.shapes)
            for pad in pads:
                for layer in pad.padstack.layers:
                    if L.Name(layer).endswith('_Cu'):
                        poly=board.get_pad_shapes_as_polygons(pad,layer)
                        if poly is not None:body.append(polygon(poly))
                drill=pad.padstack.drill.diameter
                if drill.x or drill.y:
                    if drill.x!=drill.y:raise ValueError('Trou oblong : enveloppe IPC à qualifier.')
                    body.append(Point(xy(pad.position)).buffer(drill.x/2000000))
            hull=unary_union(body).convex_hull if body else Point(xy(fp.position)).buffer(1,cap_style=3)
            if not hull.is_empty:bodies.append(hull.buffer(.35))
        for pad in pads:
            if mask not in pad.padstack.layers:continue
            poly=board.get_pad_shapes_as_polygons(pad,mask)
            if poly is None:raise ValueError('Contour de masque de pastille absent.')
            outer=pad.padstack.front_outer_layers if front else pad.padstack.back_outer_layers
            settings=outer.proto.solder_mask_settings
            inherited=fp.overrides.proto.solder_mask
            base=inherited.solder_mask_margin.value_nm/1000000 if inherited.HasField('solder_mask_margin') else expansion
            margin=settings.solder_mask_margin.value_nm/1000000 if settings.HasField('solder_mask_margin') else base
            apertures.append(polygon(poly).buffer(max(0,margin)))
        silhouettes.extend(shape_geometry(it) for it in fp.definition.shapes if it.layer==silk)
        for it in fp.texts_and_fields:
            # La visibilité du champ est distincte de celle de son texte interne.
            if hasattr(it,'text') and not it.proto.visible:continue
            text=it.text if hasattr(it,'text') else it
            if text.layer==silk and text.attributes.visible and text.value:silhouettes.append(text_geometry(client,text))
    via_apertures={};data=[]
    for via in vias:
        outer=via.padstack.front_outer_layers if front else via.padstack.back_outer_layers
        mode=outer.solder_mask_mode
        accessible=copper in via.padstack.layers and (mode==SolderMaskMode.SMM_UNMASKED or (mode in (SolderMaskMode.SMM_UNKNOWN,SolderMaskMode.SMM_FROM_DESIGN_RULES) and not default_tented))
        x,y=xy(via.position);diameter=via.diameter/1000000
        settings=outer.proto.solder_mask_settings
        margin=settings.solder_mask_margin.value_nm/1000000 if settings.HasField('solder_mask_margin') else expansion
        if accessible:via_apertures[via.id.value]=Point(x,y).buffer(diameter/2+margin).buffer(.2)
        data.append(ViaData(via.id.value,via.net.name,x,y,diameter,via.drill_diameter/1000000,margin,accessible))
    excluded=set(exclude)
    for it in shapes:
        if it.id.value in excluded:continue
        if it.layer==silk:silhouettes.append(shape_geometry(it))
        elif it.layer==mask:
            bounds=board.get_item_bounding_box(it)
            apertures.append(box(*xy(bounds.pos),*xy(bounds.pos+bounds.size)))
    for it in texts:
        if it.id.value not in excluded and it.layer==silk and it.attributes.visible:silhouettes.append(text_geometry(client,it))
    fixed=unary_union(bodies+[g.buffer(.2) for g in apertures]+[g.buffer(.2) for g in silhouettes])
    solid=unary_union(bodies+apertures+silhouettes)
    return BoardSnapshot(area,tuple(bodies),fixed,solid,via_apertures,tuple(data))
