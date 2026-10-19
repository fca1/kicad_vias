"""Transport IPC sans pcbnew : objets par lots, groupes et transaction annulable."""
import os
import sys
import time
from pathlib import Path


def load_client():
    # Dépendances isolées de Python KiCad, installées et versionnées séparément.
    root=Path.home()/'AppData/Local/Kicad_Via/ipc-python'
    if str(root) not in sys.path:sys.path.insert(0,str(root))
    from kipy import KiCad
    return KiCad


def socket_for_pid(pid):
    """Sur Windows, vérifier le propriétaire du pipe, jamais choisir au hasard."""
    if os.name!='nt':
        value=os.environ.get('KICAD_API_SOCKET')
        if not value:raise RuntimeError('Adresse IPC du processus KiCad absente.')
        return value
    import ctypes
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,
                                ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    kernel.CreateFileW.restype=wintypes.HANDLE
    kernel.GetNamedPipeServerProcessId.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.ULONG)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    prefix='\\\\.\\pipe\\'
    for name in os.listdir(prefix):
        if 'kicad' not in name.lower() or 'api.sock' not in name:continue
        handle=kernel.CreateFileW(prefix+name,0x80000000|0x40000000,0,None,3,0,None)
        if handle==wintypes.HANDLE(-1).value:continue
        try:
            owner=wintypes.ULONG()
            if kernel.GetNamedPipeServerProcessId(handle,ctypes.byref(owner)) and owner.value==pid:
                return 'ipc://'+name
        finally:kernel.CloseHandle(handle)
    raise RuntimeError('Aucun serveur IPC appartenant à cet éditeur. Activez API enabled.')


class CheckedClient:
    """kipy 0.8 ignore les statuts individuels ; ne jamais accepter un échec muet."""
    def __init__(self,client):self.client=client
    def __getattr__(self,name):return getattr(self.client,name)
    def send(self,command,response_type):
        response=self.client.send(command,response_type)
        for field in ('created_items','updated_items','deleted_items'):
            if not hasattr(response,field):continue
            status_field=response.DESCRIPTOR.fields_by_name['status']
            if status_field.enum_type.values_by_number[response.status].name!='IRS_OK':
                raise RuntimeError('Lot IPC refusé : '+str(response.status))
            results=getattr(response,field)
            expected=len(command.item_ids if field=='deleted_items' else command.items)
            if len(results)!=expected:raise RuntimeError('Réponse IPC incomplète.')
            for result in results:
                code=result.status if field=='deleted_items' else result.status.code
                if code!=1:raise RuntimeError('Objet IPC refusé : '+str(result.status))
        return response


class IPCAdapter:
    def __init__(self,board):self.board=board

    @classmethod
    def connect(cls,pid):
        KiCad=load_client();client=KiCad(socket_path=socket_for_pid(pid),timeout_ms=10000)
        # Le callback natif vient de rendre la main ; un Busy transitoire est permis.
        from kipy.client import ApiError
        for attempt in range(20):
            try:
                board=client.get_board();board._kicad=CheckedClient(board._kicad)
                adapter=cls(board);adapter.read();return adapter
            except ApiError as error:
                if 'busy' not in str(error).lower() or attempt==19:raise
                time.sleep(.1)

    def read(self):
        return dict(vias=self.board.get_vias(),shapes=self.board.get_shapes(),
                    texts=self.board.get_text(),groups=self.board.get_groups())

    def apply(self,job,before_commit=lambda:None,rollback=lambda:None,publish=lambda:None,finalize=lambda:None):
        """Tout échec avant push annule les écritures IPC et les replis natifs.

        Les UUID retournés sont contrôlés ; finalize intervient après push.
        Ne pas faire de retry des mutations, une réponse perdue reste ambiguë.
        """
        from kipy.proto.common.types import KIID
        board=self.board
        current=self.read()
        actual={i.id.value for k in ('shapes','texts') for i in current[k]}
        if 'expected_vias' in job:
            observed={i.id.value:(i.position.x,i.position.y) for i in current['vias']}
            if observed!=job['expected_vias']:raise ValueError('La carte IPC diffère du document préparé.')
        if not {i.id.value for i in job.get('updates',[])}.issubset(actual):
            raise ValueError('Un dessin à mettre à jour a disparu.')
        if job.get('remove_group') and job['remove_group'] not in {g.id.value for g in current['groups']}:
            raise ValueError('Le groupe précédent a changé.')
        if not set(job['remove_ids']).issubset(actual):
            raise ValueError('Les anciens dessins ont changé ; relancez le plugin.')
        enabled=board.get_enabled_layers();visible=board.get_visible_layers()
        layers={i.layer for i in job['items']+job.get('updates',[])}
        layers.update(job.get('target_layers',[]))
        from kipy.proto.board.board_types_pb2 import BoardLayer
        copper={layer for layer in enabled if BoardLayer.Name(layer).endswith('_Cu')}
        # L'API exige l'empilage complet : ne jamais modifier le nombre de cuivres.
        def enable(values):board.set_enabled_layers(len(copper),sorted(set(values)-copper))
        commit=board.begin_commit();fallback=False
        try:
            enable(set(enabled)|layers)
            board.set_visible_layers(sorted(set(visible)|layers))
            # Retirer le groupe avant les membres pour éviter des liens pendants.
            if job.get('remove_group'):
                board.remove_items_by_id([KIID(value=job['remove_group'])])
            if job['remove_ids']:board.remove_items_by_id([KIID(value=i) for i in job['remove_ids']])
            if job.get('updates'):
                # La fusion ne réécrit pas la police, l'alignement ou les attributs
                # édités à la main : conserver le message IPC courant en entier.
                import copy
                from kipy.board_types import BoardText
                existing={i.id.value:i for k in ('shapes','texts') for i in current[k]}
                updates=[]
                for desired in job['updates']:
                    message=copy.deepcopy(existing[desired.id.value]);message.layer=desired.layer
                    if isinstance(message,BoardText):message.attributes.mirrored=desired.attributes.mirrored
                    updates.append(message)
                changed=board.update_items(updates)
                if {i.id.value for i in changed}!={i.id.value for i in job['updates']}:
                    raise RuntimeError('Mise à jour IPC incomplète.')
            if job['items']:
                created=board.create_items(job['items'])
                if {i.id.value for i in created}!={i.id.value for i in job['items']}:
                    raise RuntimeError('Création IPC incomplète ou UUID modifiés.')
            fallback=True;before_commit()
            publish()
            board.push_commit(commit,'Kicad_Via — '+job['mode'])
        except BaseException as error:
            try:board.drop_commit(commit)
            except BaseException as drop_error:
                # Une réponse perdue au push ne permet pas de conclure à l'échec.
                # Garder le registre publié pour ne pas rendre les objets orphelins.
                raise RuntimeError('État de transaction IPC incertain ; registre conservé. '
                                   'Vérifiez la carte avant de relancer.') from drop_error
            enable(enabled);board.set_visible_layers(visible)
            if fallback:rollback()
            raise
        # Les membres créés ne sont résolus par les groupes qu'après push.
        # Le repli natif assure aussi les groupes vides (tous les accès fantômes).
        # Une erreur ici ne doit pas tenter d'annuler une transaction déjà close.
        try:finalize()
        except BaseException as error:
            raise RuntimeError('Dessins IPC validés et registre conservé, mais finalisation '
                               'du groupe impossible : '+str(error)) from error
