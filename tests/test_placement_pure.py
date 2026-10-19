"""Le moteur doit fonctionner sans API KiCad, GUI ou client IPC."""
from pathlib import Path
import subprocess
import sys
import unittest


class PureEngineTests(unittest.TestCase):
    def test_no_native_or_gui_imports_and_declarative_plan(self):
        code="""
import sys,importlib.abc
class Deny(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in ('pcbnew','wx','kipy'):
            raise AssertionError('Import interdit : '+fullname)
sys.meta_path.insert(0,Deny())
from shapely.geometry import box,Point
from Kicad_Via.board_data import BoardSnapshot,ViaData,TextMetrics
from Kicad_Via.placement import choose,layout
from Kicad_Via.model import Options
snapshot=BoardSnapshot(box(0,0,20,20),(),Point().buffer(0),Point().buffer(0),
                       {'v':Point(10,10).buffer(.6)},
                       (ViaData('v','N',10,10,.8,.3,0,True),))
opt=Options(grid=False)
chosen=choose(snapshot,opt)
metrics=TextMetrics({('A1.1',.65):(-900000,-400000,900000,400000)})
result=layout(snapshot,chosen,metrics,opt)
assert result['printed']==1 and result['rows'][0]['repere']=='A1.1'
assert result['rows'][0]['rappel'][0]==(10,10)
assert {d['kind'] for d in result['drawings']}=={'text','line','capsule'}
assert not any(n in sys.modules for n in ('pcbnew','wx','kipy'))
"""
        import os
        env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'plugin'))
        code='import sys; sys.path.insert(0, '+repr(env['PYTHONPATH'])+')\n'+code
        result=subprocess.run([sys.executable,'-c',code],env=env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
