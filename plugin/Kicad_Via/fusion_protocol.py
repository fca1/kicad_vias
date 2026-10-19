"""Lecture des sources et génération ULP, sans dépendance KiCad."""
import json
import math
from pathlib import Path
import tempfile
import re
import zipfile
import xml.etree.ElementTree as ET

ULP_STATE='int count=0, layers=0; string issue="";'


def layer_code(side):
    """Résoudre la sérigraphie Fusion 360 dans les couches de la cible.

    Les numéros de couches exportés ne sont pas une preuve de compatibilité
    avec le moteur actif. Conserver son nom réel pour la commande LAYER.
    """
    if side not in ('Top','Bottom'):raise ValueError('Face invalide.')
    name='SilkscreenTop' if side=='Top' else 'SilkscreenBottom'
    # Fusion expose des noms différents selon le document ; interroger ULP
    # avant l’écriture, sans créer une couche ni accepter un alias ambigu.
    alias='tPlace' if side=='Top' else 'bPlace'
    condition='L.name=='+json.dumps(name)+' || L.name=='+json.dumps(alias)
    lookup='  B.layers(L) if ('+condition+') { layers++; targetLayer=L.name; }'
    guards=[f'if (layers==0 && issue=="") issue="Couche de serigraphie Fusion 360 absente : {name}.";',
            f'if (layers>1 && issue=="") issue="Couche de serigraphie Fusion 360 ambigue : {name}.";']
    command='  printf("GRID MM;\\nLAYER \'%s\';\\nSET WIRE_BEND 2;\\nCHANGE STYLE Continuous;\\n", targetLayer);'
    return name,lookup,guards,command


def read_source(path):
    path=Path(path)
    if path.suffix.lower() not in ('.brd','.fbrd') or path.stat().st_size>128*1024*1024:
        raise ValueError('Choisissez une carte XML Fusion .brd ou .fbrd de moins de 128 Mo.')
    if path.suffix.lower()=='.fbrd':
        with zipfile.ZipFile(path) as z:
            entries=[i for i in z.infolist() if not i.is_dir() and i.filename.lower().endswith('.brd')]
            if len(entries)!=1 or entries[0].file_size>128*1024*1024:
                raise ValueError('Le FBRD doit contenir un seul BRD de moins de 128 Mo.')
            data=z.read(entries[0])
    else: data=path.read_bytes()
    if b'<!ENTITY' in data.upper(): raise ValueError('Entités XML non prises en charge.')
    root=ET.fromstring(data)
    board=root.find('./drawing/board')
    if root.tag!='eagle' or board is None: raise ValueError('Source sans carte XML Fusion.')
    elements=list(board.findall('./elements/element'))
    if len(elements)<2 or len({e.get('name') for e in elements})!=len(elements):
        raise ValueError('Deux composants distincts au minimum sont requis pour contrôler la cible.')
    for e in elements:
        for key in ('x','y'):
            if not math.isfinite(float(e.get(key))): raise ValueError('Coordonnée source invalide.')
    return elements


def export_wires(elements,wires,side,destination):
    destination=Path(destination).expanduser().resolve()
    if not destination.is_dir(): raise ValueError('Choisissez un dossier de sortie existant.')
    q=lambda s:json.dumps(s,ensure_ascii=True)
    layer,lookup,guards,command=layer_code(side)
    ulp=['// Kicad_Via : copie additive des labels et dessins uniquement.',
         'string refs[], packages[]; real xs[], ys[], angles[]; int mirrors[];',
         ULP_STATE+' string targetLayer="";',
         'if (!board) { dlgMessageBox("Ouvrir le PCB cible Fusion."); exit(1); }']
    for i,e in enumerate(elements):
        rot=e.get('rot','R0');angle=float(rot.replace('S','').replace('M','').replace('R',''))
        ulp.append(f'refs[{i}]={q(e.get("name"))}; packages[{i}]={q(e.get("package",""))}; xs[{i}]={float(e.get("x")):.9f}; ys[{i}]={float(e.get("y")):.9f}; angles[{i}]={angle:.9f}; mirrors[{i}]={int("M" in rot)};')
    ulp.extend(['board(B) {',lookup,
                '  B.elements(E) { int found=-1; count++;',
                f'    for (int i=0; i<{len(elements)}; i++) if (E.name==refs[i]) found=i;',
                '    if (found<0) issue="Composant inattendu : " + E.name;',
                '    else if (abs(u2mm(E.x)-xs[found])>0.01 || abs(u2mm(E.y)-ys[found])>0.01 || abs(E.angle-angles[found])>0.0001 || E.mirror!=mirrors[found] || E.footprint.name!=packages[found]) issue="Implantation differente : " + E.name;',
                '  }','}',f'if (count!={len(elements)} && issue=="") issue="Nombre de composants different de la source.";',
                *guards,
                'if (issue!="") { dlgMessageBox("Copie annulee : " + issue); exit(1); }',
                'string scriptPath=filesetext(argv[0], ".scr");','output(scriptPath,"wt") {',
                command])
    for x1,y1,x2,y2,width in wires:
        ulp.append(f'  printf("WIRE {width:.6f} ({x1:.6f} {y1:.6f}) ({x2:.6f} {y2:.6f});\\n");')
    ulp.extend(['}', 'if (fileerror()) { dlgMessageBox("Erreur de creation du script."); exit(1); }',
                'if (dlgMessageBox("Ajouter les labels et dessins Kicad_Via sur la serigraphie ? Ne lancer qu une fois pour eviter les doublons.", "Ajouter", "+Annuler")==0)',
                '  exit("SCRIPT \'" + scriptPath + "\';");','exit(0);'])
    # Dossier neuf pour chaque préparation : ni ancienne livraison ni projet
    # Fusion ne sont écrasés, et la commande reste liée à cet instantané.
    job=Path(tempfile.mkdtemp(prefix='Kicad_Via_'+side.lower()+'_',dir=destination))
    target=job/'labels_vias.ulp';target.write_text('\n'.join(ulp)+'\n',encoding='utf-8')
    return {'path':str(target),'command':"RUN '"+str(target).replace("'","''")+"';",
            'strokes':len(wires),'side':side,'layer':layer}
