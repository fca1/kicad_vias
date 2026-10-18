"""Installation exacte d'un commit : archive Git, sauvegarde et contrôle SHA-256."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
TARGET=Path.home()/'Documents/KiCad/10.0/3rdparty/plugins/Kicad_Via'


def install(ref='HEAD'):
    commit=subprocess.check_output(['git','rev-parse',ref+'^{commit}'],cwd=ROOT,text=True).strip()
    archive=subprocess.check_output(['git','archive','--format=zip',commit,'plugin/Kicad_Via'],cwd=ROOT)
    local=ROOT/'.local'; local.mkdir(exist_ok=True)
    run=Path(tempfile.mkdtemp(prefix='install_'+commit[:7]+'_',dir=local)).resolve()
    stage=run/'package'; stage.mkdir()
    prefix='plugin/Kicad_Via/'
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for name in z.namelist():
            if not name.startswith(prefix) or name.endswith('/'): continue
            destination=(stage/name[len(prefix):]).resolve()
            if not destination.is_relative_to(stage.resolve()): raise ValueError('Chemin d’archive invalide.')
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(z.read(name))
    build={'name':'Kicad_Via','version':'0.1.0','commit':commit}
    (stage/'_build.json').write_text(json.dumps(build,indent=2),encoding='utf-8')
    for required in ('__init__.py','action.py','geometry.py','service.py','model.py','fusion.py','icon.png','icon_dark.png'):
        if not (stage/required).is_file(): raise ValueError('Paquet incomplet : '+required)
    expected={str(f.relative_to(stage)):hashlib.sha256(f.read_bytes()).hexdigest() for f in stage.rglob('*') if f.is_file()}
    target=TARGET.resolve(); parent=(Path.home()/'Documents/KiCad/10.0/3rdparty/plugins').resolve()
    if target.parent!=parent or target.name!='Kicad_Via': raise ValueError('Destination inattendue.')
    parent.mkdir(parents=True,exist_ok=True)
    # Déplacement réversible, limité au dossier exact du plugin, sans suppression.
    if target.exists(): shutil.move(str(target),str(run/'backup'))
    try:
        shutil.copytree(stage,target)
        actual={str(f.relative_to(target)):hashlib.sha256(f.read_bytes()).hexdigest() for f in target.rglob('*') if f.is_file()}
        if actual!=expected: raise ValueError('Écart SHA-256 après installation.')
    except BaseException:
        if target.exists(): shutil.move(str(target),str(run/'failed_install'))
        if (run/'backup').exists(): shutil.move(str(run/'backup'),str(target))
        raise
    manifest={'commit':commit,'target':str(target),'files':expected,'verified':True}
    (run/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (local/'last_install.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Kicad_Via installé : '+commit[:7]+' ; '+str(len(expected))+' fichiers vérifiés.')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--commit',default='HEAD')
    install(parser.parse_args().commit)
