"""Petite boîte d'options native et bouton dans le bandeau de l'éditeur PCB."""
from pathlib import Path
import json
import traceback
import pcbnew as p
import wx
from .model import Options
from . import service


def version():
    path=Path(__file__).with_name('_build.json')
    return json.loads(path.read_text(encoding='utf-8'))['commit'][:7] if path.exists() else 'développement'


class ViaDialog(wx.Dialog):
    def __init__(self,parent,board):
        super().__init__(parent,title='Kicad_Via — '+version())
        self.board=board; self.mode=None; self.layers=[]; self.outputs={}
        outer=wx.BoxSizer(wx.VERTICAL)
        self.side=wx.RadioBox(self,label='Face',choices=['Top','Bottom'],majorDimension=2,style=wx.RA_SPECIFY_COLS)
        outer.Add(self.side,0,wx.EXPAND|wx.ALL,10)
        grid=wx.FlexGridSizer(cols=2,hgap=10,vgap=10); grid.AddGrowableCol(1)
        grid.Add(wx.StaticText(self,label='Hauteur des labels (mm)'),0,wx.ALIGN_CENTER_VERTICAL)
        self.size=wx.SpinCtrlDouble(self,min=.4,max=2,initial=.65,inc=.05); self.size.SetDigits(2)
        grid.Add(self.size,1,wx.EXPAND)
        grid.Add(wx.StaticText(self,label='Couche utilisateur'),0,wx.ALIGN_CENTER_VERTICAL)
        self.layer=wx.Choice(self); grid.Add(self.layer,1,wx.EXPAND)
        grid.Add(wx.StaticText(self,label='Tableau de sortie'),0,wx.ALIGN_CENTER_VERTICAL)
        self.output=wx.FilePickerCtrl(self,message='Choisir le tableau de correspondance',
                                     wildcard='Tableau (*.nd)|*.nd|Markdown (*.md)|*.md',
                                     style=wx.FLP_SAVE|wx.FLP_USE_TEXTCTRL)
        grid.Add(self.output,1,wx.EXPAND)
        outer.Add(grid,0,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,12)
        self.grid=wx.CheckBox(self,label='Ajouter la grille en pointillés — pas de 20 mm'); self.grid.SetValue(True)
        self.near=wx.CheckBox(self,label='Alléger les labels proches — moins de 3 mm'); self.near.SetValue(True)
        outer.Add(self.grid,0,wx.LEFT|wx.RIGHT|wx.BOTTOM,12)
        outer.Add(self.near,0,wx.LEFT|wx.RIGHT|wx.BOTTOM,12)
        info=wx.StaticText(self,label='C2-1 : colonne C, ligne 2, accès 1. Top et Bottom ont deux listes séparées.\n'
                           'Labels entourés d’un ovale, avec trait vers le via. Bottom est vu de dessous.\n'
                           'Seules les couches libres ou déjà gérées par Kicad_Via sont proposées.')
        info.Wrap(590); outer.Add(info,0,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,12)
        self.status=wx.StaticText(self,label=''); outer.Add(self.status,0,wx.EXPAND|wx.ALL,12)
        buttons=wx.BoxSizer(wx.HORIZONTAL)
        self.generate=wx.Button(self,label='Générer / remplacer'); self.generate.SetDefault()
        self.merge=wx.Button(self,label='Fusionner vers F.SilkS')
        close=wx.Button(self,wx.ID_CANCEL,label='Fermer')
        for button in (self.generate,self.merge,close): buttons.Add(button,0,wx.ALL,5)
        outer.Add(buttons,0,wx.ALIGN_RIGHT|wx.ALL,6)
        self.SetSizer(outer); self.SetMinSize((660,-1)); self.Fit(); self.CentreOnParent()
        self.side.Bind(wx.EVT_RADIOBOX,self.change_side)
        self.layer.Bind(wx.EVT_CHOICE,self.refresh_actions)
        self.generate.Bind(wx.EVT_BUTTON,lambda e:self.finish('generate'))
        self.merge.Bind(wx.EVT_BUTTON,lambda e:self.finish('merge'))
        self.update_side()

    @property
    def selected_side(self): return self.side.GetStringSelection()

    def change_side(self,event):
        previous='Bottom' if self.selected_side=='Top' else 'Top'
        self.outputs[previous]=self.output.GetPath()
        self.update_side()

    def update_side(self):
        side=self.selected_side; data=service.state(self.board)
        self.layers=service.available_layers(self.board,side)
        current=data['faces'].get(side,{}).get('preview',{})
        self.layer.SetItems([f'{self.board.GetLayerName(l)}  ({p.BOARD.GetStandardLayerName(l)})' for l in self.layers])
        if self.layers:
            self.layer.SetSelection(self.layers.index(current['layer']) if current.get('layer') in self.layers else 0)
        filename=Path(self.board.GetFileName()) if self.board.GetFileName() else Path.home()/'carte.kicad_pcb'
        default=filename.with_name(filename.stem+'_vias_'+side.lower()+'.nd')
        face=data['faces'].get(side,{})
        previous=face.get('preview',face.get('merged',{})).get('output',str(default))
        self.output.SetPath(self.outputs.get(side,previous))
        self.merge.SetLabel('Fusionner vers '+('F.SilkS' if side=='Top' else 'B.SilkS'))
        self.refresh_actions()
        self.Layout()

    def refresh_actions(self,event=None):
        index=self.layer.GetSelection(); valid=0<=index<len(self.layers)
        self.generate.Enable(valid)
        preview=service.state(self.board)['faces'].get(self.selected_side,{}).get('preview',{})
        self.merge.Enable(bool(valid and preview and preview['layer']==self.layers[index]))
        self.status.SetLabel('La couche sera renommée Kicad_Via_'+self.selected_side.upper()+'.' if valid
                             else 'Aucune couche disponible : libérez une couche utilisateur.')

    def finish(self,mode):
        try:
            self.options=Options(side=self.selected_side,label_size=self.size.GetValue(),
                                 grid=self.grid.GetValue(),omit_nearby=self.near.GetValue())
            self.chosen_layer=self.layers[self.layer.GetSelection()]
            if mode=='generate' and not self.output.GetPath(): raise ValueError('Choisissez le fichier du tableau.')
            self.chosen_output=self.output.GetPath(); self.mode=mode
            self.EndModal(wx.ID_OK)
        except (ValueError,IndexError) as error:
            wx.MessageBox(str(error),'Kicad_Via',wx.OK|wx.ICON_INFORMATION,parent=self)


class KicadVia(p.ActionPlugin):
    def defaults(self):
        self.name='Kicad_Via'
        self.category='Repérage des accès de test'
        self.description='Vias Top/Bottom, repères géographiques et grille de 20 mm'
        self.show_toolbar_button=True
        self.icon_file_name=str(Path(__file__).with_name('icon.png'))
        self.dark_icon_file_name=str(Path(__file__).with_name('icon_dark.png'))

    def Run(self):
        board=p.GetBoard()
        if board is None: return
        parent=next((w for w in wx.GetTopLevelWindows() if 'pcb' in w.GetName().lower()),None)
        dialog=None
        try:
            dialog=ViaDialog(parent,board)
            if dialog.ShowModal()!=wx.ID_OK: return
            mode,layer,opt,path=dialog.mode,dialog.chosen_layer,dialog.options,dialog.chosen_output
            dialog.Destroy(); dialog=None
            # Les modifications restent dans le callback ActionPlugin, pour
            # bénéficier de la gestion native de l'historique des actions.
            with wx.BusyCursor():
                result=service.generate(board,layer,opt,path) if mode=='generate' else service.merge(board,layer,opt.side)
            p.Refresh()
            wx.MessageBox(f"{result['points']} accès, {result['labels']} labels — {result['layer']}\n"
                          f"Tableau : {result['output']}", 'Kicad_Via',wx.OK|wx.ICON_INFORMATION,parent=parent)
        except Exception as error:
            # Le texte destiné à l'utilisateur reste concret ; la trace est
            # conservée séparément pour diagnostiquer un éventuel défaut.
            log=Path(wx.StandardPaths.Get().GetUserLocalDataDir())/'Kicad_Via_error.log'
            try: log.parent.mkdir(parents=True,exist_ok=True); log.write_text(traceback.format_exc(),encoding='utf-8')
            except OSError: pass
            wx.MessageBox(str(error),'Kicad_Via — opération interrompue',wx.OK|wx.ICON_ERROR,parent=parent)
        finally:
            if dialog is not None: dialog.Destroy()
