"""Enregistrement du bouton natif dans l'éditeur PCB KiCad."""
import wx
if wx.GetApp() is not None:
    from .action import KicadVia
    KicadVia().register()
