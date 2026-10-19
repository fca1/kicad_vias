"""Export Fusion depuis les formes de texte IPC du serveur KiCad."""
import copy
import math
import statistics
from kipy.geometry import Vector2
from kipy.common_types import Text
from kipy.board_types import BoardText,BoardSegment,BoardArc
from .fusion_protocol import read_source,export_wires


def nm(value):return int(float(value)*1000000)


def arc_points(item):
    """Discrétiser les arcs avec une erreur de corde d'au plus 5 micromètres."""
    points=[(v.x/1000000,v.y/1000000) for v in (item.start,item.mid,item.end)]
    (ax,ay),(bx,by),(cx,cy)=points
    d=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    if abs(d)<1e-12: raise ValueError('Arc dégénéré dans le repérage.')
    a=ax*ax+ay*ay;b=bx*bx+by*by;c=cx*cx+cy*cy
    ox=(a*(by-cy)+b*(cy-ay)+c*(ay-by))/d
    oy=(a*(cx-bx)+b*(ax-cx)+c*(bx-ax))/d
    angles=[math.atan2(y-oy,x-ox) for x,y in points]
    sweep=(angles[2]-angles[0])%(2*math.pi)
    if (angles[1]-angles[0])%(2*math.pi)>sweep: sweep-=2*math.pi
    radius=math.hypot(ax-ox,ay-oy)
    step=2*math.acos(max(-1,1-min(.005/radius,1)))
    count=max(2,math.ceil(abs(sweep)/step))
    return [Vector2.from_xy(nm(ox+radius*math.cos(angles[0]+sweep*i/count)),
                       nm(oy+radius*math.sin(angles[0]+sweep*i/count))) for i in range(count+1)]



def prepare(session,side,source,destination):
    session.refresh();face=session.faces.get(side,{})
    record=face.get('preview') or face.get('merged')
    if not record:raise ValueError('Générez d’abord le repérage de cette face.')
    items=session.validate(record,session.native_to_ipc[record['layer']] in session.user_layers)
    elements=read_source(source);footprints={}
    for fp in session.board.get_footprints():
        ref=fp.reference_field.text.value
        if ref in footprints:raise ValueError('Référence KiCad dupliquée : '+ref)
        footprints[ref]=fp
    if any(e.get('name') not in footprints for e in elements):raise ValueError('Composants Fusion absents de KiCad.')
    if len({(float(e.get('x')),float(e.get('y'))) for e in elements})<2:raise ValueError('Deux origines distinctes sont requises.')
    offsets=[(footprints[e.get('name')].position.x/1e6-float(e.get('x')),
              footprints[e.get('name')].position.y/1e6+float(e.get('y'))) for e in elements]
    dx=statistics.median(v[0] for v in offsets);sy=statistics.median(v[1] for v in offsets)
    if any(math.hypot(x-dx,y-sy)>.01 for x,y in offsets):raise ValueError('Implantation différente : alignement refusé.')
    def transform(v):return v.x/1e6-dx,sy-v.y/1e6
    wires=[]
    def add(a,b,width):
        a,b=transform(a),transform(b)
        if a!=b:wires.append((*a,*b,width/1e6))
    for item in items:
        if isinstance(item,BoardText):
            text=Text(item.proto.text);text.attributes.mirrored=side=='Bottom'
            for compound in session.client.get_text_as_shapes(text):
                for shape in compound:
                    if type(shape).__name__!='Segment':raise ValueError('Police à contours non prise en charge pour Fusion.')
                    add(shape.start,shape.end,shape.attributes.stroke.width)
        elif isinstance(item,BoardSegment):add(item.start,item.end,item.attributes.stroke.width)
        elif isinstance(item,BoardArc):
            points=arc_points(item)
            for a,b in zip(points,points[1:]):add(a,b,item.attributes.stroke.width)
        else:raise ValueError('Dessin non exportable vers Fusion.')
    if not wires:raise ValueError('Aucun trait à exporter.')
    return export_wires(elements,wires,side,destination)
