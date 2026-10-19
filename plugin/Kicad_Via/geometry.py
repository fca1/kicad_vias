"""Sélection et placement sur copie géométrique ; aucune écriture sur la carte.

Les enveloppes 2D sont conservatrices. Elles ne qualifient ni le volume d'une
pointe de mesure ni la présence réelle d'un composant sur une carte assemblée.
"""
import math
from collections import defaultdict
import pcbnew as p
from shapely.geometry import Point,Polygon,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.affinity import translate
from shapely.strtree import STRtree
from shapely.prepared import prep
from .model import coordinates,cell,column,number_unprinted


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


def leader_obstacles(fixed,via_apertures,via_id,solid):
    """Exempter seulement l'ouverture du via désigné, jamais ses voisins.

    Près du centre, relâcher aussi les marges ajoutées aux obstacles fixes,
    mais réintroduire leurs contours réels : aucune pastille ni inscription
    superposée ne doit disparaître avec l'exception du via.
    """
    local=via_apertures[via_id]
    return unary_union([fixed.difference(local),solid]+[g for key,g in via_apertures.items() if key!=via_id])


class CollisionIndex:
    """Tester une union sans reconstruire ses contours à chaque ajout.

    Intersecter une union équivaut à intersecter au moins un de ses membres,
    contacts de frontières compris. L'index filtre seulement les boîtes ; les
    prédicats exacts et toutes les marges restent ceux du placement initial.
    Les ajouts sont peu nombreux et préparés séparément, sans rebâtir l'index.
    """
    def __init__(self,geometries):
        geometries=list(geometries)
        self.tree=STRtree(geometries)
        self.fixed=[prep(g) for g in geometries]
        self.added=[]

    def add(self,geometry):
        self.added.append(prep(geometry))

    def intersects(self,geometry):
        return (any(self.fixed[i].intersects(geometry) for i in self.tree.query(geometry))
                or any(g.intersects(geometry) for g in self.added))


def prepare(board,layer,opt,exclude=(),obstacles_only=False):
    exclude=set(exclude)
    copper=p.F_Cu if opt.side=='Top' else p.B_Cu
    mask=p.F_Mask if opt.side=='Top' else p.B_Mask
    silk_layer=p.F_SilkS if opt.side=='Top' else p.B_SilkS
    poly=p.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(poly,False):
        raise ValueError('Le PCB doit avoir un contour Edge.Cuts fermé.')
    area=polygons(poly); safe=area.buffer(-.3); ext=area.bounds
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
    body_union=unary_union(bodies)
    fixed=unary_union(bodies+[g.buffer(.2) for g in apertures]+[g.buffer(.2) for g in silk])
    solid=unary_union(bodies+apertures+silk)
    if obstacles_only:
        occupied=unary_union([fixed]+list(via_apertures.values()))
        return dict(occupied=occupied,safe=safe,fixed=fixed,solid=solid,via_apertures=via_apertures)
    occupied=CollisionIndex([fixed]+list(via_apertures.values()))
    bynet=defaultdict(list)
    for v in vias:
        if not v.GetNetname() or not v.IsOnLayer(copper) or v.IsTented(mask): continue
        pos=v.GetPosition(); x,y=mm(pos.x),mm(pos.y); r=mm(v.GetWidth(copper))/2
        access=Point(x,y).buffer(r+.25)
        if not safe.covers(access) or body_union.intersects(access): continue
        clearance=min(Point(x,y).distance(body_union) if not body_union.is_empty else 100,
                      Point(x,y).distance(area.boundary))
        bynet[v.GetNetname()].append((clearance,r,x,y,v))
    chosen=[]
    for net,candidates in bynet.items():
        score,r,x,y,v=min(candidates,key=lambda c:(-c[0],-c[1],c[2],c[3]))
        xx,yy=coordinates(x,y,ext,opt.side)
        chosen.append(dict(net=net,via=v,x=x,y=y,xx=xx,yy=yy,radius=r,
                           case=cell(x,y,ext,opt.side)))
    # Les suffixes suivent les positions dans chaque case, jamais l'ordre des nets.
    bins=defaultdict(list)
    for row in chosen: bins[row['case']].append(row)
    for key,rows in bins.items():
        for i,row in enumerate(sorted(rows,key=lambda r:(r['xx'],r['yy'],r['net'])),1):
            row['label']=f'{key}.{i}'
    chosen.sort(key=lambda r:(int(r['xx']//20),int(r['yy']//20),r['xx'],r['yy'],r['net']))
    additions=[]; printed=[]; records=[]; protections=[]; leader_vias={}; label_items={}
    # Réserver la taille de tous les numéros possibles de la case : les visibles
    # peuvent changer de suffixe après regroupement de leurs voisins masqués.
    dimensions={}
    for case,members in bins.items():
        sizes=[bounds(text_item(board,case+'.'+str(i),0,0,opt.label_size,layer,opt.side)).bounds
               for i in range(1,len(members)+1)]
        dimensions[case]=(max(b[2]-b[0] for b in sizes),max(b[3]-b[1] for b in sizes))

    def free(g):
        return safe.covers(g) and not occupied.intersects(g)

    for row in chosen:
        x,y=row['x'],row['y']; label=row['label']
        neighbor=None
        pos=None; leader_path=[]
        # Garder la différence locale exacte de l'ancien calcul : seule
        # l'union coûteuse disparaît, pas l'exception près du centre du via.
        via_id=uid(row['via'])
        route_occupied=CollisionIndex([fixed.difference(via_apertures[via_id]),solid]
                                     +[g for key,g in via_apertures.items() if key!=via_id]
                                     +protections)
        width,height=dimensions[row['case']]
        half_height=height/2+.2
        half_width=max(width/2+.25,half_height+.1)
        core=LineString([(-half_width+half_height,0),(half_width-half_height,0)])
        oval=core.buffer(half_height,quad_segs=20)
        # Le trait de rappel est obligatoire. On peut décaler le drapeau,
        # mais pas l'imprimer sans désigner son via dans une zone dense.
        for distance in [1.5+.5*i for i in range(18)]:
            for angle in range(0,360,15):
                a=math.radians(angle); tx=x+distance*math.cos(a); ty=y+distance*math.sin(a)
                shape=translate(oval,tx,ty)
                if not free(shape.buffer(.15)): continue
                end=nearest_points(Point(x,y),shape.boundary)[1]
                d=math.hypot(end.x-x,end.y-y)
                min_label_distance=row['radius']+max(0,mm(row['via'].GetSolderMaskExpansion()))+.32
                if d<=min_label_distance+.15: continue
                start=(x,y)
                routes=[ [start,(end.x,end.y)],
                         [start,(start[0],end.y),(end.x,end.y)],
                         [start,(end.x,start[1]),(end.x,end.y)] ]
                path=next((r for r in routes if safe.covers(LineString(r).buffer(.08))
                           and not route_occupied.intersects(LineString(r).buffer(.08))),None)
                if path is None: continue
                pos=(tx,ty); leader_path=path
                label_items[uid(row['via'])]=text_item(board,label,tx,ty,opt.label_size,layer,opt.side)
                additions.append(label_items[uid(row['via'])])
                additions.extend(capsule(board,shape,layer))
                for a,b in zip(path,path[1:]):
                    if a==b: continue
                    leader=line(board,a,b,layer);additions.append(leader)
                    leader_vias[uid(leader)]=uid(row['via'])
                protected=unary_union([shape.buffer(.2),LineString(path).buffer(.18)])
                occupied.add(protected); protections.append(protected)
                printed.append(row)
                break
            if pos: break
        # Un accès sans place reste dans le tableau. Son ancrage et son numéro
        # sont calculés après tous les placements, même si le visible vient après.
        v=row['via']
        records.append(dict(face=opt.side,repere=label,net=row['net'],case=row['case'],
                            x_mm=round(row['xx'],4),y_mm=round(row['yy'],4),
                            kicad_x_mm=row['x'],kicad_y_mm=row['y'],via_uuid=uid(v),
                            diametre_mm=mm(v.GetWidth(copper)),percage_mm=mm(v.GetDrillValue()),
                            imprime=pos is not None,voisin=neighbor['label'] if neighbor else '',
                            ecart_x_mm=round(row['xx']-neighbor['xx'],4) if neighbor else '',
                            ecart_y_mm=round(row['yy']-neighbor['yy'],4) if neighbor else '',
                            label_xy=pos,rappel=leader_path))

    def grid_text(text,x,y):
        it=text_item(board,text,x,y,max(.6,opt.label_size),layer,opt.side)
        g=bounds(it).buffer(.15)
        if free(g):
            additions.append(it); occupied.add(g); return True
        return False

    if opt.grid:
        xmin,ymin,xmax,ymax=ext
        # Lettres et chiffres désignent les cases, leurs inscriptions sont posées
        # avant les tirets afin que la grille s'interrompe aussi autour d'elles.
        for i in range(math.ceil((xmax-xmin)/20)):
            x=xmin+min(i*20+10,xmax-xmin-1) if opt.side=='Top' else xmax-min(i*20+10,xmax-xmin-1)
            for y in (ymax-1.2,ymin+1.2):
                if grid_text(column(i),x,y): break
        for i in range(math.ceil((ymax-ymin)/20)):
            y=ymax-min(i*20+10,ymax-ymin-1)
            for x in (xmin+1.2,xmax-1.2):
                if grid_text(str(i+1),x,y): break
        for i in range(1,math.ceil((xmax-xmin)/20)):
            x=xmin+i*20 if opt.side=='Top' else xmax-i*20
            for n in range(math.ceil((ymax-ymin)/2)):
                y=ymin+.5+n*2
                g=LineString([(x,y),(x,y+.6)]).buffer(.14)
                if free(g): additions.append(line(board,(x,y),(x,y+.6),layer))
        for i in range(1,math.ceil((ymax-ymin)/20)):
            y=ymax-i*20
            for n in range(math.ceil((xmax-xmin)/2)):
                x=xmin+.5+n*2
                g=LineString([(x,y),(x+.6,y)]).buffer(.14)
                if free(g): additions.append(line(board,(x,y),(x+.6,y),layer))
    numbered=number_unprinted(records)
    for record in numbered:
        if record['imprime']:label_items[record['via_uuid']].SetText(record['repere'])
    return dict(items=additions,rows=numbered,bounds=list(ext),side=opt.side,leader_vias=leader_vias,
                count_vias=len(vias),printed=len(printed),protections=protections)
