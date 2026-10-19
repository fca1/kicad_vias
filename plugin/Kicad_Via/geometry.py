"""Compatibilité des appels existants ; calcul et accès natifs sont séparés."""
from .native_adapter import mm,vec,uid,bounds,polygons,silhouette,text_item,line,capsule,prepare
from .placement import CollisionIndex,leader_obstacles
