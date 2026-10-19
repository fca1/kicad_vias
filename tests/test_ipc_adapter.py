"""Transactions IPC simulées : aucun accès au document utilisateur."""
import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'plugin'),str(Path(__file__).parent)]
import pcbnew as p
from test_plugin import sample
from Kicad_Via import ipc_jobs,service
from Kicad_Via.ipc_adapter import IPCAdapter,load_client
from Kicad_Via.ipc_native import encode
from Kicad_Via.model import Options
from Kicad_Via.geometry import uid
load_client()
from kipy.board_types import BoardText,BoardShape,Group
from kipy.proto.common.types import KIID


class FakeBoard:
    def __init__(self,native):
        self.objects={};self.groups={};self.enabled=[];self.visible=[];self.events=[];self.incomplete=False
        from types import SimpleNamespace
        self.vias=[SimpleNamespace(id=KIID(value=uid(v)),position=SimpleNamespace(x=v.GetPosition().x,y=v.GetPosition().y))
                   for v in native.GetTracks() if isinstance(v,p.PCB_VIA)]
    def get_vias(self):return self.vias
    def get_shapes(self):return [v for v in self.objects.values() if isinstance(v,BoardShape)]
    def get_text(self):return [v for v in self.objects.values() if isinstance(v,BoardText)]
    def get_groups(self):return list(self.groups.values())
    def get_enabled_layers(self):return self.enabled[:]
    def get_visible_layers(self):return self.visible[:]
    def set_enabled_layers(self,copper_layer_count,layers):self.enabled=list(layers)
    def set_visible_layers(self,layers):self.visible=list(layers)
    def begin_commit(self):
        self.saved=copy.deepcopy((self.objects,self.groups));self.events.append('begin');return 'commit'
    def push_commit(self,c,message):self.events.append('push')
    def drop_commit(self,c):self.objects,self.groups=self.saved;self.events.append('drop')
    def create_items(self,items):
        items=[items] if isinstance(items,Group) else list(items)
        for i in items:
            target=self.groups if isinstance(i,Group) else self.objects
            target[i.id.value]=copy.deepcopy(i)
        return items[:-1] if self.incomplete else items
    def update_items(self,items):
        for i in items:self.objects[i.id.value]=copy.deepcopy(i)
        return items
    def remove_items_by_id(self,ids):
        for i in ids:self.objects.pop(i.value,None);self.groups.pop(i.value,None)


class IPCTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.native=sample()
        self.env=patch.dict(os.environ,{'KICAD_VIA_STATE_DIR':str(self.root/'ownership')});self.env.start()
        self.remote=FakeBoard(self.native);self.adapter=IPCAdapter(self.remote)
    def tearDown(self):self.env.stop();self.tmp.cleanup()
    def prepared(self):return ipc_jobs.generation(self.native,p.User_1,Options(),self.root/'Top.md')
    def apply(self,prepared):
        self.adapter.apply(prepared.job,prepared.rename,prepared.rollback,prepared.publish)
        prepared.cleanup()
    def test_generate_exact_messages_and_group(self):
        job=self.prepared();self.apply(job)
        self.assertEqual(self.remote.events,['begin','push'])
        self.assertEqual(set(self.remote.objects),set(job.record['ids']))
        self.assertFalse(self.remote.groups)  # Groupe finalisé sur le fil GUI natif.
        self.assertTrue((self.root/'Top.md').exists())
        for item in job.job['items']:
            self.assertEqual(item.proto,self.remote.objects[item.id.value].proto)
        self.assertEqual(self.native.GetLayerName(p.User_1),'Kicad_Via_TOP')
        self.assertFalse(service.layer_objects(self.native,p.User_1))
    def test_publication_failure_rolls_back_ipc_names_and_files(self):
        job=self.prepared();old=self.native.GetLayerName(p.User_1)
        def fail():job.publish();raise OSError('publication')
        with self.assertRaises(OSError):
            self.adapter.apply(job.job,job.rename,job.rollback,fail)
        self.assertEqual(self.remote.events,['begin','drop'])
        self.assertFalse(self.remote.objects);self.assertFalse(self.remote.groups)
        self.assertFalse(job.owner.exists());self.assertFalse((self.root/'Top.md').exists())
        self.assertEqual(self.native.GetLayerName(p.User_1),old)
        self.assertEqual(self.remote.enabled,[]);job.cleanup()
    def test_partial_create_is_not_committed(self):
        job=self.prepared();self.remote.incomplete=True
        with self.assertRaisesRegex(RuntimeError,'incomplète'):self.apply(job)
        self.assertEqual(self.remote.events,['begin','drop']);self.assertFalse(self.remote.objects)
        job.cleanup()
    def test_wrong_board_is_refused_before_transaction(self):
        job=self.prepared();self.remote.vias=[]
        with self.assertRaisesRegex(ValueError,'diffère'):self.apply(job)
        self.assertEqual(self.remote.events,[]);job.cleanup()
    def test_merge_updates_only_owned_objects(self):
        service.generate(self.native,p.User_1,Options(),self.root/'Top.md')
        record=service.state(self.native)['faces']['Top']['preview']
        for it in service.layer_objects(self.native,p.User_1):
            msg=encode(it);self.remote.objects[msg.id.value]=msg
        group=Group();group.id.value=record['group'];self.remote.groups[group.id.value]=group
        job=ipc_jobs.merging(self.native,p.User_1,'Top');self.apply(job)
        from kipy.proto.board.board_types_pb2 import BoardLayer
        self.assertTrue(all(i.layer==BoardLayer.BL_F_SilkS for i in self.remote.objects.values()))
        self.assertEqual(set(self.remote.groups),{record['group']})

    def test_empty_native_group_keeps_requested_uuid(self):
        job=self.prepared();job.record['ids']=[]
        job.finalize()
        group=next(g for g in self.native.Groups() if uid(g)==job.record['group'])
        self.assertEqual(len(group.GetItems()),0);job.cleanup()

    def test_all_ghosts_still_enable_target_layer(self):
        job=self.prepared();job.job['items']=[]
        self.apply(job)
        self.assertEqual(self.remote.enabled,job.job['target_layers'])

    def test_finalization_failure_keeps_committed_ownership(self):
        job=self.prepared()
        def fail():raise RuntimeError('group')
        with self.assertRaisesRegex(RuntimeError,'registre conservé'):
            self.adapter.apply(job.job,job.rename,job.rollback,job.publish,fail)
        self.assertEqual(self.remote.events,['begin','push'])
        self.assertTrue(job.owner.exists());job.cleanup()

    def test_client_checks_individual_statuses(self):
        from Kicad_Via.ipc_adapter import CheckedClient
        from kipy.proto.common.commands import editor_commands_pb2 as commands
        from types import SimpleNamespace
        response=commands.CreateItemsResponse()
        enum=response.DESCRIPTOR.fields_by_name['status'].enum_type
        response.status=enum.values_by_name['IRS_OK'].number
        response.created_items.add().status.code=commands.ISC_INVALID_DATA
        client=CheckedClient(SimpleNamespace(send=lambda *args:response))
        request=commands.CreateItems();request.items.add()
        with self.assertRaisesRegex(RuntimeError,'Objet IPC refusé'):
            client.send(request,commands.CreateItemsResponse)

    def test_merge_preserves_remote_text_attributes(self):
        service.generate(self.native,p.User_1,Options(),self.root/'Top.md')
        for it in service.layer_objects(self.native,p.User_1):
            msg=encode(it);self.remote.objects[msg.id.value]=msg
        text=next(i for i in self.remote.objects.values() if isinstance(i,BoardText))
        text.attributes.bold=True;text.attributes.italic=True
        job=ipc_jobs.merging(self.native,p.User_1,'Top');self.apply(job)
        self.assertTrue(self.remote.objects[text.id.value].attributes.bold)
        self.assertTrue(self.remote.objects[text.id.value].attributes.italic)
