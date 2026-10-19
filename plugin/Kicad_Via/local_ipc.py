"""Commandes locales JSON : même service que l'IHM, une opération à la fois."""
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class CommandError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def board_identity(session):
    doc = session.board.document
    return {'filename': doc.board_filename, 'project': doc.project.path,
            'vias': session.board_id}


class Controller:
    def __init__(self, session, socket_path):
        if not socket_path:
            raise ValueError('Socket KiCad explicite obligatoire.')
        self.session = session
        self.lock = threading.Lock()
        self.instance = secrets.token_hex(16)
        self.socket_path = socket_path
        self.board = board_identity(session)
        self.board_key = hashlib.sha256(json.dumps(self.board, sort_keys=True).encode()).hexdigest()

    def execute(self, request):
        if not isinstance(request, dict):
            raise CommandError('Objet JSON attendu.')
        if request.get('instance') != self.instance:
            raise CommandError('Instance du plugin différente.', 409)
        command = request.get('command')
        if command not in ('status', 'generate', 'merge', 'export'):
            raise CommandError('Commande inconnue.')
        if command == 'status' and self.lock.locked():
            return self.status(True)
        if not self.lock.acquire(blocking=False):
            raise CommandError('Opération déjà en cours.', 409)
        try:
            self.session.refresh()
            # Une autre carte ou un ensemble de vias différent exige une nouvelle
            # session : un ancien client ne doit jamais écrire sur une nouvelle cible.
            if board_identity(self.session) != self.board:
                raise CommandError('Carte changée : relancez le plugin.', 409)
            if command == 'status':
                return self.status(False)
            if request.get('board') != self.board_key:
                raise CommandError('Identité de carte manquante ou différente.', 409)
            params = request.get('params', {})
            if not isinstance(params, dict):
                raise CommandError('Paramètres invalides.')
            side = params.get('side')
            if side not in ('Top', 'Bottom'):
                raise CommandError('Face Top ou Bottom obligatoire.')
            if command == 'export':
                from .ipc_fusion import prepare
                return prepare(self.session, side, self.path(params, 'source'),
                               self.path(params, 'destination'))
            layer = params.get('layer')
            available = self.session.available_layers(side)
            if type(layer) is not int or layer not in available:
                raise CommandError('Couche IPC indisponible : consultez status.')
            if command == 'merge':
                return self.session.merge(side, layer)
            size = params.get('size', .65)
            if type(size) not in (int, float) or not math.isfinite(size) or not .4 <= size <= 2:
                raise CommandError('Taille entre 0,4 et 2 mm requise.')
            grid = params.get('grid', True)
            if type(grid) is not bool:
                raise CommandError('grid doit être booléen.')
            return self.session.generate(side, layer, size, grid, self.path(params, 'output'))
        finally:
            self.lock.release()

    @staticmethod
    def path(params, key):
        value = params.get(key)
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise CommandError('Chemin absolu obligatoire : ' + key)
        return value

    def status(self, busy):
        result = dict(instance=self.instance, board=self.board_key, target=self.board,
                      socket=self.socket_path, busy=busy)
        if not busy:
            result['layers'] = {side: [{'id': layer, 'name': self.session.names[layer]}
                                      for layer in self.session.available_layers(side)]
                                for side in ('Top', 'Bottom')}
        return result


class LocalServer:
    def __init__(self, controller, directory=None):
        self.controller = controller
        self.token = secrets.token_hex(32)
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass  # Ne jamais journaliser les jetons ou les données de carte.

            def do_POST(self):
                try:
                    if self.path != '/v1' or self.headers.get('Origin') is not None:
                        raise CommandError('Requête non autorisée.', 403)
                    if not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + owner.token):
                        raise CommandError('Authentification requise.', 403)
                    if self.headers.get('Content-Type') != 'application/json':
                        raise CommandError('Content-Type application/json requis.')
                    length = int(self.headers.get('Content-Length', '0'))
                    if not 0 < length <= 65536:
                        raise CommandError('Taille de requête invalide.')
                    self.connection.settimeout(5)
                    data = json.loads(self.rfile.read(length))
                    result = owner.controller.execute(data)
                    self.reply(200, dict(ok=True, result=result))
                except Exception as error:
                    self.reply(getattr(error, 'status', 400), dict(ok=False, error=str(error)))

            def reply(self, status, value):
                payload = json.dumps(value, ensure_ascii=False, default=str).encode('utf-8')
                try:
                    self.send_response(status)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Content-Length', str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except (OSError, TimeoutError):
                    pass  # Une déconnexion client n'annule pas une écriture déjà engagée.

        directory = Path(directory or Path.home() / 'AppData/Local/Kicad_Via/control')
        directory.mkdir(parents=True, exist_ok=True)
        # Le verrou OS survit aux demandes concurrentes mais est libéré même
        # après un crash. Deux dialogues ne doivent pas piloter la même instance.
        key = hashlib.sha256(controller.socket_path.encode()).hexdigest()
        self.instance_lock = (directory / (key + '.lock')).open('a+b')
        self.instance_lock.write(b'0')
        self.instance_lock.flush()
        self.instance_lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.instance_lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.instance_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.instance_lock.close()
            raise ValueError('Une interface locale contrôle déjà cette instance KiCad.')
        self.http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.path = directory / (controller.instance + '.json')
        descriptor = dict(protocol=1, url='http://127.0.0.1:%d/v1' % self.http.server_port,
                          token=self.token, instance=controller.instance, pid=os.getpid(),
                          socket=controller.socket_path, board=controller.board_key,
                          target=controller.board)
        with self.path.open('x', encoding='utf-8') as stream:
            json.dump(descriptor, stream, ensure_ascii=False)
        self.path.chmod(0o600)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.http.shutdown()
        self.http.server_close()
        self.path.unlink(missing_ok=True)
        self.instance_lock.close()


def call(descriptor_path, command, params=None, timeout=120):
    """Client explicite ; jamais de sélection implicite ni de relance après timeout."""
    descriptor = json.loads(Path(descriptor_path).read_text(encoding='utf-8'))
    from urllib.parse import urlsplit
    url = urlsplit(descriptor['url'])
    if url.scheme != 'http' or url.hostname != '127.0.0.1' or url.path != '/v1':
        raise ValueError('Adresse locale invalide.')
    data = json.dumps(dict(instance=descriptor['instance'], board=descriptor['board'],
                           command=command, params=params or {})).encode()
    request = Request(descriptor['url'], data=data,
                      headers={'Authorization': 'Bearer ' + descriptor['token'],
                               'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.load(response)
    except HTTPError as error:
        result = json.load(error)
    if not result['ok']:
        raise RuntimeError(result['error'])
    return result['result']


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--descriptor')
    parser.add_argument('--command', choices=['status', 'generate', 'merge', 'export'])
    parser.add_argument('--params', default='{}')
    args = parser.parse_args()
    if not args.serve:
        if not args.descriptor or not args.command:
            parser.error('--descriptor et --command requis')
        print(json.dumps(call(args.descriptor, args.command, json.loads(args.params)), ensure_ascii=False, default=str))
        return
    socket = os.environ.get('KICAD_API_SOCKET')
    if not socket:
        parser.error('KICAD_API_SOCKET explicite requis')
    from kipy import KiCad
    from .ipc_service import Session
    server = LocalServer(Controller(Session(KiCad(socket_path=socket, timeout_ms=10000)), socket))
    print(str(server.path), flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()


if __name__ == '__main__':
    main()
