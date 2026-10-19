"""Moteur de placement pur : aucun objet KiCad, aucun accès à la carte.

Entrée : instantané géométrique et métriques de police. Sortie : plan déclaratif
texte/ligne/capsule, tableau et protections. Un adaptateur applique le plan.
"""
import math
from collections import defaultdict
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
from shapely.affinity import translate
from shapely.strtree import STRtree
from shapely.prepared import prep
from .model import coordinates,cell,column,number_unprinted

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


def choose(snapshot,opt):
    area=snapshot.area; safe=area.buffer(-.3); ext=area.bounds
    body_union=unary_union(snapshot.bodies)
    bynet=defaultdict(list)
    for v in snapshot.vias:
        if not v.net or not v.accessible: continue
        x,y=v.x,v.y; r=v.diameter/2
        access=Point(x,y).buffer(r+.25)
        if not safe.covers(access) or body_union.intersects(access): continue
        clearance=min(Point(x,y).distance(body_union) if not body_union.is_empty else 100,
                      Point(x,y).distance(area.boundary))
        bynet[v.net].append((clearance,r,x,y,v))
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
    return chosen

def layout(snapshot,chosen,metrics,opt):
    area=snapshot.area; safe=area.buffer(-.3); ext=area.bounds
    fixed=snapshot.fixed; solid=snapshot.solid; via_apertures=snapshot.via_apertures
    occupied=CollisionIndex([fixed]+list(via_apertures.values()))
    bins=defaultdict(list)
    for row in chosen: bins[row['case']].append(row)
    additions=[]; printed=[]; records=[]; protections=[]; label_items={}
    # Réserver la taille de tous les numéros possibles de la case : les visibles
    # peuvent changer de suffixe après regroupement de leurs voisins masqués.
    dimensions={}
    for case,members in bins.items():
        sizes=[metrics.bounds(case+'.'+str(i),0,0,opt.label_size).bounds
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
        via_id=row['via'].uuid
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
                min_label_distance=row['radius']+max(0,row['via'].mask_expansion)+.32
                if d<=min_label_distance+.15: continue
                start=(x,y)
                routes=[ [start,(end.x,end.y)],
                         [start,(start[0],end.y),(end.x,end.y)],
                         [start,(end.x,start[1]),(end.x,end.y)] ]
                path=next((r for r in routes if safe.covers(LineString(r).buffer(.08))
                           and not route_occupied.intersects(LineString(r).buffer(.08))),None)
                if path is None: continue
                pos=(tx,ty); leader_path=path
                label_items[row['via'].uuid]=dict(kind='text',text=label,x=tx,y=ty,size=opt.label_size)
                additions.append(label_items[row['via'].uuid])
                additions.append(dict(kind='capsule',bounds=shape.bounds))
                for a,b in zip(path,path[1:]):
                    if a==b: continue
                    additions.append(dict(kind='line',a=a,b=b,via_uuid=row['via'].uuid))
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
                            kicad_x_mm=row['x'],kicad_y_mm=row['y'],via_uuid=v.uuid,
                            diametre_mm=v.diameter,percage_mm=v.drill,
                            imprime=pos is not None,voisin=neighbor['label'] if neighbor else '',
                            ecart_x_mm=round(row['xx']-neighbor['xx'],4) if neighbor else '',
                            ecart_y_mm=round(row['yy']-neighbor['yy'],4) if neighbor else '',
                            label_xy=pos,rappel=leader_path))

    def grid_text(text,x,y):
        it=dict(kind='text',text=text,x=x,y=y,size=max(.6,opt.label_size))
        g=metrics.bounds(text,x,y,it['size']).buffer(.15)
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
                if free(g): additions.append(dict(kind='line',a=(x,y),b=(x,y+.6)))
        for i in range(1,math.ceil((ymax-ymin)/20)):
            y=ymax-i*20
            for n in range(math.ceil((xmax-xmin)/2)):
                x=xmin+.5+n*2
                g=LineString([(x,y),(x+.6,y)]).buffer(.14)
                if free(g): additions.append(dict(kind='line',a=(x,y),b=(x+.6,y)))
    numbered=number_unprinted(records)
    for record in numbered:
        if record['imprime']:label_items[record['via_uuid']]['text']=record['repere']
    return dict(drawings=additions,rows=numbered,bounds=list(ext),side=opt.side,
                count_vias=len(snapshot.vias),printed=len(printed),protections=protections)
