"""Parité du constructeur IPC avec les dessins natifs de référence."""
import sys
from pathlib import Path
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'plugin'),str(Path(__file__).parent)]
import pcbnew as p
from test_plugin import sample
from Kicad_Via.ipc_adapter import load_client
load_client()
from Kicad_Via import native_adapter,ipc_drawing
from Kicad_Via.ipc_native import encode
from Kicad_Via.model import Options
from Kicad_Via.placement import choose,layout
from kipy.proto.board.board_types_pb2 import BoardLayer


class DrawingParityTests(unittest.TestCase):
    def test_generated_messages_match_native_for_both_sides(self):
        board=sample()
        for side in ('Top','Bottom'):
            for size in (.4,.65,1.2):
                with self.subTest(side=side,size=size):
                    options=Options(side=side,label_size=size)
                    snapshot=native_adapter.capture(board,options)
                    chosen=choose(snapshot,options)
                    metrics=native_adapter.measure_texts(board,p.User_1,snapshot,chosen,options)
                    plan=layout(snapshot,chosen,metrics,options)
                    native=native_adapter.materialize(board,p.User_1,options,plan)
                    actual=ipc_drawing.materialize(plan,BoardLayer.BL_User_1,options)
                    self.assertEqual(len(native['items']),len(actual['items']))
                    for old,new in zip(native['items'],actual['items']):
                        expected=encode(old);new.id.value=expected.id.value
                        self.assertEqual(new.proto,expected.proto)

    def test_bottom_mirror_only_on_bottom_silk(self):
        preview=ipc_drawing.text_message('A1.1',-1.23456789,3,.65,BoardLayer.BL_User_1,'Bottom')
        final=ipc_drawing.text_message('A1.1',-1.23456789,3,.65,BoardLayer.BL_B_SilkS,'Bottom')
        self.assertFalse(preview.attributes.mirrored)
        self.assertTrue(final.attributes.mirrored)
        self.assertEqual(preview.position.x,-1234567)
