"""Frozen-protocol spatial cross-fitting for the paper audit."""
import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
import numpy as np
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import f1_score,average_precision_score,roc_auc_score,brier_score_loss,confusion_matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import orman_ssl.advanced as adv
from orman_ssl.experiment import subset
OUT=ROOT/'experiments/paper_v4'
ORIGINAL_BLOCK=adv.block_mask


def iid_mask(mask):
    hidden=(torch.rand(mask.shape)<(1/3))&mask
    for i in range(len(mask)):
        observed=torch.nonzero(mask[i],as_tuple=False)
        if len(observed)>1 and not (mask[i]&~hidden[i]).any():
            j,k=observed[0];hidden[i,j,k]=False
        if len(observed)>1 and not hidden[i].any():
            j,k=observed[-1];hidden[i,j,k]=True
    return hidden


def score(y,p):
    q=p>=.5
    return dict(macro_f1=float(f1_score(y,q,average='macro',zero_division=0)),pr_auc=float(average_precision_score(y,p)),
                roc_auc=float(roc_auc_score(y,p)),brier=float(brier_score_loss(y,p)),confusion_matrix=confusion_matrix(y,q,labels=[0,1]).tolist())


def worker(job):
    fold,seed,budget,method=job
    dest=OUT/'runs'/f'{method}_f{fold}_s{seed}_b{budget}.json'
    if dest.exists():return {'cached':True,'file':dest.name}
    started=time.time();torch.set_num_threads(2)
    d=dict(np.load(ROOT/'data/processed/real_series.npz',allow_pickle=False))
    splits=json.loads((OUT/'folds.json').read_text());part=splits[fold]
    train=np.array(part['train_indices']);test=np.array(part['test_indices']);labeled=subset(d['y'],train,budget,seed)
    config={r['name']:r for r in adv.CONFIGS}
    epochs=40;log={};adv.block_mask=ORIGINAL_BLOCK
    if method in ['mask_only','metadata_only']:
        if method=='mask_only':features=d['observed'].reshape(len(d['x']),-1).astype(float)
        else:
            lookup={r['id']:r for r in json.loads((ROOT/'data/disfor/sample_manifest.json').read_text())}
            features=np.array([[lookup[i]['lon'],lookup[i]['lat'],lookup[i]['year'],lookup[i]['dataset']] for i in d['ids']])
        estimator=RandomForestClassifier(n_estimators=500,min_samples_leaf=4,max_features=.7,class_weight='balanced_subsample',random_state=seed,n_jobs=2)
        estimator.fit(features[labeled],d['y'][labeled]);p=estimator.predict_proba(features[test])[:,1]
        epochs=0
    else:
        chosen=method
        if method=='iid_ssl':chosen='ssl_transformer48';adv.block_mask=iid_mask
        if method=='step_matched':
            chosen='transformer48';epochs=math.ceil((60*math.ceil(len(train)/64)+40*math.ceil(len(labeled)/64))/math.ceil(len(labeled)/64))
        state,log=adv.fit(config[chosen],d,train,seed=seed,epochs=epochs,pre_epochs=60,labeled=labeled,early_stop=False)
        p=adv.state_probability(state,adv.view(d,test))
    row=dict(fold=fold,seed=seed,budget=budget,method=method,n_train=len(train),n_labeled=len(labeled),epochs=epochs,
             labeled_ids=d['ids'][labeled].tolist(),train_ids=d['ids'][train].tolist(),test_ids=d['ids'][test].tolist(),
             y=d['y'][test].tolist(),groups=d['groups'][test].tolist(),probabilities=p.tolist(),metrics=score(d['y'][test],p),
             seconds=time.time()-started,log=log)
    adv.write_json(dest,row)
    return dict(file=dest.name,macro_f1=row['metrics']['macro_f1'],seconds=row['seconds'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=3);args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    files=['scripts/train_paper.py','src/orman_ssl/advanced.py','src/orman_ssl/experiment.py','src/orman_ssl/inputs.py',
           'data/processed/real_series.npz','experiments/paper_v4/protocol.json']
    signature={name:adv.digest(ROOT/name) for name in files}
    lock=OUT/'signature.json'
    if lock.exists() and json.loads(lock.read_text())!=signature:raise ValueError('Protocol/code/data changed; do not mix cached fits')
    adv.write_json(lock,signature)
    d=dict(np.load(ROOT/'data/processed/real_series.npz',allow_pickle=False));splits=[]
    cv=StratifiedGroupKFold(5,shuffle=True,random_state=4192026)
    for fold,(train,test) in enumerate(cv.split(d['x'],d['y'],d['groups'])):
        if set(d['groups'][train])&set(d['groups'][test]):raise ValueError('Group leakage')
        if len(np.unique(d['y'][test]))!=2:raise ValueError('Inadequate fold support; do not search by model score')
        splits.append(dict(fold=fold,train_indices=train.tolist(),test_indices=test.tolist(),train_ids=d['ids'][train].tolist(),test_ids=d['ids'][test].tolist(),
                           test_class_counts=np.bincount(d['y'][test],minlength=2).tolist(),test_groups=np.unique(d['groups'][test]).tolist()))
    adv.write_json(OUT/'folds.json',splits)
    jobs=[(fold,seed,budget,method) for fold in range(5) for seed in [7,17,27] for budget in [.2,1.] for method in ['rf_leaf4','cnn64','transformer48','ssl_transformer48']]
    jobs += [(fold,seed,.2,method) for fold in range(5) for seed in [7,17,27] for method in ['iid_ssl','step_matched','mask_only','metadata_only']]
    adv.write_json(OUT/'jobs.json',[dict(fold=f,seed=s,budget=b,method=m) for f,s,b,m in jobs])
    print('Fixed jobs:',len(jobs),'workers:',args.workers,flush=True)
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(worker,job) for job in jobs]
        for i,future in enumerate(concurrent.futures.as_completed(futures),1):
            print(i,'/',len(jobs),json.dumps(future.result()),flush=True)
    adv.write_json(OUT/'completion.json',dict(status='complete',jobs=len(jobs),signature=signature))

if __name__=='__main__':main()
