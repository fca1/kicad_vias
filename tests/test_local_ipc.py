"""Contrat réseau local et refus avant écriture sur une mauvaise cible."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as N
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugin'))
from Kicad_Via.local_ipc import Controller, LocalServer, call


class LocalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.writes = []
        self.session = N(board=N(document=N(board_filename='test.kicad_pcb', project=N(path='project'))),
                         board_id='vias', refresh=lambda: None, names={42: 'Kicad_Via_TOP'},
                         available_layers=lambda side: [42],
                         generate=lambda *args: self.writes.append(args) or {'points': 3},
                         merge=lambda *args: self.writes.append(args) or {'points': 3})
        self.controller = Controller(self.session, 'explicit-socket')
        self.server = LocalServer(self.controller, self.temp.name)
        self.descriptor = json.loads(self.server.path.read_text(encoding='utf-8'))

    def tearDown(self):
        self.server.close()
        self.assertFalse(self.server.path.exists())
        self.temp.cleanup()

    def test_network_status_generate_merge(self):
        result = call(self.server.path, 'status')
        self.assertEqual(result['socket'], 'explicit-socket')
        self.assertEqual(result['target']['filename'], 'test.kicad_pcb')
        self.assertFalse(result['busy'])
        call(self.server.path, 'generate', dict(side='Top', layer=42, output=str(Path(self.temp.name)/'test.md')))
        call(self.server.path, 'merge', dict(side='Top', layer=42))
        self.assertEqual(len(self.writes), 2)

    def test_wrong_identity_and_changed_board_never_write(self):
        request = dict(command='merge', instance='other', board=self.controller.board_key,
                       params=dict(side='Top', layer=42))
        with self.assertRaisesRegex(Exception, 'Instance'):self.controller.execute(request)
        request['instance'] = self.controller.instance
        request['board'] = 'other'
        with self.assertRaisesRegex(Exception, 'Identité'):self.controller.execute(request)
        request['board'] = self.controller.board_key
        self.session.board.document.board_filename = 'other.kicad_pcb'
        with self.assertRaisesRegex(Exception, 'Carte changée'):self.controller.execute(request)
        self.assertEqual(self.writes, [])

    def test_busy_is_readable_but_mutations_refused(self):
        with self.controller.lock:
            self.assertTrue(call(self.server.path, 'status')['busy'])
            with self.assertRaisesRegex(RuntimeError, 'en cours'):
                call(self.server.path, 'merge', dict(side='Top', layer=42))
        self.assertEqual(self.writes, [])

    def test_authentication_and_browser_origin(self):
        for token, origin in [('wrong', None), (self.descriptor['token'], 'http://website.invalid')]:
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer '+token}
            if origin:headers['Origin']=origin
            request=Request(self.descriptor['url'], data=b'{}', headers=headers)
            with self.assertRaises(HTTPError) as error:urlopen(request)
            self.assertEqual(error.exception.code, 403)
        self.assertEqual(self.writes, [])

    def test_second_server_for_same_socket_refused(self):
        with self.assertRaisesRegex(ValueError, 'déjà'):
            LocalServer(Controller(self.session, 'explicit-socket'), self.temp.name)

    def test_bad_parameters_leave_service_untouched(self):
        for params in [dict(side='side', layer=42), dict(side='Top', layer=43),
                       dict(side='Top', layer=42, size=float('nan')),
                       dict(side='Top', layer=42, grid='false'),
                       dict(side='Top', layer=42, output='relative.md')]:
            with self.assertRaises(RuntimeError):call(self.server.path, 'generate', params)
        self.assertEqual(self.writes, [])


if __name__ == '__main__':unittest.main()
