"""Conversions de dessins natifs aux messages IPC, sans écriture sur la carte."""
from .ipc_adapter import load_client


def encode(item):
    load_client()
    import pcbnew as p
    from kipy.board_types import BoardSegment,BoardArc,BoardText
    from kipy.geometry import Vector2
    from kipy.proto.board.board_types_pb2 import BoardLayer
    from kipy.proto.common.types import HorizontalAlignment,VerticalAlignment,StrokeLineStyle
    def vector(v):return Vector2.from_xy(v.x,v.y)
    # Les numéros natifs et protobuf ne sont pas interchangeables.
    name=p.BOARD.GetStandardLayerName(item.GetLayer())
    mapping={'F.Silkscreen':'BL_F_SilkS','B.Silkscreen':'BL_B_SilkS'}
    layer=BoardLayer.Value(mapping.get(name,'BL_'+name.replace('.','_')))
    if isinstance(item,p.PCB_TEXT):
        result=BoardText();result.value=item.GetText();result.position=vector(item.GetPosition())
        result.attributes.size=vector(item.GetTextSize())
        result.attributes.stroke_width=item.GetTextThickness()
        result.attributes.angle=item.GetTextAngle().AsDegrees()
        result.attributes.mirrored=item.IsMirrored()
        result.attributes.visible=item.IsVisible()
        result.attributes.font_name=item.GetFontName()
        result.attributes.line_spacing=item.GetLineSpacing()
        result.attributes.bold=item.IsBold();result.attributes.italic=item.IsItalic()
        result.attributes.multiline=item.IsMultilineAllowed()
        result.attributes.keep_upright=item.IsKeepUpright()
        result.attributes.horizontal_alignment={-1:HorizontalAlignment.HA_LEFT,0:HorizontalAlignment.HA_CENTER,1:HorizontalAlignment.HA_RIGHT}[int(item.GetHorizJustify())]
        result.attributes.vertical_alignment={-1:VerticalAlignment.VA_TOP,0:VerticalAlignment.VA_CENTER,1:VerticalAlignment.VA_BOTTOM}[int(item.GetVertJustify())]
    elif item.GetShape()==p.SHAPE_T_SEGMENT:
        result=BoardSegment();result.start=vector(item.GetStart());result.end=vector(item.GetEnd())
    elif item.GetShape()==p.SHAPE_T_ARC:
        result=BoardArc();result.start=vector(item.GetStart());result.mid=vector(item.GetArcMid());result.end=vector(item.GetEnd())
    else:raise ValueError('Dessin non pris en charge par IPC.')
    if not isinstance(item,p.PCB_TEXT):
        result.attributes.stroke.width=item.GetWidth()
        result.attributes.stroke.style=StrokeLineStyle.SLS_SOLID
        result.attributes.fill.filled=False
    result.id.value=item.m_Uuid.AsString();result.layer=layer;result.locked=item.IsLocked()
    return result
