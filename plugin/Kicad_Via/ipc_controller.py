"""Coordinateur hybride : réseau hors GUI, renommage natif sur le fil GUI."""
import os
import threading
import traceback
import wx
import pcbnew as p
from .ipc_adapter import IPCAdapter
from . import ipc_jobs

_active=False

class InteractionGuard(wx.EventFilter):
    # Désactiver la frame ferait refuser IPC (CanAcceptApiCommands=IsEnabled).
    # Filtrer seulement les entrées utilisateur laisse fonctionner les événements
    # réseau et CallAfter. Aucun événement de dessin ou timer n'est intercepté.
    def __init__(self,parent):
        super().__init__();self.parent=parent
    def FilterEvent(self,event):
        if not self.parent:return self.Event_Skip
        obj=event.GetEventObject()
        if not isinstance(obj,wx.Window) or wx.GetTopLevelParent(obj)!=self.parent:return self.Event_Skip
        if isinstance(event,(wx.MouseEvent,wx.KeyEvent)) or event.GetEventType() in (wx.wxEVT_MENU,wx.wxEVT_TOOL,wx.wxEVT_CLOSE_WINDOW):
            return self.Event_Processed
        return self.Event_Skip


def start(board,parent,mode,layer,opt,path):
    global _active
    if _active:raise ValueError('Une opération Kicad_Via est déjà en cours.')
    # Aucun appel réseau tant que le callback ActionPlugin bloque la boucle GUI.
    prepared=ipc_jobs.generation(board,layer,opt,path) if mode=='generate' else ipc_jobs.merging(board,layer,opt.side)
    _active=True
    guard=InteractionGuard(parent);wx.EvtHandler.AddFilter(guard)

    def on_gui(fn):
        done=threading.Event();answer=[]
        def invoke():
            try:answer.append((True,fn()))
            except BaseException as error:answer.append((False,error))
            finally:done.set()
        wx.CallAfter(invoke)
        # Pas de timeout qui abandonnerait un renommage encore en file GUI.
        done.wait()
        ok,value=answer[0]
        if not ok:raise value
        return value

    def finish(error):
        global _active
        _active=False
        wx.EvtHandler.RemoveFilter(guard)
        p.Refresh()
        if error:
            wx.MessageBox(str(error),'Kicad_Via — IPC interrompu',wx.OK|wx.ICON_ERROR,parent=parent)
        else:
            r=prepared.result
            wx.MessageBox(f"{r['points']} accès, {r['labels']} labels — {r['layer']}\nTableau : {r['output']}",
                          'Kicad_Via — IPC',wx.OK|wx.ICON_INFORMATION,parent=parent)

    def worker():
        error=None
        try:
            adapter=IPCAdapter.connect(os.getpid())
            adapter.apply(prepared.job,before_commit=lambda:on_gui(prepared.rename),
                          rollback=lambda:on_gui(prepared.rollback),publish=prepared.publish,finalize=lambda:on_gui(prepared.finalize))
        except BaseException as caught:
            error=caught
            log=service_log()
            log.parent.mkdir(parents=True,exist_ok=True);log.write_text(traceback.format_exc(),encoding='utf-8')
        finally:
            try:prepared.cleanup()
            finally:wx.CallAfter(finish,error)
    try:
        threading.Thread(target=worker,name='Kicad_Via_IPC',daemon=True).start()
    except BaseException:
        _active=False;wx.EvtHandler.RemoveFilter(guard);prepared.cleanup();raise


def service_log():
    from pathlib import Path
    return Path.home()/'AppData/Local/Kicad_Via/ipc_error.log'
