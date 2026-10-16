"""Publication figures from complete, frozen cross-fitting outputs."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper/figures';OUT.mkdir(parents=True,exist_ok=True)
a=json.loads((ROOT/'experiments/paper_v4/analysis.json').read_text())
s={(r['budget'],r['method']):r for r in a['summary']}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.dpi':240})
names={'rf_leaf4':'Random forest','cnn64':'Temporal CNN','transformer48':'Transformer','ssl_transformer48':'Block + band SSL','iid_ssl':'Independent-cell SSL','step_matched':'Step-matched Transformer','mask_only':'Observation mask only','metadata_only':'Location / year / campaign'}
colors=['#6c757d','#267d87','#e1a23b','#263d70']
def save(fig,name):
    fig.savefig(OUT/f'{name}.png',bbox_inches='tight');fig.savefig(OUT/f'{name}.pdf',bbox_inches='tight');plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(10,4.2),sharey=True)
for ax,budget in zip(axes,[.2,1.]):
    for j,(method,color) in enumerate(zip(['rf_leaf4','cnn64','transformer48','ssl_transformer48'],colors)):
        r=s[budget,method]
        ax.errorbar(j,r['macro_f1_mean'],yerr=r['macro_f1_std'],fmt='o',color=color,capsize=5,ms=8)
        ax.scatter(j+np.array([-.1,0,.1]),[v['macro_f1'] for v in r['seed_results']],color=color,alpha=.5,s=20)
    ax.set_xticks(range(4),['RF','CNN','Transformer','SSL']);ax.set_title(f'{int(budget*100)}% of training labels');ax.grid(axis='y',alpha=.18);ax.set_ylim(.78,.97)
axes[0].set_ylabel('Pooled out-of-fold macro-F1');fig.tight_layout();save(fig,'01_primary')
fig,axes=plt.subplots(1,2,figsize=(10,4.4),gridspec_kw={'width_ratios':[1,1.05]})
methods=['mask_only','metadata_only','transformer48','rf_leaf4','iid_ssl','ssl_transformer48','cnn64','step_matched']
for j,m in enumerate(methods):
    r=s[.2,m];axes[0].errorbar(r['macro_f1_mean'],j,xerr=r['macro_f1_std'],fmt='o',color='#263d70',capsize=3)
axes[0].set_yticks(range(8),[names[m] for m in methods]);axes[0].set_xlim(.48,.96);axes[0].set_xlabel('Macro-F1 (mean ± seed SD)');axes[0].grid(axis='x',alpha=.18)
for j,r in enumerate(a['paired_comparisons']):
    lo,hi=r['paired_group_bootstrap_95_interval'];axes[1].plot([lo,hi],[j,j],color='#267d87',lw=2);axes[1].scatter(r['mean_difference'],j,color='#263d70',zorder=3)
axes[1].set_yticks(range(5),['vs short Transformer','vs step-matched','vs independent-cell','vs random forest','vs CNN']);axes[1].yaxis.tick_right();axes[1].axvline(0,color='gray',ls='--',lw=1);axes[1].set_xlabel('SSL minus comparator macro-F1');axes[1].grid(axis='x',alpha=.18)
fig.tight_layout(w_pad=2);save(fig,'02_controls')
d=np.load(ROOT/'data/processed/real_series.npz');manifest={r['id']:r for r in json.loads((ROOT/'data/disfor/sample_manifest.json').read_text())};xy=np.array([[manifest[i]['lon'],manifest[i]['lat']] for i in d['ids']]);folds=json.loads((ROOT/'experiments/paper_v4/folds.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(10,4.4))
for f in folds:
    ix=f['test_indices'];axes[0].scatter(xy[ix,0],xy[ix,1],s=8,alpha=.6,label=str(f['fold']+1))
axes[0].set_xlabel('Longitude (degrees)');axes[0].set_ylabel('Latitude (degrees)');axes[0].legend(title='Fold',ncol=3,fontsize=8);axes[0].set_title('Sample coordinates (no basemap)')
months=d['observed'].any(-1).sum(1)
for label,name,color in [(0,'Stable forest','#267d87'),(1,'Clear-cut','#b15a46')]:
    axes[1].hist(months[d['y']==label],bins=np.arange(11.5,25.5),alpha=.6,density=True,label=name,color=color)
axes[1].set_xlabel('Observed months in the 24-month window');axes[1].set_ylabel('Within-class fraction');axes[1].legend();axes[1].set_title('Retained observation support');fig.tight_layout();save(fig,'03_data')
print('Saved three figures as PNG and vector PDF')
