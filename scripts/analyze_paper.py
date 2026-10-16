"""Aggregate every predeclared cross-fit and quantify paired group uncertainty."""
import json,sys,os
from pathlib import Path
import numpy as np
from sklearn.metrics import f1_score,average_precision_score,roc_auc_score,brier_score_loss,confusion_matrix
from sklearn.neighbors import BallTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from orman_ssl.advanced import write_json
OUT=ROOT/'experiments/paper_v4'


def macro(y,p,weights=None):
    # Exact weighted binary macro-F1 from class counts, used for efficient cluster bootstrap.
    q=p>=.5;w=np.ones(len(y)) if weights is None else weights
    tp=np.sum(w*(q&(y==1)));tn=np.sum(w*((~q)&(y==0)))
    fp=np.sum(w*(q&(y==0)));fn=np.sum(w*((~q)&(y==1)))
    return .5*((2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)+(2*tn/(2*tn+fp+fn) if 2*tn+fp+fn else 0))


def main():
    if not (OUT/'completion.json').exists():raise ValueError('All predeclared jobs must finish before aggregation')
    jobs=json.loads((OUT/'jobs.json').read_text());rows=[json.loads(p.read_text()) for p in sorted((OUT/'runs').glob('*.json'))]
    if len(rows)!=180 or len(jobs)!=180:raise ValueError('Missing or extra runs')
    d=dict(np.load(ROOT/'data/processed/real_series.npz',allow_pickle=False));lookup={str(v):i for i,v in enumerate(d['ids'])};n=len(d['ids']);y=d['y'];groups=d['groups']
    keys=sorted({(r['budget'],r['method']) for r in rows});pooled={};summary=[]
    for budget,method in keys:
        probs=[];per_seed=[]
        for seed in [7,17,27]:
            p=np.full(n,np.nan);seen=set()
            for r in [r for r in rows if r['budget']==budget and r['method']==method and r['seed']==seed]:
                train=set(r['train_ids']);test=set(r['test_ids'])
                if train&test or not set(r['labeled_ids'])<=train:raise ValueError('Split leakage')
                if seen&test:raise ValueError('Duplicate OOF assignment')
                seen |= test;ix=[lookup[i] for i in r['test_ids']];p[ix]=r['probabilities']
            if len(seen)!=n or not np.isfinite(p).all():raise ValueError('OOF coverage incomplete')
            probs.append(p);q=p>=.5;cm=confusion_matrix(y,q,labels=[0,1])
            per_seed.append(dict(seed=seed,macro_f1=float(f1_score(y,q,average='macro')),pr_auc=float(average_precision_score(y,p)),
                                 roc_auc=float(roc_auc_score(y,p)),brier=float(brier_score_loss(y,p)),clear_cut_recall=float(cm[1,1]/cm[1].sum()),confusion_matrix=cm.tolist()))
        pooled[(budget,method)]=np.stack(probs)
        group=[r for r in rows if r['budget']==budget and r['method']==method]
        summary.append(dict(budget=budget,method=method,seed_results=per_seed,macro_f1_mean=float(np.mean([r['macro_f1'] for r in per_seed])),
                            macro_f1_std=float(np.std([r['macro_f1'] for r in per_seed],ddof=1)),
                            pr_auc_mean=float(np.mean([r['pr_auc'] for r in per_seed])),recall_mean=float(np.mean([r['clear_cut_recall'] for r in per_seed])),
                            brier_mean=float(np.mean([r['brier'] for r in per_seed])),total_fit_seconds=float(sum(r['seconds'] for r in group)),
                            epochs=sorted({r['epochs'] for r in group})))
    unique,gi=np.unique(groups,return_inverse=True);rng=np.random.default_rng(120926)
    comparisons=[('transformer48','primary'),('step_matched','exploratory'),('iid_ssl','exploratory'),('rf_leaf4','exploratory'),('cnn64','exploratory')]
    draws={name:[] for name,_ in comparisons};skipped=0
    for _ in range(2000):
        sampled=rng.integers(0,len(unique),size=len(unique));weights=np.bincount(sampled,minlength=len(unique))[gi]
        if not weights[y==0].sum() or not weights[y==1].sum():skipped+=1;continue
        ssl=np.mean([macro(y,p,weights) for p in pooled[(.2,'ssl_transformer48')]])
        for name,_ in comparisons:
            other=np.mean([macro(y,p,weights) for p in pooled[(.2,name)]])
            draws[name].append(float(ssl-other))
    stats=[]
    for method,role in comparisons:
        a=pooled[(.2,'ssl_transformer48')];b=pooled[(.2,method)]
        stats.append(dict(comparator=method,role=role,mean_difference=float(np.mean([macro(y,p)-macro(y,q) for p,q in zip(a,b)])),
                          paired_group_bootstrap_95_interval=np.quantile(draws[method],[.025,.975]).tolist(),draws=len(draws[method])))
    manifest={r['id']:r for r in json.loads((ROOT/'data/disfor/sample_manifest.json').read_text())}
    coords=np.deg2rad([[manifest[i]['lat'],manifest[i]['lon']] for i in d['ids']]);distances=[]
    for fold in json.loads((OUT/'folds.json').read_text()):
        tr=fold['train_indices'];te=fold['test_indices']
        dist=float(BallTree(coords[tr],metric='haversine').query(coords[te],k=1)[0].min()*6371.0088)
        if dist<=5-1e-6:raise ValueError('Spatial buffer violation')
        distances.append(dict(fold=fold['fold'],minimum_distance_km=dist,test_class_counts=fold['test_class_counts']))
    result=dict(n=n,groups=len(unique),class_counts=np.bincount(y).tolist(),jobs=len(rows),summary=summary,paired_comparisons=stats,
        bootstrap=dict(unit='spatial component',seed_replicates_kept_together=True,draws_requested=2000,one_class_draws_discarded=skipped,
                       limitation='Conditional on fixed data, folds and trained fits; does not quantify adaptive development or correlated refitting uncertainty'),
        folds=distances,development_history=json.loads((OUT/'protocol.json').read_text())['development_history'])
    write_json(OUT/'analysis.json',result)
    arrays={'ids':d['ids'],'y':y,'groups':groups}
    for (budget,method),p in pooled.items():arrays[f'{method}_{budget}']=p
    np.savez_compressed(OUT/'oof_predictions.npz',**arrays)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
