"""Options et convention de repérage géographique, indépendantes de KiCad."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Options:
    side: str = 'Top'
    label_size: float = 0.65
    grid: bool = True
    omit_nearby: bool = True
    proximity: float = 3.0
    step: float = 20.0

    def __post_init__(self):
        if self.side not in ('Top','Bottom'):
            raise ValueError('Face invalide.')
        if not .4 <= self.label_size <= 2:
            raise ValueError('Taille du label : 0,4 à 2 mm.')
        if self.step != 20:
            raise ValueError('La grille de repérage est fixée à 20 mm.')


def column(index):
    """A..Z, AA..AZ, BA.. ; pas de limite artificielle à 26 colonnes."""
    if index<0: raise ValueError('Colonne négative.')
    result=''
    while index>=0:
        result=chr(65+index%26)+result
        index=index//26-1
    return result


def coordinates(x,y,bounds,side):
    xmin,ymin,xmax,ymax=bounds
    # Bottom est la vue physique de dessous : X est inversé, Y reste vers le haut.
    return (x-xmin if side=='Top' else xmax-x),ymax-y


def cell(x,y,bounds,side):
    xx,yy=coordinates(x,y,bounds,side)
    return column(max(0,math.floor(xx/20)))+str(max(0,math.floor(yy/20))+1)


def number_unprinted(rows):
    """Dans chaque case : label visible, puis fantômes par distance au via.

    Tous partagent une seule suite E2.1, E2.2… ; les coordonnées des centres
    sont utilisées avant arrondi. Les groupes visibles gardent leur ordre
    spatial initial, les fantômes suivent le visible le plus proche de la case.
    """
    cases={}
    for row in rows:cases.setdefault(row['case'],[]).append(row)
    def distance(a,b):
        return (a['kicad_x_mm']-b['kicad_x_mm'])**2+(a['kicad_y_mm']-b['kicad_y_mm'])**2
    result=[]; external_references=[]
    all_printed=[r for r in rows if r['imprime']]
    for case,members in cases.items():
        printed=[r for r in members if r['imprime']]
        if not printed:
            # Cas limite au bord d'une case : tous ses accès sont masqués et
            # leur voisin visible est dans une autre case. Garder le préfixe
            # géographique réel et classer par référence puis distance.
            if not all_printed:raise ValueError('Un accès masqué doit avoir un label imprimé de référence.')
            anchors={r['via_uuid']:min(all_printed,key=lambda a:(distance(r,a),a['repere'])) for r in members}
            ordered=sorted(members,key=lambda r:(anchors[r['via_uuid']]['repere'],distance(r,anchors[r['via_uuid']]),r['via_uuid']))
            for index,row in enumerate(ordered,1):
                anchor=anchors[row['via_uuid']]
                numbered=dict(row,repere=case+'.'+str(index),
                              ecart_x_mm=round(row['kicad_x_mm']-anchor['kicad_x_mm'],4),
                              ecart_y_mm=round(row['kicad_y_mm']-anchor['kicad_y_mm'],4))
                result.append(numbered);external_references.append((numbered,anchor['via_uuid']))
            continue
        groups={r['via_uuid']:[] for r in printed}
        for row in members:
            if row['imprime']:continue
            if not printed:raise ValueError('Un accès masqué doit avoir un label imprimé dans sa case.')
            anchor=min(printed,key=lambda r:(distance(row,r),r['repere']))
            groups[anchor['via_uuid']].append(row)
        index=1
        for anchor in printed:
            name=case+'.'+str(index);index+=1
            result.append(dict(anchor,repere=name))
            ghosts=sorted(groups[anchor['via_uuid']],key=lambda r:(distance(r,anchor),r['kicad_x_mm'],r['kicad_y_mm'],r['via_uuid']))
            for row in ghosts:
                result.append(dict(row,repere=case+'.'+str(index),voisin=name,
                                   ecart_x_mm=round(row['kicad_x_mm']-anchor['kicad_x_mm'],4),
                                   ecart_y_mm=round(row['kicad_y_mm']-anchor['kicad_y_mm'],4)))
                index+=1
    printed_names={r['via_uuid']:r['repere'] for r in result if r['imprime']}
    for row,anchor_id in external_references:row['voisin']=printed_names[anchor_id]
    return result
