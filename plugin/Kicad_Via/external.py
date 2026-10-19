"""Entrée du plugin IPC : Python externe fourni par le gestionnaire KiCad."""
import json
import os
from pathlib import Path
import queue
import sys
import threading
import traceback
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from kipy import KiCad
from Kicad_Via.ipc_service import Session
from Kicad_Via.local_ipc import Controller, LocalServer


class Window:
    def __init__(self):
        self.root=tk.Tk();self.root.title('Kicad_Via — IPC');self.root.minsize(690,390)
        self.controller=None;self.control_server=None
        self.events=queue.Queue();self.busy=False;self.session=None;self.layer_ids=[];self.result=None
        self.side=tk.StringVar(value='Top');self.size=tk.StringVar(value='0.65')
        self.grid=tk.BooleanVar(value=True);self.layer=tk.StringVar();self.path=tk.StringVar()
        self.status=tk.StringVar(value='Connexion à la carte ouverte…')
        frame=ttk.Frame(self.root,padding=18);frame.grid(sticky='nsew');frame.columnconfigure(1,weight=1)
        self.root.columnconfigure(0,weight=1);self.root.rowconfigure(0,weight=1)
        ttk.Label(frame,text='Repérage des accès de test',font=('Segoe UI',13,'bold')).grid(row=0,column=0,columnspan=3,sticky='w',pady=(0,12))
        ttk.Label(frame,text='Face').grid(row=1,column=0,sticky='w')
        side=ttk.Combobox(frame,textvariable=self.side,values=['Top','Bottom'],state='readonly',width=12);side.grid(row=1,column=1,sticky='w');side.bind('<<ComboboxSelected>>',lambda e:self.select_side())
        ttk.Label(frame,text='Taille du label (mm)').grid(row=2,column=0,sticky='w',pady=8)
        ttk.Spinbox(frame,textvariable=self.size,from_=.4,to=2,increment=.05,width=12).grid(row=2,column=1,sticky='w')
        ttk.Label(frame,text='Couche des repères').grid(row=3,column=0,sticky='w')
        self.layers=ttk.Combobox(frame,textvariable=self.layer,state='readonly',width=36);self.layers.grid(row=3,column=1,sticky='ew')
        ttk.Button(frame,text='Actualiser',command=self.refresh).grid(row=3,column=2,padx=(8,0))
        ttk.Label(frame,text='Dans KiCad, renommez une couche User libre Kicad_Via_TOP ou Kicad_Via_BOTTOM,\npuis actualisez. Seuls ses repères connus pourront être remplacés.',wraplength=650).grid(row=4,column=0,columnspan=3,sticky='w',pady=10)
        ttk.Checkbutton(frame,text='Grille en pointillés — pas de 20 mm',variable=self.grid).grid(row=5,column=0,columnspan=3,sticky='w')
        ttk.Label(frame,text='Tableau Markdown').grid(row=6,column=0,sticky='w',pady=10)
        ttk.Entry(frame,textvariable=self.path,width=48).grid(row=6,column=1,sticky='ew')
        ttk.Button(frame,text='Parcourir…',command=self.browse).grid(row=6,column=2,padx=(8,0))
        actions=ttk.Frame(frame);actions.grid(row=7,column=0,columnspan=3,sticky='w',pady=10)
        self.generate_button=ttk.Button(actions,text='Générer / remplacer',command=self.generate);self.generate_button.pack(side='left')
        self.merge_button=ttk.Button(actions,text='Fusionner vers F.SilkS',command=self.merge);self.merge_button.pack(side='left',padx=8)
        self.fusion_button=ttk.Button(actions,text='Copier vers Fusion…',command=self.fusion);self.fusion_button.pack(side='left')
        ttk.Label(frame,textvariable=self.status,wraplength=650).grid(row=8,column=0,columnspan=3,sticky='w',pady=6)
        self.copy_button=ttk.Button(frame,text='Copier la commande RUN',command=self.copy_run,state='disabled');self.copy_button.grid(row=9,column=0,columnspan=2,sticky='w')
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.root.after(100,self.poll);self.refresh()

    def close(self):
        if self.busy:return
        if self.controller and not self.controller.lock.acquire(blocking=False):return
        try:
            if self.control_server:self.control_server.close()
            self.root.destroy()
        finally:
            if self.controller:self.controller.lock.release()

    def launch(self,operation,callback):
        if self.busy:return
        self.busy=True;self.status.set('Opération en cours…')
        for button in (self.generate_button,self.merge_button,self.fusion_button):button.configure(state='disabled')
        def worker():
            locked=False
            try:
                if self.controller:
                    locked=self.controller.lock.acquire(blocking=False)
                    if not locked:raise ValueError('Une commande IPC locale est en cours.')
                self.events.put((callback,operation(),None))
            except Exception as error:
                log=Path.home()/'AppData/Local/Kicad_Via/ipc_external_error.log';log.parent.mkdir(parents=True,exist_ok=True)
                log.write_text(traceback.format_exc(),encoding='utf-8');self.events.put((callback,None,str(error)))
            finally:
                if locked:self.controller.lock.release()
        threading.Thread(target=worker,daemon=True).start()

    def poll(self):
        try:
            callback,result,error=self.events.get_nowait();self.busy=False
            for button in (self.generate_button,self.merge_button,self.fusion_button):button.configure(state='normal')
            if error:self.status.set(error);messagebox.showerror('Kicad_Via',error,parent=self.root)
            else:callback(result)
        except queue.Empty:pass
        self.root.after(100,self.poll)

    def refresh(self):
        def operation():
            if self.session is None:
                if not os.environ.get('KICAD_API_SOCKET'):raise ValueError('Lancez Kicad_Via depuis le bouton de KiCad.')
                self.session=Session(KiCad(timeout_ms=10000))
                self.controller=Controller(self.session,os.environ['KICAD_API_SOCKET'])
                self.control_server=LocalServer(self.controller)
            else:self.session.refresh()
        self.launch(operation,lambda result:self.select_side())

    def select_side(self):
        if not self.session or (self.controller and self.controller.lock.locked()):return
        self.layer_ids=self.session.available_layers(self.side.get())
        names=[self.session.names[i] for i in self.layer_ids];self.layers.configure(values=names)
        self.layer.set(names[0] if names else '')
        self.merge_button.configure(text='Fusionner vers '+('F.SilkS' if self.side.get()=='Top' else 'B.SilkS'))
        doc=self.session.board.document
        self.path.set(str(Path(doc.project.path)/(Path(doc.board_filename).stem+'_vias_'+self.side.get().lower()+'.md')))
        self.status.set('Prêt — '+doc.board_filename if names else 'Renommez une couche User libre dans KiCad, puis cliquez sur Actualiser.')

    def browse(self):
        value=filedialog.asksaveasfilename(parent=self.root,title='Tableau de correspondance',defaultextension='.md',filetypes=[('Markdown','*.md')],initialfile=Path(self.path.get()).name)
        if value:self.path.set(value)

    def chosen_layer(self):
        if self.layers.current()<0:raise ValueError('Préparez la couche User puis actualisez.')
        return self.layer_ids[self.layers.current()]

    def generate(self):
        try:side=self.side.get();layer=self.chosen_layer();size=float(self.size.get().replace(',','.'));grid=self.grid.get();path=self.path.get()
        except ValueError as error:messagebox.showerror('Kicad_Via',str(error));return
        self.launch(lambda:self.session.generate(side,layer,size,grid,path),self.completed)

    def merge(self):
        try:side=self.side.get();layer=self.chosen_layer()
        except ValueError as error:messagebox.showerror('Kicad_Via',str(error));return
        self.launch(lambda:self.session.merge(side,layer),self.completed)

    def completed(self,result):
        text=f"{result['points']} accès, {result['labels']} labels.\nTableau : {result['output']}"
        self.status.set(text);messagebox.showinfo('Kicad_Via — terminé',text,parent=self.root)

    def fusion(self):
        if self.busy:return
        source=filedialog.askopenfilename(parent=self.root,title='Source Fusion',filetypes=[('Fusion Electronics','*.brd *.fbrd')])
        if not source:return
        dest=filedialog.askdirectory(parent=self.root,title='Dossier de sortie Fusion')
        if not dest:return
        side=self.side.get()
        def operation():
            from Kicad_Via.ipc_fusion import prepare
            return prepare(self.session,side,source,dest)
        def done(result):
            self.result=result;self.copy_button.configure(state='normal');self.status.set(str(result['strokes'])+' traits préparés. Copiez RUN, puis lancez-le dans Fusion.')
        self.launch(operation,done)

    def copy_run(self):
        if self.result:
            self.root.clipboard_clear();self.root.clipboard_append(self.result['command']);self.status.set('Commande RUN copiée.')


if __name__=='__main__':
    Window().root.mainloop()
