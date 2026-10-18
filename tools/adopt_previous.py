"""Reprendre uniquement l'ancien repérage de ce chat, à partir de ses preuves.

Le PCB reste inchangé. Le registre est initialisé seulement si UUID, géométrie
et membres du groupe concordent exactement avec la copie précédemment vérifiée.
Ce n'est pas une reconnaissance heuristique de textes sur une couche utilisateur.
"""
import argparse
import csv
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugin'))
import pcbnew as p
from Kicad_Via.geometry import uid,prepare
from Kicad_Via.model import Options,cell
from Kicad_Via import service


def signature(it):
    if isinstance(it,p.PCB_TEXT):
        return ('text',it.GetText(),it.GetPosition().x,it.GetPosition().y,
                it.GetTextSize().x,it.GetTextSize().y,it.GetTextThickness(),it.IsMirrored(),it.GetTextAngle().AsDegrees())
    if isinstance(it,p.PCB_SHAPE) and it.GetShape()==p.SHAPE_T_SEGMENT:
        return ('line',it.GetStart().x,it.GetStart().y,it.GetEnd().x,it.GetEnd().y,it.GetWidth())
    raise ValueError('L’ancien repérage contient un objet inattendu.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board');parser.add_argument('proof');parser.add_argument('table');parser.add_argument('output')
    args=parser.parse_args()
    proof=json.loads(Path(args.proof).read_text(encoding='utf-8'))
    b=p.LoadBoard(args.board);old=p.LoadBoard(proof['copie_finale'])
    current={uid(i):i for i in service.layer_objects(b,p.User_1)}
    previous={uid(i):i for i in service.layer_objects(old,p.User_1)}
    expected=set(proof['uuids_ajoutes'])
    assert set(current)==expected==set(previous)
    assert all(signature(current[i])==signature(previous[i]) for i in expected)
    groups={uid(g):g for g in b.Groups()};group=groups[proof['groupe_uuid']]
    assert {uid(i) for i in group.GetItems()}==expected
    if service.state(b)['faces']: raise ValueError('La carte possède déjà un registre Kicad_Via.')
    obstacle=prepare(b,p.User_1,Options(),obstacles_only=True)
    ext=obstacle['safe'].buffer(.3).bounds
    rows=[]
    with Path(args.table).open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f,delimiter=';'):
            rows.append(dict(repere=r['Repere'],net=r['Net'],imprime=r['Label_imprime']=='True',
                             x_mm=float(r['X_mm']),y_mm=float(r['Y_mm']),via_uuid=r['Via_UUID']))
    record=dict(layer=p.User_1,ids=sorted(expected),group=uid(group),rows=rows,bounds=list(ext),
                output=str(Path(args.output).resolve()),previous_name=str(b.GetLayerName(p.User_1)),
                migration='Repérage vérifié du 18 octobre 2026, avant création du plugin.')
    service.validate_record(b,record,True)
    service.persist('Top','preview',record)
    print('Ancien repérage reconnu :',len(expected),'graphismes ; PCB inchangé.')


if __name__=='__main__': main()
