"""Frozen-test analysis, group bootstrap, missing-month robustness and deploy selection."""
from pathlib import Path
import sys,json,shutil,os
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
os.environ.setdefault('MPLCONFIGDIR',str(root/'.cache/matplotlib'))
import numpy as np
from sklearn.metrics import f1_score,confusion_matrix
from orman_ssl.predict import predict
r=json.loads((root/'reports/real_experiment/results.json').read_text());d=dict(np.load(root/'data/processed/real_series.npz',allow_pickle=False))
lookup={str(s):i for i,s in enumerate(d['ids'])};test_ids=r['runs'][0]['test_ids'];ix=np.array([lookup[s] for s in test_ids]);y=d['y'][ix];groups=d['groups'][ix]
# Select method exclusively on mean validation score at full labels; fixed seed 7.
methods=['RandomForest','Transformer','SSL_Transformer']
validation={m:float(np.mean([row['validation_macro_f1'] for row in r['runs'] if row['method']==m and row['label_fraction']==1])) for m in methods}
selected=max(methods,key=lambda m:validation[m]);suffix='.joblib' if selected=='RandomForest' else '.pt'
modelpath=root/f'reports/real_experiment/checkpoints/{selected}_7_1.0{suffix}'
(root/'models').mkdir(exist_ok=True);shutil.copy2(modelpath,root/('models/model'+suffix))
modelcard=dict(method=selected,seed=7,label_fraction=1.,validation_scores=validation,selection='highest mean validation macro-F1 across seeds; seed=7 fixed, no test-based selection',
 checkpoint='models/model'+suffix,classes=r['metadata']['classes'],channels=r['metadata']['channels'],task=r['metadata']['task'])
(root/'models/model_card.json').write_text(json.dumps(modelcard,indent=2))
subset={k:v[ix] if isinstance(v,np.ndarray) and v.ndim>0 and len(v)==len(d['x']) else v for k,v in d.items()}
pred=predict(modelpath,subset);probs=np.array(pred['probabilities']);predictions=np.array(pred['predictions'])
(root/'reports/real_experiment/selected_test_predictions.json').write_text(json.dumps(pred,indent=2))
rows=json.loads((root/'data/disfor/sample_manifest.json').read_text());manifest={row['id']:row for row in rows}
features=[]
for k,sid in enumerate(test_ids):
 row=manifest[sid];features.append(dict(type='Feature',geometry=dict(type='Point',coordinates=[row['lon'],row['lat']]),properties=dict(id=sid,year=row['year'],group=row['group'],truth=int(y[k]),prediction=int(predictions[k]),score=float(probs[k].max()),correct=bool(y[k]==predictions[k]))))
(root/'reports/real_experiment/test_predictions.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=features),indent=2))
# Paired group bootstrap: retain every sample of a resampled spatial group.
rng=np.random.default_rng(908);ug=np.unique(groups);members=[np.flatnonzero(groups==g) for g in ug]
boot=[]
base=[row for row in r['runs'] if row['label_fraction']==.2 and row['method']=='Transformer']
ssl=[row for row in r['runs'] if row['label_fraction']==.2 and row['method']=='SSL_Transformer']
for _ in range(1000):
 take=np.concatenate([members[i] for i in rng.integers(0,len(ug),len(ug))])
 diffs=[]
 for a,b in zip(base,ssl):
  assert a['seed']==b['seed'] and a['test_ids']==b['test_ids']
  diffs.append(f1_score(y[take],np.array(b['predictions'])[take],labels=[0,1],average='macro',zero_division=0)-f1_score(y[take],np.array(a['predictions'])[take],labels=[0,1],average='macro',zero_division=0))
 boot.append(float(np.mean(diffs)))
interval=np.quantile(boot,[.025,.975]).tolist()
robust=[]
for rate in [0.,.2,.4,.6]:
 for seed in [7,17,27]:
  view={k:(v.copy() if isinstance(v,np.ndarray) else v) for k,v in subset.items()}
  mask=view['observed'];drop=np.random.default_rng(1000+seed).random(mask.shape[:2])<rate;mask &= ~drop[:,:,None]
  for i in range(len(mask)):
   if not mask[i].any():
    first=np.flatnonzero(subset['observed'][i].any(1))[0];mask[i,first]=subset['observed'][i,first]
  for method in methods:
   ext='.joblib' if method=='RandomForest' else '.pt'
   cp=root/f'reports/real_experiment/checkpoints/{method}_{seed}_0.2{ext}'
   q=predict(cp,view);score=f1_score(y,q['predictions'],average='macro',labels=[0,1],zero_division=0)
   robust.append(dict(method=method,seed=seed,drop_rate=rate,macro_f1=float(score)))
result=dict(selection=modelcard,selected_test_macro_f1=float(f1_score(y,predictions,average='macro')),selected_confusion_matrix=confusion_matrix(y,predictions).tolist(),
 spatial_groups_test=len(ug),positive_groups_test=len(np.unique(groups[y==1])),
 ssl_minus_supervised_at_20_percent=dict(mean=float(np.mean([b['macro_f1']-a['macro_f1'] for a,b in zip(base,ssl)])),bootstrap_95_interval=interval,resamples=1000,unit='spatial connected-component',conditional_on='fixed data preparation and geographic split'),
 robustness=robust)
(root/'reports/real_analysis.json').write_text(json.dumps(result,indent=2))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(8,4.5))
for method in methods:
 means=[np.mean([v['macro_f1'] for v in robust if v['method']==method and v['drop_rate']==rate]) for rate in [0,.2,.4,.6]]
 ax.plot([0,20,40,60],means,'o-',label=method)
ax.set(xlabel='Additional missing months (%)',ylabel='Test macro-F1',ylim=(0,1),title='REAL DISFOR • 20% training labels • fixed models');ax.grid(alpha=.2);ax.legend();fig.tight_layout();fig.savefig(root/'figures/real_robustness.png',dpi=170);plt.close(fig)
fig,ax=plt.subplots(figsize=(5,4))
cm=confusion_matrix(y,predictions);ax.imshow(cm,cmap='Greens')
for i in range(2):
 for j in range(2):ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if cm[i,j]>cm.max()/2 else '#17392f',fontsize=18)
ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['Intact','Clear-cut'],yticklabels=['Intact','Clear-cut'],xlabel='Prediction',ylabel='Interpreted label',title=selected+' • held-out test');fig.tight_layout();fig.savefig(root/'figures/real_confusion.png',dpi=170);plt.close(fig)
# Diagnostic atlas includes errors and correct predictions, deterministic order.
wrong=np.flatnonzero(y!=predictions);correct=np.flatnonzero(y==predictions)
examples=np.r_[wrong[:4],correct[:2]][:6]
fig,axs=plt.subplots(3,2,figsize=(11,9));axs=np.ravel(axs)
for ax,k in zip(axs,examples):
 raw=subset['x'][k];ma=subset['observed'][k]
 for channel,color in [(2,'#c65338'),(6,'#347a4c'),(9,'#7755a0')]:ax.plot(range(24),np.where(ma[:,channel],raw[:,channel],np.nan),label=r['metadata']['channels'][channel],color=color)
 ax.set_title(f'{test_ids[k]} | true={y[k]} pred={predictions[k]}',fontsize=9);ax.set(xlabel='Month',ylabel='Source DN');ax.legend(fontsize=7)
for ax in axs[len(examples):]:ax.axis('off')
fig.suptitle('Real-data error atlas • diagnostics only, no test tuning');fig.tight_layout();fig.savefig(root/'figures/real_error_atlas.png',dpi=150);plt.close(fig)
print(json.dumps({k:v for k,v in result.items() if k!='robustness'},indent=2))
