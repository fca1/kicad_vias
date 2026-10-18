"""Copie graphique vers Fusion : ULP contrôlé, sans connexion à l'application."""
import json
import math
from pathlib import Path
import statistics
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import pcbnew as p
from . import service
from .geometry import mm


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


def alignment(board,elements):
    """Même transformation que la passerelle : translation X et inversion Y.

    Les coordonnées de la grille de repérage ne sont pas celles du PCB Fusion.
    Vérifier chaque origine de composant évite un décalage silencieux du dessin.
    """
    footprints={}
    for fp in board.GetFootprints():
        ref=fp.GetReference()
        if ref in footprints: raise ValueError('Référence KiCad dupliquée : '+ref)
        footprints[ref]=fp
    if any(e.get('name') not in footprints for e in elements):
        raise ValueError('Des composants de la source Fusion manquent dans KiCad.')
    if len({(float(e.get('x')),float(e.get('y'))) for e in elements})<2:
        raise ValueError('Deux origines de composants différentes sont requises.')
    offsets=[(mm(footprints[e.get('name')].GetPosition().x)-float(e.get('x')),
              mm(footprints[e.get('name')].GetPosition().y)+float(e.get('y'))) for e in elements]
    dx=statistics.median(v[0] for v in offsets); sy=statistics.median(v[1] for v in offsets)
    if any(math.hypot(x-dx,y-sy)>.01 for x,y in offsets):
        raise ValueError('Implantation KiCad différente du BRD/FBRD : alignement refusé.')
    return lambda v:(mm(v.x)-dx,sy-mm(v.y))


def arc_points(item):
    """Discrétiser les arcs avec une erreur de corde d'au plus 5 micromètres."""
    points=[(mm(v.x),mm(v.y)) for v in (item.GetStart(),item.GetArcMid(),item.GetEnd())]
    (ax,ay),(bx,by),(cx,cy)=points
    d=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    if abs(d)<1e-12: raise ValueError('Arc dégénéré dans le repérage.')
    a=ax*ax+ay*ay;b=bx*bx+by*by;c=cx*cx+cy*cy
    ox=(a*(by-cy)+b*(cy-ay)+c*(ay-by))/d
    oy=(a*(cx-bx)+b*(ax-cx)+c*(bx-ax))/d
    angles=[math.atan2(y-oy,x-ox) for x,y in points]
    sweep=(angles[2]-angles[0])%(2*math.pi)
    if (angles[1]-angles[0])%(2*math.pi)>sweep: sweep-=2*math.pi
    radius=math.hypot(ax-ox,ay-oy)
    step=2*math.acos(max(-1,1-min(.005/radius,1)))
    count=max(2,math.ceil(abs(sweep)/step))
    return [p.VECTOR2I(p.FromMM(ox+radius*math.cos(angles[0]+sweep*i/count)),
                       p.FromMM(oy+radius*math.sin(angles[0]+sweep*i/count))) for i in range(count+1)]


def strokes(items,transform):
    result=[]
    def add(a,b,width):
        a,b=transform(a),transform(b)
        if a!=b: result.append((*a,*b,width))
    for item in items:
        if isinstance(item,p.PCB_TEXT):
            # Le moteur KiCad fournit les traits déjà positionnés, tournés et
            # miroités. Aucune substitution par une autre police dans Fusion.
            shape=item.GetEffectiveTextShape()
            if not isinstance(shape,p.SHAPE_COMPOUND):
                raise ValueError('Utilisez une police vectorielle KiCad pour les labels.')
            for part in shape.GetSubshapes():
                if not isinstance(part,p.SHAPE_SEGMENT):
                    raise ValueError('Police à contours non prise en charge pour Fusion.')
                add(part.GetSeg().A,part.GetSeg().B,mm(part.GetWidth()))
        elif isinstance(item,p.PCB_SHAPE):
            if item.GetShape()==p.SHAPE_T_SEGMENT:
                add(item.GetStart(),item.GetEnd(),mm(item.GetWidth()))
            elif item.GetShape()==p.SHAPE_T_ARC:
                pts=arc_points(item)
                for a,b in zip(pts,pts[1:]): add(a,b,mm(item.GetWidth()))
            else: raise ValueError('Dessin modifié : seuls traits et arcs sont exportables.')
        else: raise ValueError('Objet étranger au dessin Kicad_Via.')
    if not result: raise ValueError('Aucun trait à exporter.')
    return result


def prepare(board,side,source,destination):
    face=service.state(board)['faces'].get(side,{})
    record=face.get('preview') or face.get('merged')
    if not record: raise ValueError('Générez d’abord le repérage de cette face.')
    items,_=service.validate_record(board,record,record['layer'] in service.USER_LAYERS)
    elements=read_source(source); transform=alignment(board,elements)
    wires=strokes(items,transform)
    destination=Path(destination).expanduser().resolve()
    if not destination.is_dir(): raise ValueError('Choisissez un dossier de sortie existant.')
    q=lambda s:json.dumps(s,ensure_ascii=True)
    layer='tPlace' if side=='Top' else 'bPlace'
    ulp=['// Kicad_Via : copie additive des labels et dessins uniquement.',
         'string refs[], packages[]; real xs[], ys[], angles[]; int mirrors[];',
         'int count=0, layers=0; string issue="";',
         'if (!board) { dlgMessageBox("Ouvrir le PCB cible Fusion."); exit(1); }']
    for i,e in enumerate(elements):
        rot=e.get('rot','R0');angle=float(rot.replace('S','').replace('M','').replace('R',''))
        ulp.append(f'refs[{i}]={q(e.get("name"))}; packages[{i}]={q(e.get("package",""))}; xs[{i}]={float(e.get("x")):.9f}; ys[{i}]={float(e.get("y")):.9f}; angles[{i}]={angle:.9f}; mirrors[{i}]={int("M" in rot)};')
    ulp.extend(['board(B) {',f'  B.layers(L) if (L.name=={q(layer)}) layers++;',
                '  B.elements(E) { int found=-1; count++;',
                f'    for (int i=0; i<{len(elements)}; i++) if (E.name==refs[i]) found=i;',
                '    if (found<0) issue="Composant inattendu : " + E.name;',
                '    else if (abs(u2mm(E.x)-xs[found])>0.01 || abs(u2mm(E.y)-ys[found])>0.01 || abs(E.angle-angles[found])>0.0001 || E.mirror!=mirrors[found] || E.footprint.name!=packages[found]) issue="Implantation differente : " + E.name;',
                '  }','}',f'if (count!={len(elements)} || layers!=1) issue="Carte ou couche cible differente.";',
                'if (issue!="") { dlgMessageBox("Copie annulee : " + issue); exit(1); }',
                'string scriptPath=filesetext(argv[0], ".scr");','output(scriptPath,"wt") {',
                f'  printf("GRID MM;\\nLAYER {layer};\\nSET WIRE_BEND 2;\\nCHANGE STYLE Continuous;\\n");'])
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
