"""Enregistrement natif uniquement quand le paquet est chargé par pcbnew.

Un client IPC ou un test du moteur peut importer le paquet sans wx/pcbnew.
"""
import sys
if 'pcbnew' in sys.modules:
    import wx
    if wx.GetApp() is not None:
        from .action import KicadVia
        KicadVia().register()
