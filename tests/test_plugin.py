"""Vérification native sur copies et cas synthétiques, jamais sur l'original ouvert."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugin'))
import pcbnew as p
from Kicad_Via.model import Options,column,cell,coordinates,number_unprinted
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
        return service.generate(self.b,layer,Options(side=side),self.root/(side+'.md'))

    def test_old_output_path_migrates_without_touching_old_file(self):
        old=self.root/'Top.nd';old.write_text('Ancien fichier conservé',encoding='utf-8')
        result=service.generate(self.b,p.User_1,Options(),old)
        self.assertEqual(Path(result['output']),self.root/'Top.md')
        self.assertEqual(old.read_text(encoding='utf-8'),'Ancien fichier conservé')
        # Le contrôle de destination s'applique aussi après normalisation.
        (self.root/'Top.md').write_text('Document étranger',encoding='utf-8')
        with self.assertRaises(ValueError):service.generate(self.b,p.User_1,Options(),old)

    def test_text_metrics_match_native_translations(self):
        from Kicad_Via import native_adapter as adapter
        for side in ('Top','Bottom'):
            opt=Options(side=side)
            snapshot=adapter.capture(self.b,opt)
            chosen=adapter.choose(snapshot,opt)
            metrics=adapter.measure_texts(self.b,p.User_1,snapshot,chosen,opt)
            for text,size in metrics.boxes:
                for x,y in ((0,0),(12.123456789,7.9999999),(-12.123456789,-7.9999999)):
                    it=adapter.text_item(self.b,text,x,y,size,p.User_1,side)
                    self.assertEqual(metrics.bounds(text,x,y,size).bounds,adapter.bounds(it).bounds)

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
            text=(self.root/(side+'.md')).read_text(encoding='utf-8')
            self.assertTrue(text.startswith('# '+side+'\n\n| Repère | Net | Label imprimé | X (mm) | Y (mm) |\n'))
            self.assertIn('| true |',text)
            self.assertNotIn('Case',text)
            self.assertRegex(text,r'\| -?\d+\.\d \| -?\d+\.\d \|')
        bottom=[it for it in service.layer_objects(self.b,p.User_2) if isinstance(it,p.PCB_TEXT)]
        self.assertTrue(all(not it.IsMirrored() and not it.IsSideSpecific() for it in bottom))
        top_ids=set(data['Top']['preview']['ids']);self.generate('Bottom',p.User_2)
        self.assertEqual(top_ids,set(service.state(self.b)['faces']['Top']['preview']['ids']))
        service.merge(self.b,p.User_2,'Bottom')
        bottom=[it for it in service.layer_objects(self.b,p.B_SilkS) if isinstance(it,p.PCB_TEXT)]
        self.assertTrue(bottom)
        self.assertTrue(all(it.IsMirrored() and it.IsSideSpecific() for it in bottom))
        self.assertEqual(top_ids,set(service.state(self.b)['faces']['Top']['preview']['ids']))
        self.assertTrue(all(i.GetLayer()==p.B_SilkS for i in self.b.GetDrawings()
                            if uid(i) in service.state(self.b)['faces']['Bottom']['merged']['ids']))

    def test_same_file_other_side_refused(self):
        self.generate()
        with self.assertRaises(ValueError): service.generate(self.b,p.User_2,Options(side='Bottom'),self.root/'Top.md')
        self.assertFalse(service.layer_objects(self.b,p.User_2))

    def test_arbitrary_output_refused_before_mutation(self):
        output=self.root/'notes.md';output.write_text('Mes notes',encoding='utf-8')
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

    def test_center_leaders_survive_save_and_merge(self):
        for side,layer in [('Top',p.User_1),('Bottom',p.User_2)]:
            self.generate(side,layer)
            record=service.state(self.b)['faces'][side]['preview']
            self.assertTrue(record['leader_vias'])
            for row in record['rows']:
                if row['imprime']:
                    self.assertEqual(tuple(row['rappel'][0]),(row['kicad_x_mm'],row['kicad_y_mm']))
        path=self.root/'center.kicad_pcb';p.SaveBoard(str(path),self.b)
        board=p.LoadBoard(str(path))
        service.merge(board,p.User_1,'Top');service.merge(board,p.User_2,'Bottom')

    def test_center_exception_keeps_other_apertures_protected(self):
        for obstacle in ('other_via','overlapping_mask'):
            with self.subTest(obstacle=obstacle):
                self.b=sample();self.generate()
                record=service.state(self.b)['faces']['Top']['preview']
                leader_id,via_id=next(iter(record['leader_vias'].items()))
                objects={uid(it):it for it in service.all_objects(self.b)}
                leader=objects[leader_id];via=objects[via_id]
                if obstacle=='other_via':
                    other=next(v for v in self.b.GetTracks() if isinstance(v,p.PCB_VIA)
                               and uid(v)!=via_id and not v.IsTented(p.F_Mask))
                    leader.SetEnd(other.GetPosition())
                else:
                    # Un obstacle superposé au via ne doit pas disparaître
                    # avec l'exception accordée à sa seule ouverture propre.
                    pos=via.GetPosition()
                    mask=p.PCB_SHAPE(self.b);mask.SetShape(p.SHAPE_T_RECT);mask.SetLayer(p.F_Mask)
                    mask.SetStart(p.VECTOR2I(pos.x-p.FromMM(.1),pos.y-p.FromMM(.1)))
                    mask.SetEnd(p.VECTOR2I(pos.x+p.FromMM(.1),pos.y+p.FromMM(.1)));self.b.Add(mask)
                with self.assertRaisesRegex(ValueError,'chevauche'):
                    service.merge(self.b,p.User_1,'Top')

    def test_center_margin_relaxed_without_removing_silkscreen(self):
        from shapely.geometry import Point,LineString,box
        from Kicad_Via.geometry import leader_obstacles
        actual=box(-1,.25,1,.4);fixed=actual.buffer(.2)
        apertures={'own':Point(0,0).buffer(.6)}
        departure=LineString([(0,0),(0,-2)]).buffer(.08)
        self.assertTrue(fixed.intersects(departure))
        allowed=leader_obstacles(fixed,apertures,'own',actual)
        self.assertFalse(allowed.intersects(departure))
        self.assertTrue(allowed.intersects(LineString([(0,0),(0,2)]).buffer(.08)))

    def test_ghost_names_follow_anchor_and_distance(self):
        def row(name,x,y,printed):
            return dict(repere=name,case=name.split('.')[0],kicad_x_mm=x,kicad_y_mm=y,imprime=printed,via_uuid=name,net=name)
        # Le fantôme plus loin vient initialement avant le proche dans la case.
        rows=[row('A3.1',10,10,True),row('A3.2',10,12,False),
              row('A3.3',11,10,False),row('A3.4',18,10,True),row('A3.5',18.2,10,False),
              row('B3.1',18.3,10,True),row('C3.1',18.4,10,False)]
        result=number_unprinted(rows)
        self.assertEqual([r['repere'] for r in result],['A3.1','A3.2','A3.3','A3.4','A3.5','B3.1','C3.1'])
        self.assertEqual(result[1]['via_uuid'],'A3.3')
        self.assertEqual(result[2]['via_uuid'],'A3.2')
        self.assertEqual(result[4]['voisin'],'A3.4')
        self.assertEqual(result[-1]['voisin'],'B3.1')
        self.assertEqual([r['imprime'] for r in result],[True,False,False,True,False,True,False])

    def test_proximity_and_independent_cell_suffixes(self):
        net=p.NETINFO_ITEM(self.b,'NEAR_N3');self.b.Add(net)
        v=p.PCB_VIA(self.b);v.SetPosition(vec(65,56));v.SetWidth(p.FromMM(.8));v.SetDrill(p.FromMM(.3))
        v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(net);v.SetFrontTentingMode(p.TENTING_MODE_NOT_TENTED);self.b.Add(v)
        plan=prepare(self.b,p.User_1,Options())
        self.assertEqual(plan['printed'],len(plan['rows']))
        labels={r['repere'] for r in plan['rows'] if r['imprime']}
        self.assertTrue(all(r['voisin'] in labels for r in plan['rows'] if not r['imprime']))
        ids={r['repere'] for r in plan['rows'] if r['net'] in ('N3','NEAR_N3')}
        self.assertEqual(len(ids),2)
        self.assertTrue(all(r['rappel'] and r['label_xy'] for r in plan['rows']))
        dense=prepare(self.b,p.User_1,Options(omit_nearby=False))
        self.assertEqual(dense['printed'],len(dense['rows']))

    def test_proximity_fallback_only_after_no_free_leader(self):
        net=p.NETINFO_ITEM(self.b,'NEAR_N3');self.b.Add(net)
        v=p.PCB_VIA(self.b);v.SetPosition(vec(65,56));v.SetWidth(p.FromMM(.8));v.SetDrill(p.FromMM(.3))
        v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(net);v.SetFrontTentingMode(p.TENTING_MODE_NOT_TENTED);self.b.Add(v)
        # Ouverture de masque autour de N3 : chaque départ de rappel croise
        # cet obstacle, tandis que le via voisin conserve des directions libres.
        mask=p.PCB_SHAPE(self.b);mask.SetShape(p.SHAPE_T_RECT);mask.SetLayer(p.F_Mask)
        mask.SetStart(vec(64.5,54.5));mask.SetEnd(vec(65.5,55.5));mask.SetWidth(p.FromMM(.1));self.b.Add(mask)
        plan=prepare(self.b,p.User_1,Options())
        rows={r['net']:r for r in plan['rows']}
        self.assertTrue(rows['NEAR_N3']['imprime'])
        self.assertFalse(rows['N3']['imprime'])
        self.assertIsNone(rows['N3']['label_xy'])
        self.assertEqual(rows['N3']['rappel'],[])
        self.assertEqual(rows['N3']['voisin'],rows['NEAR_N3']['repere'])
        output,staged=service.stage_output(self.root/'fallback.md','Top',plan['rows'],plan['bounds'])
        text=staged.read_text(encoding='utf-8');staged.unlink()
        self.assertIn('| true |',text);self.assertIn('| false |',text)
        # Le manque de place ne bloque plus, même sans option ni voisin proche.
        for opt in (Options(omit_nearby=False),Options(proximity=.5)):
            plan=prepare(self.b,p.User_1,opt)
            self.assertFalse(next(r for r in plan['rows'] if r['net']=='N3')['imprime'])
            self.assertGreater(plan['printed'],0)
        result=self.generate()
        self.assertEqual(result['points'],4)
        self.assertEqual(result['labels'],3)

    def test_all_ghosts_still_produce_table(self):
        # Bloquer chaque départ, sans rendre les vias inaccessibles par un corps.
        for via in self.b.GetTracks():
            pos=via.GetPosition();x=p.ToMM(pos.x);y=p.ToMM(pos.y)
            mask=p.PCB_SHAPE(self.b);mask.SetShape(p.SHAPE_T_RECT);mask.SetLayer(p.F_Mask)
            mask.SetStart(vec(x-.5,y-.5));mask.SetEnd(vec(x+.5,y+.5));mask.SetWidth(p.FromMM(.1));self.b.Add(mask)
        result=service.generate(self.b,p.User_1,Options(grid=False),self.root/'Top.md')
        self.assertEqual(result['points'],3);self.assertEqual(result['labels'],0)
        rows=service.state(self.b)['faces']['Top']['preview']['rows']
        self.assertTrue(all(not r['imprime'] and not r['voisin'] for r in rows))
        self.assertEqual((self.root/'Top.md').read_text(encoding='utf-8').count('| false |'),3)
        service.generate(self.b,p.User_1,Options(grid=False),self.root/'Top.md')


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
            self.assertTrue(dialog.output.GetPath().endswith('_top.md'))
            self.assertIn('F.SilkS',dialog.merge.GetLabel())
            dialog.side.SetSelection(1);dialog.update_side()
            self.assertTrue(dialog.output.GetPath().endswith('_bottom.md'))
            self.assertIn('B.SilkS',dialog.merge.GetLabel())
            self.assertTrue(dialog.grid.GetValue())
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
