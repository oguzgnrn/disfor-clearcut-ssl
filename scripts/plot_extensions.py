"""English figures for the declared extensions (label-budget curve paper_v6, grouping radius paper_v5)."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper/figures';OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.dpi':240})
names={'rf_leaf4':'Random forest','cnn64':'Temporal CNN','transformer48':'Transformer (40 ep.)','ssl_transformer48':'Block + band SSL','step_matched':'Step-matched Transformer'}
colors={'rf_leaf4':'#6c757d','cnn64':'#267d87','transformer48':'#e1a23b','ssl_transformer48':'#263d70','step_matched':'#b15a46'}
def save(fig,name):
    fig.savefig(OUT/f'{name}.png',bbox_inches='tight');fig.savefig(OUT/f'{name}.pdf',bbox_inches='tight');plt.close(fig)
v6=ROOT/'experiments/paper_v6_label_curve/analysis.json'
if v6.exists():
    a=json.loads(v6.read_text())
    if a['status']=='complete_verified':
        curve=a['combined_curve']
        fig,ax=plt.subplots(figsize=(7.2,4.4))
        for m in ['rf_leaf4','cnn64','transformer48','ssl_transformer48','step_matched']:
            rows=sorted([r for r in curve if r['method']==m],key=lambda r:r['budget'])
            x=[r['budget']*100 for r in rows];y=[r['macro_f1_mean'] for r in rows];e=[r['macro_f1_std'] for r in rows]
            ax.errorbar(x,y,yerr=e,fmt='o-' if m!='step_matched' else 's--',color=colors[m],capsize=3,ms=5,lw=1.4,label=names[m])
        ax.set_xscale('log');ax.set_xticks([5,10,20,50,100],['5%','10%','20%','50%','100%']);ax.minorticks_off()
        ax.set_xlabel('Share of outer-training locations with labels');ax.set_ylabel('Pooled out-of-fold macro-F1 (mean ± seed SD)')
        ax.grid(alpha=.18);ax.legend(fontsize=8.5,loc='lower right',frameon=False);ax.set_ylim(.6,.97)
        fig.tight_layout();save(fig,'04_label_curve');print('04_label_curve')
v5=ROOT/'experiments/paper_v5_exploratory/analysis.json'
if v5.exists():
    a=json.loads(v5.read_text());support=json.loads((ROOT/'experiments/paper_v5_exploratory/support_audit.json').read_text())
    if a['status']=='complete_verified':
        vals={(r['radius_km'],r['method']):r for r in a['summary']};radii=[5,10,20];methods=['rf_leaf4','cnn64','transformer48','ssl_transformer48','step_matched']
        fig,ax=plt.subplots(figsize=(7.6,4.4));pos=np.arange(3);w=.15
        for i,m in enumerate(methods):
            ys=[vals[r,m]['macro_f1'] for r in radii]
            bars=ax.bar(pos+(i-2)*w,ys,w,color=colors[m],label=names[m])
            for b,v in zip(bars,ys):ax.text(b.get_x()+b.get_width()/2,v+.006,f'{v:.3f}',ha='center',va='bottom',fontsize=6.5,rotation=90)
        ax.set_xticks(pos,[f"{s['radius_km']} km\n{s['groups']} comp. / {s['positive_groups']} cut" for s in support['radii']],fontsize=9)
        ax.set_ylim(.6,1.0);ax.set_ylabel('Pooled out-of-fold macro-F1 (seed 7)');ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
        ax.legend(fontsize=8,ncol=3,loc='upper center',bbox_to_anchor=(.5,-.2),frameon=False)
        fig.tight_layout();save(fig,'05_radius');print('05_radius')
