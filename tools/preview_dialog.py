"""Prévisualiser la boîte sur une copie, sans appliquer de modification."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugin'))
import pcbnew as p
# Importer avant wx.App pour ne pas enregistrer le plugin dans ce processus d'essai.
from Kicad_Via.action import ViaDialog
import wx
app=wx.App(False)
board=p.LoadBoard(sys.argv[1])
dialog=ViaDialog(None,board)
dialog.SetTitle(dialog.GetTitle()+' — aperçu sans application')
print('Dimensions de la boîte :',dialog.GetSize(),flush=True)
dialog.ShowModal()
dialog.Destroy()
