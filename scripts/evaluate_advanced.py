"""Evaluate the frozen advanced bundle; never modify its selection or threshold."""
import json
import sys
from pathlib import Path
import numpy as np
from sklearn.metrics import (f1_score,confusion_matrix,classification_report,roc_auc_score,
                             average_precision_score,brier_score_loss,log_loss)
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from orman_ssl.advanced import context,view,ensemble_predict,state_probability,load_state,write_json,digest
from orman_ssl.predict import predict
OUT=ROOT/'experiments/advanced_v3';MODEL=ROOT/'models/advanced_v3'


def metrics(y,p,pred):
    return dict(macro_f1=float(f1_score(y,pred,average='macro',zero_division=0)),
                confusion_matrix=confusion_matrix(y,pred,labels=[0,1]).tolist(),
                per_class=classification_report(y,pred,labels=[0,1],target_names=['undisturbed_forest','clear_cut'],output_dict=True,zero_division=0),
                roc_auc=float(roc_auc_score(y,p)),pr_auc=float(average_precision_score(y,p)),
                brier=float(brier_score_loss(y,p)),log_loss=float(log_loss(y,np.stack([1-p,p],1),labels=[0,1])))


def main():
    d,parts=context();ix=parts['test'];test=view(d,ix);y=d['y'][ix];groups=d['groups'][ix]
    bundle_path=MODEL/'bundle.json';frozen_hash=digest(bundle_path)
    new=ensemble_predict(bundle_path,test);p=np.array(new['probabilities'])[:,1];pred=np.array(new['predictions'])
    old=predict(ROOT/'models/model.pt',test);oldpred=np.array(old['predictions']);oldp=np.array(old['probabilities'])[:,1]
    write_json(OUT/'test_predictions.json',new)
    rng=np.random.default_rng(60825);unique=np.unique(groups);members=[np.flatnonzero(groups==g) for g in unique]
    draws=[];paired=[];skipped=0
    for _ in range(2000):
        take=np.concatenate([members[j] for j in rng.integers(0,len(unique),len(unique))])
        if len(np.unique(y[take]))<2:skipped+=1;continue
        score=f1_score(y[take],pred[take],average='macro',zero_division=0)
        draws.append(float(score));paired.append(float(score-f1_score(y[take],oldpred[take],average='macro',zero_division=0)))
    robustness=[]
    for rate in [0.,.2,.4,.6]:
        for seed in [7,17,27]:
            test_view={k:v.copy() if isinstance(v,np.ndarray) else v for k,v in test.items()}
            mask=test_view['observed'];drop=np.random.default_rng(600+seed).random(mask.shape[:2])<rate
            mask &= ~drop[:,:,None]
            for i in range(len(mask)):
                if not mask[i].any():
                    j=np.flatnonzero(test['observed'][i].any(1))[0];mask[i,j]=test['observed'][i,j]
            q=ensemble_predict(bundle_path,test_view)
            robustness.append(dict(drop_rate=rate,seed=seed,macro_f1=float(f1_score(y,q['predictions'],average='macro')),quality_eligible=sum(q['quality_eligible'])))
    low=[]
    for row in json.loads((OUT/'low_label_training.json').read_text()):
        prob=state_probability(load_state(ROOT/row['checkpoint']),test)
        low.append(dict(method=row['config']['name'],fraction=row['fraction'],seed=row['seed'],n_labeled=len(row['labeled_ids']),
                        metrics=metrics(y,prob,prob>=.5),predictions=(prob>=.5).astype(int).tolist()))
    result=dict(bundle_sha256=frozen_hash,test_status='Previously examined 486-point benchmark; not an untouched external test',
                ensemble=metrics(y,p,pred),baseline=metrics(y,oldp,oldpred),
                calibration_comparison=dict(raw_brier=float(brier_score_loss(y,new['raw_probabilities'])),calibrated_brier=float(brier_score_loss(y,p)),
                    raw_macro_f1_at_half=float(f1_score(y,np.array(new['raw_probabilities'])>=.5,average='macro')),
                    calibrated_macro_f1_at_half=float(f1_score(y,p>=.5,average='macro')),
                    calibrated_macro_f1_at_frozen_threshold=float(f1_score(y,pred,average='macro'))),
                bootstrap=dict(requested=2000,valid=len(draws),one_class_draws_discarded=skipped,unit='spatial connected component',
                    macro_f1_95_interval=np.quantile(draws,[.025,.975]).tolist(),
                    paired_difference_95_interval=np.quantile(paired,[.025,.975]).tolist(),
                    point_difference=float(f1_score(y,pred,average='macro')-f1_score(y,oldpred,average='macro'))),
                robustness=robustness,low_label_runs=low,spatial_groups=len(unique),positive_spatial_groups=len(np.unique(groups[y==1])))
    rows={r['id']:r for r in json.loads((ROOT/'data/disfor/sample_manifest.json').read_text())}
    features=[]
    for i,identifier in enumerate(new['ids']):
        r=rows[identifier]
        features.append(dict(type='Feature',geometry=dict(type='Point',coordinates=[r['lon'],r['lat']]),
            properties=dict(id=identifier,truth=int(y[i]),prediction=int(pred[i]),clear_cut_score=float(p[i]),
                            member_std=new['member_std'][i],quality_eligible=new['quality_eligible'][i],group=int(groups[i]))))
    write_json(OUT/'test_predictions.geojson',dict(type='FeatureCollection',features=features))
    write_json(OUT/'evaluation.json',result)
    if digest(bundle_path)!=frozen_hash:raise ValueError('Evaluation modified the deployed bundle')
    print(json.dumps({k:v for k,v in result.items() if k not in ['robustness','low_label_runs']},indent=2))

if __name__=='__main__':main()
