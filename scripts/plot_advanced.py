"""Scientific figures from frozen outputs, without further model tuning."""
import json
import os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve
from sklearn.calibration import calibration_curve
OUT=ROOT/'experiments/advanced_v3';FIG=ROOT/'figures/advanced_v3';FIG.mkdir(exist_ok=True,parents=True)
a=json.loads((OUT/'evaluation.json').read_text());s=json.loads((OUT/'selection.json').read_text());p=json.loads((OUT/'test_predictions.json').read_text())
with np.load(ROOT/'data/processed/real_series.npz') as d:
    lookup=dict(zip(d['ids'],d['y']));y=np.array([lookup[i] for i in p['ids']])
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(12,4.5))
r=s['ranking'];names=[x['config']['name'] for x in r]
axes[0].errorbar([x['mean_macro_f1'] for x in r],np.arange(len(names)),xerr=[x['std'] for x in r],fmt='o',color='#27765d',capsize=3)
axes[0].set_yticks(np.arange(len(names)),labels=names)
axes[0].invert_yaxis();axes[0].set(xlim=(.6,1),xlabel='Mean macro-F1 ± fold SD',title='Training-only spatial CV · selection scores')
cm=np.array(a['ensemble']['confusion_matrix']);axes[1].imshow(cm,cmap='Greens')
for i in range(2):
    for j in range(2):axes[1].text(j,i,str(cm[i,j]),ha='center',va='center',fontsize=18,color='white' if cm[i,j]>cm.max()/2 else '#163d32')
axes[1].set(xticks=[0,1],yticks=[0,1],xticklabels=['Intact','Clear-cut'],yticklabels=['Intact','Clear-cut'],xlabel='Prediction',ylabel='Interpreted source label',title='Frozen ensemble · repeated benchmark')
fig.tight_layout();fig.savefig(FIG/'selection_and_confusion.png',dpi=180);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,4))
prob=np.array(p['probabilities'])[:,1];precision,recall,_=precision_recall_curve(y,prob)
axes[0].plot(recall,precision,color='#27765d',label=f'PR-AUC {a["ensemble"]["pr_auc"]:.3f}')
axes[0].axhline(y.mean(),ls='--',color='gray',label='Class prevalence');axes[0].set(xlabel='Clear-cut recall',ylabel='Precision',ylim=(0,1.03),title='Repeated benchmark · 38 clear-cuts');axes[0].legend()
for label,values in [('Raw ensemble',p['raw_probabilities']),('Development-calibrated',prob)]:
    observed,estimated=calibration_curve(y,values,n_bins=6,strategy='quantile');axes[1].plot(estimated,observed,'o-',label=label)
axes[1].plot([0,1],[0,1],'--',color='gray');axes[1].set(xlabel='Mean model score',ylabel='Observed clear-cut fraction',title='Reliability · quantile bins, small test support');axes[1].legend()
fig.tight_layout();fig.savefig(FIG/'precision_recall_calibration.png',dpi=180);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,4))
for method in ['transformer48','ssl_transformer48']:
    xs=[.05,.1,.2];groups=[[r['metrics']['macro_f1'] for r in a['low_label_runs'] if r['method']==method and r['fraction']==f] for f in xs]
    axes[0].errorbar(np.array(xs)*100,[np.mean(g) for g in groups],yerr=[np.std(g,ddof=1) for g in groups],marker='o',capsize=3,label=method)
axes[0].set(xlabel='Training label budget (%)',xticks=[5,10,20],ylabel='Macro-F1 ± seed SD',ylim=(0,1),title='Matched weighted training · 3 seeds');axes[0].legend()
xs=[0,.2,.4,.6];groups=[[r['macro_f1'] for r in a['robustness'] if r['drop_rate']==f] for f in xs]
axes[1].errorbar(np.array(xs)*100,[np.mean(g) for g in groups],yerr=[np.std(g,ddof=1) for g in groups],marker='o',capsize=3,color='#27765d')
axes[1].set(xlabel='Additional removed months (%)',ylabel='Macro-F1',ylim=(0,1),title='Frozen ensemble · synthetic missingness')
fig.tight_layout();fig.savefig(FIG/'label_efficiency_and_robustness.png',dpi=180);plt.close(fig)
print('Saved scientific figures:',FIG)
