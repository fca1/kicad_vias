"""Registre et tableau indépendants du backend KiCad."""
import json
import os
import string
import tempfile
from pathlib import Path
from .model import markdown_path

def ownership_root():
    return Path(os.environ.get('KICAD_VIA_STATE_DIR',str(Path.home()/'AppData/Local/Kicad_Via/ownership')))


def persist(side,kind,record):
    root=ownership_root();root.mkdir(parents=True,exist_ok=True)
    target=root/(record['group']+'.json')
    owner={'schema':1,'side':side,'kind':kind,'record':record}
    fd,name=tempfile.mkstemp(prefix='.owner_',suffix='.tmp',dir=root)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(owner,f,ensure_ascii=False,indent=2)
        os.replace(name,target)
    finally:
        Path(name).unlink(missing_ok=True)


def stage_output(path,side,rows,ext):
    """Écrire un fichier provisoire avant toute modification du PCB.

    Le fichier existant doit être un tableau produit par le plugin pour cette
    face : une liste Bottom ne remplace jamais une liste Top par mégarde.
    """
    path=markdown_path(path).expanduser().resolve()
    header=[f'# {side}','','| Repère | Net | Label imprimé | X (mm) | Y (mm) |',
            '| --- | --- | --- | ---: | ---: |']
    previous_header=[f'# {side}','','| Repère | Net | X (mm) | Y (mm) |',
                     '| --- | --- | ---: | ---: |']
    if path.suffix.lower()!='.md':
        raise ValueError('Le tableau doit avoir une extension .md.')
    if path.exists():
        text=path.read_text(encoding='utf-8-sig')
        # Reconnaître aussi l'ancien format pour permettre sa simplification,
        # tout en gardant la séparation des faces et le refus des autres fichiers.
        if not (text.startswith(f'<!-- Kicad_Via v1 {side} -->')
                or text.startswith('\n'.join(previous_header)+'\n')
                or text.startswith('\n'.join(header)+'\n')):
            raise ValueError('Ce fichier ne contient pas un tableau Kicad_Via de cette face. Choisissez un autre nom.')
    if not path.parent.is_dir(): raise ValueError('Le dossier de sortie doit exister.')
    def escape(value,literal=False):
        # Les noms de nets sont du texte littéral : Markdig interprète notamment
        # {CMD_RESET} comme des attributs et peut masquer le nom après le tilde.
        value=str(value).replace('\n',' ').replace('\r',' ')
        if literal:
            return ''.join('\\'+c if c in string.punctuation else c for c in value)
        return value.replace('|','\\|')
    lines=header
    for r in rows:
        # Le tableau sert au repérage visuel ; les valeurs précises et UUID
        # restent dans le registre interne pour les reprises du plugin.
        values=[r['repere'],r['net'],'true' if r['imprime'] else 'false',f"{r['x_mm']:.1f}",f"{r['y_mm']:.1f}"]
        lines.append('| '+' | '.join(escape(v,i==1) for i,v in enumerate(values))+' |')
    fd,name=tempfile.mkstemp(prefix='.kicad_via_',suffix='.tmp',dir=path.parent)
    with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f: f.write('\n'.join(lines)+'\n')
    return path,Path(name)


