"""Comparer exactement le placement à un commit et mesurer sur une copie lue seule.

Python natif KiCad requis. Les rapports restent locaux ; aucune sauvegarde PCB.
La référence est chargée depuis le Git local, jamais téléchargée ou modifiée.
"""
import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
import types

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'plugin'))
import pcbnew as p
from Kicad_Via import geometry,service
from Kicad_Via.model import Options


def reference(commit):
    revision=subprocess.check_output(['git','rev-parse','--verify',commit+'^{commit}'],cwd=ROOT,text=True).strip()
    source=subprocess.check_output(['git','show',revision+':plugin/Kicad_Via/geometry.py'],cwd=ROOT,text=True,encoding='utf-8')
    module=types.ModuleType('Kicad_Via.benchmark_reference')
    exec(compile(source,revision+'/geometry.py','exec'),module.__dict__)
    return module,revision


def signature(plan):
    def xy(v):return (v.x,v.y)
    items=[]
    # Les UUID des nouveaux dessins sont aléatoires : comparer leur contenu
    # natif et l'association au via, dans l'ordre exact de création.
    for it in plan['items']:
        if isinstance(it,p.PCB_TEXT):
            data=('text',it.GetText(),xy(it.GetPosition()),xy(it.GetTextSize()),
                  it.GetTextThickness(),it.GetTextAngle().AsDegrees(),it.IsMirrored())
        else:
            data=('shape',it.GetShape(),xy(it.GetStart()),xy(it.GetEnd()),it.GetWidth())
            if it.GetShape()==p.SHAPE_T_ARC:data+=(xy(it.GetArcMid()),)
        items.append((data,it.GetLayer(),plan['leader_vias'].get(geometry.uid(it))))
    return dict(rows=plan['rows'],items=items,bounds=plan['bounds'],printed=plan['printed'],
                count_vias=plan['count_vias'],protections=[g.wkb_hex for g in plan['protections']])


def compare(board,opt,exclude,baseline,repeat=3):
    samples={'before':[],'after':[]};expected=None
    for n in range(repeat):
        # Alterner l'ordre pour limiter le biais de chauffe du processus.
        order=('before','after') if n%2==0 else ('after','before')
        for name in order:
            fn=baseline.prepare if name=='before' else geometry.prepare
            start=time.perf_counter();plan=fn(board,p.User_1,opt,exclude)
            samples[name].append(time.perf_counter()-start)
            value=signature(plan)
            if expected is None:expected=value
            if value!=expected:raise AssertionError('Placement différent : '+name)
    before=statistics.median(samples['before']);after=statistics.median(samples['after'])
    return dict(side=opt.side,size=opt.label_size,grid=opt.grid,access=len(expected['rows']),
                printed=expected['printed'],identical=True,samples=samples,
                before_median=before,after_median=after,speedup=before/after,
                reduction_percent=100*(1-after/before))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',default='5eb1bce')
    parser.add_argument('--board',required=True)
    parser.add_argument('--ownership',required=True)
    parser.add_argument('--report',required=True)
    parser.add_argument('--repeat',type=int,default=3)
    args=parser.parse_args()
    if args.repeat<1:parser.error('repeat doit être positif')
    os.environ['KICAD_VIA_STATE_DIR']=args.ownership
    baseline,revision=reference(args.baseline)
    board=p.LoadBoard(args.board)
    results=[]
    for opt in (Options(),Options(label_size=.4,grid=False),Options(side='Bottom')):
        result=compare(board,opt,service.excluded_ids(service.state(board),opt.side),baseline,args.repeat)
        results.append(result);print(json.dumps(result),flush=True)
    Path(args.report).write_text(json.dumps(dict(baseline=revision,results=results),indent=2),encoding='utf-8')
