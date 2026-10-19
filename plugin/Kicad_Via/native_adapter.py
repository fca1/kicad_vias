"""Adaptateur natif : capture, métriques KiCad et construction des dessins.

Les enveloppes 2D sont conservatrices. Elles ne qualifient ni le volume d'une
pointe de mesure ni la présence réelle d'un composant sur une carte assemblée.
"""
import math
from collections import defaultdict
import pcbnew as p
from shapely.geometry import Point,Polygon,LineString,box
from shapely.ops import unary_union
from .model import column
from .board_data import ViaData,BoardSnapshot,TextMetrics
from .placement import choose,layout


def mm(n): return p.ToMM(n)
def vec(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def uid(item): return item.m_Uuid.AsString()


def bounds(item):
    b=item.GetBoundingBox()
    return box(mm(b.GetX()),mm(b.GetY()),mm(b.GetRight()),mm(b.GetBottom()))


def polygons(poly):
    parts=[]
    for i in range(poly.OutlineCount()):
        ring=poly.COutline(i)
        coords=[(mm(ring.CPoint(j).x),mm(ring.CPoint(j).y)) for j in range(ring.PointCount())]
        holes=[]
        for h in range(poly.HoleCount(i)):
            ring=poly.CHole(i,h)
            holes.append([(mm(ring.CPoint(j).x),mm(ring.CPoint(j).y)) for j in range(ring.PointCount())])
        if len(coords)>=3: parts.append(Polygon(coords,holes).buffer(0))
    return unary_union(parts)


def silhouette(item,layer):
    """Contour des traits réels : une boîte de texte surestime ses obstacles."""
    poly=p.SHAPE_POLY_SET()
    if hasattr(item,'TransformTextToPolySet'):
        item.TransformTextToPolySet(poly,0,p.FromMM(.005),p.ERROR_OUTSIDE)
    elif isinstance(item,p.PCB_SHAPE):
        item.TransformShapeToPolygon(poly,layer,0,p.FromMM(.005),p.ERROR_OUTSIDE)
    else:
        return bounds(item)
    return polygons(poly)


def text_item(board,text,x,y,size,layer,side):
    it=p.PCB_TEXT(board); it.SetText(text); it.SetLayer(layer)
    it.SetTextSize(vec(size,size)); it.SetTextThickness(p.FromMM(max(.10,size*.16)))
    # KiCad garde l'orientation des textes User même en Flip View.
    # Le miroir physique est réservé aux couches liées à une face.
    it.SetPosition(vec(x,y)); it.SetMirrored(side=='Bottom' and it.IsSideSpecific())
    return it


def line(board,a,b,layer,width=.12):
    it=p.PCB_SHAPE(board); it.SetShape(p.SHAPE_T_SEGMENT); it.SetLayer(layer)
    it.SetStart(vec(*a)); it.SetEnd(vec(*b)); it.SetWidth(p.FromMM(width))
    return it


def capsule(board,region,layer):
    """Ovale en capsule : arcs exacts, sans succession de segments grossiers."""
    x0,y0,x1,y1=region.bounds
    radius=(y1-y0)/2; cy=(y0+y1)/2
    left=x0+radius; right=x1-radius
    result=[line(board,(left,y0),(right,y0),layer),line(board,(left,y1),(right,y1),layer)]
    for start,mid,end in [((right,y0),(x1,cy),(right,y1)),((left,y1),(x0,cy),(left,y0))]:
        arc=p.PCB_SHAPE(board); arc.SetShape(p.SHAPE_T_ARC); arc.SetLayer(layer)
        arc.SetArcGeometry(vec(*start),vec(*mid),vec(*end)); arc.SetWidth(p.FromMM(.12))
        result.append(arc)
    return result


def capture(board,opt,exclude=()):
    exclude=set(exclude)
    copper=p.F_Cu if opt.side=='Top' else p.B_Cu
    mask=p.F_Mask if opt.side=='Top' else p.B_Mask
    silk_layer=p.F_SilkS if opt.side=='Top' else p.B_SilkS
    poly=p.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(poly,False):
        raise ValueError('Le PCB doit avoir un contour Edge.Cuts fermé.')
    area=polygons(poly)
    bodies=[]; apertures=[]; silk=[]
    for fp in board.GetFootprints():
        if fp.GetLayer()==copper and not fp.GetReference().upper().startswith(('TP','MH','FID')):
            if any(pad.GetAttribute()!=p.PAD_ATTRIB_NPTH for pad in fp.Pads()):
                hull=polygons(fp.GetBoundingHull())
                if not hull.is_empty: bodies.append(hull.buffer(.35))
        for pad in fp.Pads():
            if pad.IsOnLayer(mask):
                poly=p.SHAPE_POLY_SET()
                pad.TransformShapeToPolygon(poly,mask,0,p.FromMM(.005))
                g=polygons(poly)
                if not g.is_empty: apertures.append(g.buffer(max(0,mm(pad.GetSolderMaskExpansion(mask)))))
        for it in list(fp.GraphicalItems())+list(fp.GetFields()):
            if it.GetLayer()==silk_layer and (not hasattr(it,'IsVisible') or it.IsVisible()):
                silk.append(silhouette(it,silk_layer))
    vias=[it for it in board.GetTracks() if isinstance(it,p.PCB_VIA)]
    via_apertures={}
    for v in vias:
        if v.IsOnLayer(copper) and not v.IsTented(mask):
            pos=v.GetPosition(); r=mm(v.GetWidth(copper))/2+mm(v.GetSolderMaskExpansion())
            via_apertures[uid(v)]=Point(mm(pos.x),mm(pos.y)).buffer(r).buffer(.2)
    for it in board.GetDrawings():
        if uid(it) in exclude: continue
        if it.GetLayer()==silk_layer: silk.append(silhouette(it,silk_layer))
        elif it.GetLayer()==mask: apertures.append(bounds(it))
    fixed=unary_union(bodies+[g.buffer(.2) for g in apertures]+[g.buffer(.2) for g in silk])
    solid=unary_union(bodies+apertures+silk)
    data=[]
    for v in vias:
        pos=v.GetPosition()
        data.append(ViaData(uid(v),v.GetNetname(),mm(pos.x),mm(pos.y),
                            mm(v.GetWidth(copper)),mm(v.GetDrillValue()),
                            mm(v.GetSolderMaskExpansion()),
                            v.IsOnLayer(copper) and not v.IsTented(mask)))
    return BoardSnapshot(area,tuple(bodies),fixed,solid,via_apertures,tuple(data))


def measure_texts(board,layer,snapshot,chosen,opt):
    """Mesurer avant le calcul : pas d'appel natif dans la boucle de placement."""
    counts=defaultdict(int)
    for row in chosen: counts[row['case']]+=1
    requests={(case+'.'+str(i),opt.label_size)
              for case,count in counts.items() for i in range(1,count+1)}
    if opt.grid:
        xmin,ymin,xmax,ymax=snapshot.area.bounds
        requests.update((column(i),max(.6,opt.label_size)) for i in range(math.ceil((xmax-xmin)/20)))
        requests.update((str(i+1),max(.6,opt.label_size)) for i in range(math.ceil((ymax-ymin)/20)))
    boxes={}
    for text,size in requests:
        it=text_item(board,text,0,0,size,layer,opt.side);b=it.GetBoundingBox()
        boxes[(text,size)]=(b.GetX(),b.GetY(),b.GetRight(),b.GetBottom())
    return TextMetrics(boxes,int(p.pcbIUScale.IU_PER_MM))


def materialize(board,layer,opt,plan):
    """Construire les objets natifs hors carte ; service gère leur transaction."""
    items=[];leaders={}
    for drawing in plan['drawings']:
        kind=drawing['kind']
        if kind=='text':
            items.append(text_item(board,drawing['text'],drawing['x'],drawing['y'],drawing['size'],layer,opt.side))
        elif kind=='capsule':
            items.extend(capsule(board,box(*drawing['bounds']),layer))
        elif kind=='line':
            it=line(board,drawing['a'],drawing['b'],layer);items.append(it)
            if 'via_uuid' in drawing:leaders[uid(it)]=drawing['via_uuid']
        else:raise ValueError('Type de dessin inconnu : '+kind)
    return dict({k:v for k,v in plan.items() if k!='drawings'},items=items,leader_vias=leaders)


def prepare(board,layer,opt,exclude=(),obstacles_only=False):
    snapshot=capture(board,opt,exclude)
    if obstacles_only:
        return dict(occupied=unary_union([snapshot.fixed]+list(snapshot.via_apertures.values())),
                    safe=snapshot.area.buffer(-.3),fixed=snapshot.fixed,
                    solid=snapshot.solid,via_apertures=snapshot.via_apertures)
    chosen=choose(snapshot,opt)
    metrics=measure_texts(board,layer,snapshot,chosen,opt)
    return materialize(board,layer,opt,layout(snapshot,chosen,metrics,opt))
