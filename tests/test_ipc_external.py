"""Contrôles du chemin externe : aucune écriture utilisateur, aucun import SWIG."""
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as N
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugin'))
from Kicad_Via.ipc_adapter import load_client
load_client()
from Kicad_Via import ipc_capture,ipc_drawing
from Kicad_Via.model import Options
from Kicad_Via.ipc_service import Session
from kipy.board_types import BoardSegment
from kipy.geometry import Vector2
from kipy.proto.board.board_types_pb2 import BoardLayer as L,SolderMaskMode as M,SolderMaskOverrides


class ExternalTests(unittest.TestCase):
    def board(self,mode,default='no'):
        shapes=[]
        for a,b in [((0,0),(40,0)),((40,0),(40,40)),((40,40),(0,40)),((0,40),(0,0))]:
            s=BoardSegment();s.layer=L.BL_Edge_Cuts;s.start=ipc_drawing.vector(*a);s.end=ipc_drawing.vector(*b);shapes.append(s)
        outer=N(solder_mask_mode=mode,proto=N(solder_mask_settings=SolderMaskOverrides()))
        v=N(id=N(value='via'),position=Vector2.from_xy(20000000,20000000),diameter=800000,drill_diameter=300000,
            net=N(name='N'),padstack=N(layers=[L.BL_F_Cu,L.BL_B_Cu],front_outer_layers=outer,back_outer_layers=outer))
        return N(get_shapes=lambda:shapes,get_text=lambda:[],get_footprints=lambda:[],get_vias=lambda:[v],
                 get_as_string=lambda:'(kicad_pcb (setup (pad_to_mask_clearance 0) (tenting (front '+default+') (back '+default+'))))')

    def test_inherited_mask_and_explicit_mask(self):
        for mode,default,accessible in [(M.SMM_MASKED,'no',False),(M.SMM_UNMASKED,'yes',True),
                                         (M.SMM_FROM_DESIGN_RULES,'no',True),(M.SMM_FROM_DESIGN_RULES,'yes',False)]:
            with self.subTest(mode=mode,default=default):
                result=ipc_capture.capture(None,self.board(mode,default),Options())
                self.assertEqual(result.vias[0].accessible,accessible)

    def test_hidden_footprint_field_is_not_an_obstacle(self):
        board=self.board(M.SMM_UNMASKED)
        text=ipc_drawing.text_message('HIDDEN',20,20,1,L.BL_F_SilkS,'Top')
        field=N(text=text,proto=N(visible=False))
        fp=N(definition=N(pads=[],shapes=[]),layer=L.BL_B_Cu,texts_and_fields=[field])
        board.get_footprints=lambda:[fp]
        result=ipc_capture.capture(None,board,Options())
        self.assertTrue(result.fixed.is_empty)

    def test_foreign_item_in_user_layer_is_refused(self):
        s=Session.__new__(Session);s.native_to_ipc={39:L.BL_User_1};s.groups={}
        owned=ipc_drawing.text_message('A1.1',1,1,.65,L.BL_User_1,'Top')
        foreign=ipc_drawing.text_message('FOREIGN',2,2,.65,L.BL_User_1,'Top')
        s.objects={i.id.value:i for i in (owned,foreign)}
        record=dict(ids=[owned.id.value],layer=39,group='group')
        with self.assertRaisesRegex(ValueError,'étrangers'):s.validate(record,True)

    def test_external_modules_import_without_pcbnew_or_wx(self):
        root=Path(__file__).resolve().parents[1]
        code="""import sys,importlib.abc
sys.path.insert(0,sys.argv[1])
from Kicad_Via.ipc_adapter import load_client
load_client()
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0] in ('pcbnew','wx'):raise AssertionError(name)
sys.meta_path.insert(0,Block())
from Kicad_Via import ipc_capture,ipc_drawing,ipc_service,ipc_fusion
"""
        subprocess.run([sys.executable,'-c',code,str(root/'plugin')],check=True)

    def test_external_entrypoint_compiles(self):
        path=Path(__file__).resolve().parents[1]/'plugin/Kicad_Via/external.py'
        compile(path.read_text(encoding='utf-8'),str(path),'exec')
