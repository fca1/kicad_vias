"""Vérifier la copie géométrique sans connexion ni écriture dans Fusion."""
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile
from test_plugin import sample
from Kicad_Via import fusion,service
from Kicad_Via.geometry import vec,uid,text_item,capsule
from Kicad_Via.model import Options
import pcbnew as p


class FusionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.env=patch.dict(service.os.environ,{'KICAD_VIA_STATE_DIR':str(self.root/'ownership')});self.env.start()
        self.board=sample()
        fp=p.FOOTPRINT(self.board);fp.SetReference('U2');fp.SetPosition(vec(80,70));self.board.Add(fp)
        root=ET.Element('eagle');drawing=ET.SubElement(root,'drawing')
        board=ET.SubElement(drawing,'board');elements=ET.SubElement(board,'elements')
        for fp in self.board.GetFootprints():
            pos=fp.GetPosition()
            ET.SubElement(elements,'element',name=fp.GetReference(),x=str(p.ToMM(pos.x)-10),
                          y=str(100-p.ToMM(pos.y)),package='TEST',rot='R0')
        self.source=self.root/'source.brd';ET.ElementTree(root).write(self.source,encoding='utf-8')

    def test_shared_source_reader_valid_and_nonfinite(self):
        from Kicad_Via.fusion_protocol import read_source
        self.assertEqual(len(read_source(self.source)),2)
        data=self.source.read_text(encoding='utf-8')
        root=ET.fromstring(data)
        root.find('./drawing/board/elements/element').set('x','nan')
        self.source.write_text(ET.tostring(root,encoding='unicode'),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Coordonnée'):read_source(self.source)

    def tearDown(self):
        self.env.stop();self.temp.cleanup()

    def test_export_faces_and_merged_preserves_board(self):
        for side,layer,dest in [('Top',p.User_1,'SilkscreenTop'),('Bottom',p.User_2,'SilkscreenBottom')]:
            service.generate(self.board,layer,Options(side=side),self.root/(side+'.md'))
            record=service.state(self.board)['faces'][side]['preview']
            self.assertTrue(all('.' in r['repere'] and '-' not in r['repere'] for r in record['rows']))
            before={uid(i):(i.GetLayer(),i.GetPosition().x,i.GetPosition().y) for i in service.all_objects(self.board)}
            result=fusion.prepare(self.board,side,self.source,self.root)
            text=Path(result['path']).read_text(encoding='utf-8')
            self.assertGreater(result['strokes'],len(record['ids']))
            self.assertIn('L.name=="'+dest+'"',text)
            self.assertEqual(result['layer'],dest)
            self.assertNotIn('L.name=="tPlace"',text);self.assertNotIn('L.name=="bPlace"',text)
            self.assertIn('targetLayer=L.name',text)
            self.assertIn("LAYER '%s';",text)
            self.assertIn('layers==0 && issue==""',text)
            self.assertIn('layers>1 && issue==""',text)
            self.assertNotIn('Carte ou couche cible differente',text)
            self.assertIn('E.footprint.name!=packages[found]',text)
            self.assertLess(text.index('if (issue!="")'),text.index('output(scriptPath'))
            self.assertIn("RUN '",result['command'])
            after={uid(i):(i.GetLayer(),i.GetPosition().x,i.GetPosition().y) for i in service.all_objects(self.board)}
            self.assertEqual(before,after)
            service.merge(self.board,layer,side)
            self.assertEqual(fusion.prepare(self.board,side,self.source,self.root)['strokes'],result['strokes'])

    def test_repair_legacy_layers_preserves_component_and_wire_commands(self):
        for side,name in [('Top','tPlace'),('Bottom','bPlace')]:
            path=self.root/(side+'.ulp')
            preserved=['refs[0]="U1";', 'if (issue!="") { dlgMessageBox(issue); exit(1); }',
                       '  printf("WIRE 0.12 (1 2) (3 4);\\n");']
            old='\n'.join(['// Kicad_Via : copie additive des labels et dessins uniquement.',
                           'int count=0, layers=0; string issue="";',preserved[0],
                           f'  B.layers(L) if (L.name=="{name}") layers++;',
                           'if (count!=2 || layers!=1) issue="Carte ou couche cible differente.";',preserved[1],
                           f'  printf("GRID MM;\\nLAYER {name};\\nSET WIRE_BEND 2;\\nCHANGE STYLE Continuous;\\n");',preserved[2]])+'\n'
            path.write_text(old,encoding='utf-8');original=path.read_bytes()
            backup=fusion.repair_legacy_ulp(path)
            self.assertEqual(backup.read_bytes(),original)
            text=path.read_text(encoding='utf-8')
            for line in preserved:self.assertIn(line,text)
            self.assertIn('count!=2 && issue==""',text)
            self.assertIn('Silkscreen'+side,text)
            self.assertIn("LAYER '%s';",text)
            self.assertEqual(text.count('WIRE 0.12'),1)
            with self.assertRaises(ValueError):fusion.repair_legacy_ulp(path)
            self.assertEqual(path.read_text(encoding='utf-8'),text)

    def test_repair_refuses_foreign_ulp_without_changes(self):
        path=self.root/'other.ulp';path.write_text('exit(0);',encoding='utf-8')
        with self.assertRaises(ValueError):fusion.repair_legacy_ulp(path)
        self.assertEqual(path.read_text(encoding='utf-8'),'exit(0);')
        self.assertEqual(list(self.root.glob('*avant_couches*')),[])

    def test_misalignment_refused_before_files(self):
        service.generate(self.board,p.User_1,Options(),self.root/'Top.md')
        fp=next(fp for fp in self.board.GetFootprints() if fp.GetReference()=='U2')
        fp.SetPosition(vec(81,70))
        with self.assertRaisesRegex(ValueError,'alignement refusé'):
            fusion.prepare(self.board,'Top',self.source,self.root)
        self.assertFalse(list(self.root.glob('Kicad_Via_*')))

    def test_zip_and_foreign_layer_guard(self):
        archive=self.root/'source.fbrd'
        with zipfile.ZipFile(archive,'w') as z:z.write(self.source,'nested/source.brd')
        self.assertEqual(len(fusion.read_source(archive)),2)
        service.generate(self.board,p.User_1,Options(),self.root/'Top.md')
        self.board.Add(text_item(self.board,'étranger',10,10,1,p.User_1,'Top'))
        with self.assertRaises(ValueError):fusion.prepare(self.board,'Top',archive,self.root)

    def test_strokes_reflect_bottom_and_arc_tolerance(self):
        # Le miroir natif doit être conservé, indépendamment du repère de grille.
        top=text_item(self.board,'A3.1',20,20,.65,p.User_1,'Top')
        bottom=text_item(self.board,'A3.1',20,20,.65,p.User_1,'Bottom')
        transform=lambda v:(p.ToMM(v.x),-p.ToMM(v.y))
        a=fusion.strokes([top],transform,'Top');b=fusion.strokes([bottom],transform,'Bottom')
        self.assertFalse(bottom.IsMirrored())
        for first,second in zip(a,b):
            self.assertAlmostEqual(first[0]+second[0],40,places=5)
            self.assertAlmostEqual(first[2]+second[2],40,places=5)
            self.assertAlmostEqual(first[1],second[1],places=5)
        from shapely.geometry import box
        for arc in capsule(self.board,box(10,10,14,12),p.User_1)[2:]:
            pts=fusion.arc_points(arc)
            self.assertLess(math.dist((pts[0].x,pts[0].y),(arc.GetStart().x,arc.GetStart().y)),3)
            self.assertLess(math.dist((pts[-1].x,pts[-1].y),(arc.GetEnd().x,arc.GetEnd().y)),3)
            for q,r in zip(pts,pts[1:]):
                chord=math.hypot(p.ToMM(q.x-r.x),p.ToMM(q.y-r.y))
                self.assertLessEqual(1-math.sqrt(1-(chord/2)**2),.005002)

    def test_dialog_prepare_and_clipboard_on_click(self):
        import wx
        from Kicad_Via.action import FusionDialog
        app=wx.GetApp() or wx.App(False)
        service.generate(self.board,p.User_1,Options(),self.root/'Top.md')
        dialog=FusionDialog(None,self.board,'Top',str(self.root))
        try:
            self.assertFalse(dialog.copy.IsEnabled())
            dialog.source.SetPath(str(self.source));dialog.on_prepare(None)
            self.assertTrue(dialog.copy.IsEnabled())
            self.assertTrue(dialog.command.GetValue().startswith('RUN '))
            with patch('wx.TheClipboard') as clipboard:
                clipboard.Open.return_value=True;clipboard.SetData.return_value=True
                dialog.on_copy(None)
                clipboard.SetData.assert_called_once();clipboard.Flush.assert_called_once();clipboard.Close.assert_called_once()
        finally:dialog.Destroy()


if __name__=='__main__':unittest.main()
