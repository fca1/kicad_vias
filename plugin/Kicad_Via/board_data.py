"""Contrat indépendant du transport : unités mm, identifiants opaques, Shapely."""
from dataclasses import dataclass
from shapely.geometry import box


@dataclass(frozen=True)
class ViaData:
    uuid: str
    net: str
    x: float
    y: float
    diameter: float
    drill: float
    mask_expansion: float
    accessible: bool


@dataclass(frozen=True)
class BoardSnapshot:
    area: object
    bodies: tuple
    fixed: object
    solid: object
    via_apertures: dict
    vias: tuple


@dataclass(frozen=True)
class TextMetrics:
    # Boîtes au centre (0,0), en unités entières natives. Aucun objet SWIG.
    boxes: dict
    units_per_mm: int = 1000000

    def bounds(self,text,x,y,size):
        # La troncature doit suivre FromMM pour préserver les positions aux
        # limites de collision. Une translation flottante changerait ce contrat.
        scale=self.units_per_mm
        px=int(float(x)*scale);py=int(float(y)*scale)
        a,b,c,d=self.boxes[(text,size)]
        return box((a+px)/scale,(b+py)/scale,(c+px)/scale,(d+py)/scale)
