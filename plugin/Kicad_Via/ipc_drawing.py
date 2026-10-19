"""Métriques et dessins IPC sans pcbnew : mêmes unités entières que le moteur."""
import math
import uuid
from collections import defaultdict
from .board_data import TextMetrics
from .model import column


def vector(x,y):
    from kipy.geometry import Vector2
    # Même troncature que FromMM, y compris aux coordonnées négatives.
    return Vector2.from_xy(int(float(x)*1000000),int(float(y)*1000000))


def text_message(value,x,y,size,layer,side):
    from kipy.board_types import BoardText
    from kipy.proto.board.board_types_pb2 import BoardLayer
    from kipy.proto.common.types import HorizontalAlignment,VerticalAlignment
    result=BoardText();result.id.value=str(uuid.uuid4());result.layer=layer
    result.value=value;result.position=vector(x,y);result.locked=False
    attributes=result.attributes
    attributes.size=vector(size,size)
    attributes.stroke_width=int(max(.10,size*.16)*1000000)
    attributes.horizontal_alignment=HorizontalAlignment.HA_CENTER
    attributes.vertical_alignment=VerticalAlignment.VA_CENTER
    attributes.visible=True;attributes.multiline=True;attributes.keep_upright=False
    attributes.angle=0
    attributes.line_spacing=1
    attributes.mirrored=side=='Bottom' and layer==BoardLayer.BL_B_SilkS
    return result


def measure_texts(client,snapshot,chosen,opt):
    from kipy.common_types import Text
    from kipy.proto.board.board_types_pb2 import BoardLayer
    counts=defaultdict(int)
    for row in chosen:counts[row['case']]+=1
    requests={(case+'.'+str(i),opt.label_size)
              for case,count in counts.items() for i in range(1,count+1)}
    if opt.grid:
        xmin,ymin,xmax,ymax=snapshot.area.bounds
        requests.update((column(i),max(.6,opt.label_size)) for i in range(math.ceil((xmax-xmin)/20)))
        requests.update((str(i+1),max(.6,opt.label_size)) for i in range(math.ceil((ymax-ymin)/20)))
    boxes={}
    for value,size in sorted(requests):
        item=text_message(value,0,0,size,BoardLayer.BL_User_1,opt.side)
        box=client.get_text_extents(Text(item.proto.text))
        boxes[(value,size)]=(box.pos.x,box.pos.y,box.pos.x+box.size.x,box.pos.y+box.size.y)
    return TextMetrics(boxes)


def materialize(plan,layer,opt):
    from kipy.board_types import BoardSegment,BoardArc
    from kipy.proto.common.types import StrokeLineStyle
    items=[];leaders={}
    def shape(kind,points):
        item=BoardSegment() if kind=='line' else BoardArc()
        item.id.value=str(uuid.uuid4());item.layer=layer;item.locked=False
        item.start=vector(*points[0]);item.end=vector(*points[-1])
        if kind=='arc':item.mid=vector(*points[1])
        item.attributes.stroke.width=120000
        item.attributes.stroke.style=StrokeLineStyle.SLS_SOLID
        item.attributes.fill.filled=False
        items.append(item)
        return item
    for drawing in plan['drawings']:
        if drawing['kind']=='text':
            items.append(text_message(drawing['text'],drawing['x'],drawing['y'],drawing['size'],layer,opt.side))
        elif drawing['kind']=='line':
            item=shape('line',(drawing['a'],drawing['b']))
            if 'via_uuid' in drawing:leaders[item.id.value]=drawing['via_uuid']
        elif drawing['kind']=='capsule':
            x0,y0,x1,y1=drawing['bounds'];radius=(y1-y0)/2;cy=(y0+y1)/2
            left=x0+radius;right=x1-radius
            shape('line',((left,y0),(right,y0)));shape('line',((left,y1),(right,y1)))
            shape('arc',((right,y0),(x1,cy),(right,y1)))
            shape('arc',((left,y1),(x0,cy),(left,y0)))
        else:raise ValueError('Type de dessin inconnu : '+drawing['kind'])
    return dict({k:v for k,v in plan.items() if k!='drawings'},items=items,leader_vias=leaders)
