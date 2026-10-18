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
