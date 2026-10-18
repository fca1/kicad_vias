"""Vérification native sur copies et cas synthétiques, jamais sur l'original ouvert."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugin'))
import pcbnew as p
from Kicad_Via.model import Options,column,cell,coordinates
from Kicad_Via.geometry import vec,uid,line,prepare
from Kicad_Via import service


def sample():
    b=p.BOARD()
    for a,c in [((0,0),(120,0)),((120,0),(120,80)),((120,80),(0,80)),((0,80),(0,0))]:
        b.Add(line(b,a,c,p.Edge_Cuts,.05))
    for name,points in [('N1',[(21,21),(45,30)]),('N2',[(22,21)]),('N3',[(65,55)]),
                        ('MASKED',[(85,25)]),('BLOCKED',[(100,40)])]:
        net=p.NETINFO_ITEM(b,name); b.Add(net)
        for x,y in points:
            v=p.PCB_VIA(b); v.SetPosition(vec(x,y)); v.SetWidth(p.FromMM(.8));v.SetDrill(p.FromMM(.3))
            v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(net)
            mode=p.TENTING_MODE_TENTED if name=='MASKED' else p.TENTING_MODE_NOT_TENTED
            v.SetFrontTentingMode(mode);v.SetBackTentingMode(mode);b.Add(v)
    fp=p.FOOTPRINT(b);fp.SetReference('U1');fp.SetPosition(vec(100,40))
    body=p.PCB_SHAPE(fp);body.SetShape(p.SHAPE_T_RECT);body.SetLayer(p.F_Fab)
    body.SetStart(vec(97,37));body.SetEnd(vec(103,43));fp.Add(body)
    pad=p.PAD(fp);pad.SetPosition(vec(97,40));pad.SetSize(vec(1,1));pad.SetAttribute(p.PAD_ATTRIB_SMD)
    mask=p.LSET();mask.AddLayer(p.F_Cu);pad.SetLayerSet(mask);fp.Add(pad);b.Add(fp)
    return b


class PluginTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.b=sample()
        self.env=patch.dict(service.os.environ,{'KICAD_VIA_STATE_DIR':str(self.root/'ownership')});self.env.start()

    def tearDown(self): self.env.stop();self.temp.cleanup()

    def generate(self,side='Top',layer=p.User_1):
        return service.generate(self.b,layer,Options(side=side),self.root/(side+'.nd'))

    def test_coordinates(self):
        self.assertEqual([column(i) for i in (0,25,26,27,51,52)],['A','Z','AA','AB','AZ','BA'])
        self.assertEqual(cell(21,55,(0,0,120,80),'Top'),'B2')
        self.assertEqual(cell(21,55,(0,0,120,80),'Bottom'),'E2')
        self.assertEqual(coordinates(21,55,(0,0,120,80),'Bottom'),(99,25))

    def test_generation_and_regeneration(self):
        before={uid(v):(v.GetPosition().x,v.GetPosition().y,v.GetNetname(),v.GetWidth(p.F_Cu),v.GetDrillValue()) for v in self.b.GetTracks()}
        result=self.generate()
        self.assertEqual(result['points'],3)
        self.assertEqual(self.b.GetLayerName(p.User_1),'Kicad_Via_TOP')
        a=set(service.state(self.b)['faces']['Top']['preview']['ids'])
        self.generate()
        c=set(service.state(self.b)['faces']['Top']['preview']['ids'])
        self.assertFalse(a&c)
        self.assertEqual(c,{uid(i) for i in service.layer_objects(self.b,p.User_1)})
        after={uid(v):(v.GetPosition().x,v.GetPosition().y,v.GetNetname(),v.GetWidth(p.F_Cu),v.GetDrillValue()) for v in self.b.GetTracks()}
        self.assertEqual(before,after)

    def test_foreign_layer_refused(self):
        foreign=line(self.b,(10,10),(20,10),p.User_1);self.b.Add(foreign)
        self.assertNotIn(p.User_1,service.available_layers(self.b,'Top'))
        with self.assertRaises(ValueError): self.generate()
        self.assertIn(foreign,list(self.b.GetDrawings()))

    def test_foreign_added_to_owned_layer_refused(self):
        self.generate();foreign=line(self.b,(10,10),(20,10),p.User_1);self.b.Add(foreign)
        with self.assertRaises(ValueError): self.generate()
        with self.assertRaises(ValueError): service.merge(self.b,p.User_1,'Top')

    def test_two_sides_and_exports(self):
        self.generate('Top',p.User_1); self.generate('Bottom',p.User_2)
        data=service.state(self.b)['faces']
        for side in ('Top','Bottom'):
            self.assertTrue(all(r['repere'].endswith('.1') for r in data[side]['preview']['rows']))
            text=(self.root/(side+'.nd')).read_text(encoding='utf-8')
            self.assertTrue(text.startswith('# '+side+'\n\n| Repère | Net | X (mm) | Y (mm) |\n'))
            self.assertNotIn('Case',text)
            self.assertRegex(text,r'\| -?\d+\.\d \| -?\d+\.\d \|')
        bottom=[it for it in service.layer_objects(self.b,p.User_2) if isinstance(it,p.PCB_TEXT)]
        self.assertTrue(all(it.IsMirrored() for it in bottom))
        top_ids=set(data['Top']['preview']['ids']);self.generate('Bottom',p.User_2)
        self.assertEqual(top_ids,set(service.state(self.b)['faces']['Top']['preview']['ids']))
        service.merge(self.b,p.User_2,'Bottom')
        self.assertEqual(top_ids,set(service.state(self.b)['faces']['Top']['preview']['ids']))
        self.assertTrue(all(i.GetLayer()==p.B_SilkS for i in self.b.GetDrawings()
                            if uid(i) in service.state(self.b)['faces']['Bottom']['merged']['ids']))

    def test_same_file_other_side_refused(self):
        self.generate()
        with self.assertRaises(ValueError): service.generate(self.b,p.User_2,Options(side='Bottom'),self.root/'Top.nd')
        self.assertFalse(service.layer_objects(self.b,p.User_2))

    def test_arbitrary_output_refused_before_mutation(self):
        output=self.root/'notes.nd';output.write_text('Mes notes',encoding='utf-8')
        with self.assertRaises(ValueError): service.generate(self.b,p.User_1,Options(),output)
        self.assertFalse(service.layer_objects(self.b,p.User_1))
        self.assertEqual(output.read_text(encoding='utf-8'),'Mes notes')

    def test_merge_and_replace_previous_merge(self):
        original=line(self.b,(5,5),(10,5),p.F_SilkS);self.b.Add(original)
        self.generate();record=service.state(self.b)['faces']['Top']['preview'];ids=set(record['ids'])
        service.merge(self.b,p.User_1,'Top')
        self.assertFalse(service.layer_objects(self.b,p.User_1))
        self.assertEqual(ids,{uid(i) for i in self.b.GetDrawings() if uid(i) in ids and i.GetLayer()==p.F_SilkS})
        self.assertIn(original,list(self.b.GetDrawings()))
        self.generate();service.merge(self.b,p.User_1,'Top')
        self.assertFalse(ids & {uid(i) for i in self.b.GetDrawings()})
        self.assertIn(original,list(self.b.GetDrawings()))

    def test_merge_moved_label_collision_refused(self):
        self.generate();texts=[i for i in service.layer_objects(self.b,p.User_1) if isinstance(i,p.PCB_TEXT)]
        texts[0].SetPosition(vec(100,40))
        with self.assertRaises(ValueError): service.merge(self.b,p.User_1,'Top')
        self.assertTrue(service.layer_objects(self.b,p.User_1))

    def test_roundtrip_state(self):
        self.generate();path=self.root/'board.kicad_pcb';p.SaveBoard(str(path),self.b)
        b=p.LoadBoard(str(path));data=service.state(b)['faces']['Top']['preview']
        items,group=service.validate_record(b,data,True)
        self.assertEqual(len(items),len(data['ids']));self.assertIsNotNone(group)

    def test_grid_and_oval(self):
        plan=prepare(self.b,p.User_1,Options())
        self.assertTrue(any(isinstance(i,p.PCB_SHAPE) and i.GetShape()==p.SHAPE_T_ARC for i in plan['items']))
        self.assertTrue(all(r['rappel'] for r in plan['rows'] if r['imprime']))
        self.assertFalse(service.layer_objects(self.b,p.User_1))

    def test_proximity_and_independent_cell_suffixes(self):
        net=p.NETINFO_ITEM(self.b,'NEAR_N3');self.b.Add(net)
        v=p.PCB_VIA(self.b);v.SetPosition(vec(65,56));v.SetWidth(p.FromMM(.8));v.SetDrill(p.FromMM(.3))
        v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(net);v.SetFrontTentingMode(p.TENTING_MODE_NOT_TENTED);self.b.Add(v)
        plan=prepare(self.b,p.User_1,Options())
        self.assertLess(plan['printed'],len(plan['rows']))
        labels={r['repere'] for r in plan['rows'] if r['imprime']}
        self.assertTrue(all(r['voisin'] in labels for r in plan['rows'] if not r['imprime']))
        ids={r['repere'] for r in plan['rows'] if r['net'] in ('N3','NEAR_N3')}
        self.assertEqual(len(ids),2)
        dense=prepare(self.b,p.User_1,Options(omit_nearby=False))
        self.assertEqual(dense['printed'],len(dense['rows']))

    def test_change_preview_layer(self):
        self.generate();self.generate(layer=p.User_2)
        self.assertFalse(service.layer_objects(self.b,p.User_1))
        self.assertEqual(self.b.GetLayerName(p.User_2),'Kicad_Via_TOP')

    def test_export_failure_rolls_back(self):
        name=str(self.b.GetLayerName(p.User_2));enabled=list(self.b.GetEnabledLayers().Seq())
        with patch.object(service.os,'replace',side_effect=OSError('Échec simulé')):
            with self.assertRaises(OSError): self.generate(layer=p.User_2)
        self.assertFalse(service.layer_objects(self.b,p.User_2))
        self.assertEqual(str(self.b.GetLayerName(p.User_2)),name)
        self.assertEqual(list(self.b.GetEnabledLayers().Seq()),enabled)
        self.assertEqual(service.state(self.b),{'schema':1,'faces':{}})

    def test_merge_undo_layer_state(self):
        self.generate();service.merge(self.b,p.User_1,'Top')
        data=service.state(self.b)['faces']['Top']['merged']
        ids=set(data['ids'])
        for it in self.b.GetDrawings():
            if uid(it) in ids: it.SetLayer(p.User_1)
        state=service.state(self.b)['faces']['Top']
        self.assertIn('preview',state);self.assertNotIn('merged',state)
        service.validate_record(self.b,state['preview'],True)

    def test_dialog_top_bottom_options(self):
        import wx
        from Kicad_Via.action import ViaDialog
        app=wx.GetApp() or wx.App(False)
        dialog=ViaDialog(None,self.b)
        try:
            self.assertEqual(dialog.size.GetValue(),.65)
            self.assertTrue(dialog.output.GetPath().endswith('_top.nd'))
            self.assertIn('F.SilkS',dialog.merge.GetLabel())
            dialog.side.SetSelection(1);dialog.update_side()
            self.assertTrue(dialog.output.GetPath().endswith('_bottom.nd'))
            self.assertIn('B.SilkS',dialog.merge.GetLabel())
            self.assertTrue(dialog.grid.GetValue());self.assertTrue(dialog.near.GetValue())
            self.assertFalse(dialog.merge.IsEnabled())
            self.assertLessEqual(dialog.GetSize().height,500)
        finally: dialog.Destroy()

    def test_change_layer_after_merge(self):
        self.generate();service.merge(self.b,p.User_1,'Top')
        merged=set(service.state(self.b)['faces']['Top']['merged']['ids'])
        self.generate(layer=p.User_2)
        self.assertEqual(self.b.GetLayerName(p.User_2),'Kicad_Via_TOP')
        self.assertTrue(merged.issubset({uid(i) for i in self.b.GetDrawings()}))

    def test_adopted_preview_and_empty_merged_source(self):
        self.generate(layer=p.User_2);service.merge(self.b,p.User_2,'Top')
        merged=service.state(self.b)['faces']['Top']['merged']
        item=line(self.b,(5,5),(6,5),p.User_1);self.b.Add(item)
        group=p.PCB_GROUP(self.b);group.AddItem(item);self.b.Add(group)
        legacy=dict(layer=p.User_1,ids=[uid(item)],group=uid(group),previous_name='User.1')
        service.persist('Top','preview',legacy)
        self.generate(layer=p.User_1)
        self.assertEqual(self.b.GetLayerName(p.User_1),'Kicad_Via_TOP')
        self.assertEqual(self.b.GetLayerName(p.User_2),'User.2')
        self.assertTrue(set(merged['ids']).issubset({uid(i) for i in self.b.GetDrawings()}))


if __name__=='__main__': unittest.main(verbosity=2)
