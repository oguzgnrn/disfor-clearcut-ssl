"""Spatial model selection, weighted temporal learning and block-masked SSL."""
import argparse
import copy
import hashlib
import json
import math
import time
from pathlib import Path

import joblib
import numpy as np
import torch
from torch import nn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.linear_model import LogisticRegression
from .experiment import normalize, rf_features, subset
from .inputs import validate_input

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'experiments/advanced_v3'
MODEL = ROOT/'models/advanced_v3'
CONFIGS = [
    dict(name='rf_leaf1',kind='rf',leaf=1),
    dict(name='rf_leaf4',kind='rf',leaf=4),
    dict(name='cnn32',kind='cnn',width=32,dropout=.15,lr=.001),
    dict(name='cnn64',kind='cnn',width=64,dropout=.2,lr=.001),
    dict(name='transformer48',kind='transformer',width=48,dropout=.15,lr=.0005),
    dict(name='ssl_transformer48',kind='transformer',width=48,dropout=.15,lr=.0005,ssl=True),
]
SEEDS = [7,17,27,37,47]


def write_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False))
    temporary.replace(path)


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def context():
    d=dict(np.load(ROOT/'data/processed/real_series.npz',allow_pickle=False))
    validate_input(d)
    split=json.loads((ROOT/'reports/real_experiment/split.json').read_text())
    lookup={s:i for i,s in enumerate(d['ids'])}
    parts={k:np.array([lookup[s] for s in split[k]['ids']]) for k in ['train','validation','test']}
    for a,b in [('train','validation'),('train','test'),('validation','test')]:
        if set(d['groups'][parts[a]]) & set(d['groups'][parts[b]]): raise ValueError('Outer group overlap')
    return d,parts


class ResidualBlock(nn.Module):
    def __init__(self,width,dilation,dropout):
        super().__init__()
        self.net=nn.Sequential(nn.Conv1d(width,width,3,padding=dilation,dilation=dilation),
            nn.GroupNorm(4,width),nn.GELU(),nn.Dropout(dropout),
            nn.Conv1d(width,width,3,padding=dilation,dilation=dilation),nn.GroupNorm(4,width),nn.GELU())
    def forward(self,x): return x+self.net(x)


class TemporalNet(nn.Module):
    def __init__(self,config,channels=10):
        super().__init__();self.kind=config['kind'];width=config['width']
        self.embed=nn.Linear(channels*2+3,width)
        if self.kind=='cnn':
            self.encoder=nn.Sequential(*[ResidualBlock(width,v,config['dropout']) for v in [1,2,4]])
        else:
            layer=nn.TransformerEncoderLayer(width,4,width*3,dropout=config['dropout'],activation='gelu',batch_first=True,norm_first=False)
            self.encoder=nn.TransformerEncoder(layer,2,enable_nested_tensor=False)
        self.classifier=nn.Sequential(nn.LayerNorm(width),nn.Dropout(config['dropout']),nn.Linear(width,2))
        self.reconstruct=nn.Linear(width,channels)
    def forward(self,x,mask,days):
        observed=mask.any(-1)
        time_features=torch.stack([days/730,torch.sin(days*2*math.pi/365.25),torch.cos(days*2*math.pi/365.25)],-1)
        # masked_fill avoids NaN * 0 contaminating the network.
        h=self.embed(torch.cat([x.masked_fill(~mask,0),mask.float(),time_features],-1))
        if self.kind=='cnn':h=self.encoder(h.transpose(1,2)).transpose(1,2)
        else:
            padding=~observed.clone()
            padding[~observed.any(1),0]=False
            h=self.encoder(h,src_key_padding_mask=padding)
        pooled=(h*observed.unsqueeze(-1)).sum(1)/observed.sum(1).clamp_min(1).unsqueeze(-1)
        return self.classifier(pooled),self.reconstruct(h)


def block_mask(mask):
    n,t,c=mask.shape
    hidden=torch.zeros_like(mask)
    for i in range(n):
        length=int(torch.randint(2,7,()).item());start=int(torch.randint(0,t-length+1,()).item())
        hidden[i,start:start+length]=True
        bands=torch.randperm(c)[:2];hidden[i,:,bands]=True
    hidden &= mask
    for i in range(n):
        observed=torch.nonzero(mask[i],as_tuple=False)
        if len(observed)>1 and (mask[i]&~hidden[i]).sum()==0:
            j,k=observed[0];hidden[i,j,k]=False
        if not hidden[i].any() and len(observed)>1:
            j,k=observed[-1];hidden[i,j,k]=True
    return hidden


def augment(mask):
    result=mask & ~(torch.rand(mask.shape[:2])<.1).unsqueeze(-1)
    empty=~result.any((1,2))
    result[empty]=mask[empty]
    return result


def probabilities(model,x,m,days):
    model.eval();chunks=[]
    with torch.no_grad():
        for start in range(0,len(x),128):
            chunks.append(model(x[start:start+128],m[start:start+128],days[start:start+128])[0].softmax(-1)[:,1].numpy())
    return np.concatenate(chunks)


def fit(config,d,train,val=None,seed=7,epochs=80,pre_epochs=60,labeled=None,early_stop=True):
    torch.set_num_threads(2);torch.manual_seed(seed);np.random.seed(seed)
    z,mean,std=normalize(d['x'],d['observed'],train)
    labeled=train if labeled is None else labeled
    y=d['y'];counts=np.bincount(y[labeled],minlength=2)
    if not counts.all():raise ValueError('Training labels need both classes')
    if config['kind']=='rf':
        model=RandomForestClassifier(n_estimators=500,min_samples_leaf=config['leaf'],max_features=.7,
                                     class_weight='balanced_subsample',n_jobs=2,random_state=seed)
        features=rf_features(z,d['observed']);model.fit(features[labeled],y[labeled])
        score=None if val is None else float(f1_score(y[val],model.predict(features[val]),average='macro'))
        return dict(model=model,mean=mean.tolist(),std=std.tolist(),config=config,seed=seed,epochs=0),dict(best_epoch=0,validation_macro_f1=score,history=[])
    x=torch.tensor(z);m=torch.tensor(d['observed']);days=torch.tensor(d['days']);labels=torch.tensor(y)
    model=TemporalNet(config)
    initial=copy.deepcopy(model.state_dict())
    prehistory=[]
    if config.get('ssl'):
        optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.01)
        for epoch in range(pre_epochs):
            model.train();losses=[]
            for ids in torch.tensor(train)[torch.randperm(len(train))].split(64):
                hidden=block_mask(m[ids]);visible=m[ids]&~hidden
                _,reconstructed=model(x[ids].masked_fill(hidden,0),visible,days[ids])
                loss=nn.functional.smooth_l1_loss(reconstructed[hidden],x[ids][hidden])
                optimizer.zero_grad();loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step();losses.append(loss.item())
            prehistory.append(float(np.mean(losses)))
    # The classifier starts identically for SSL and supervised comparisons.
    state=model.state_dict()
    for name in state:
        if name.startswith('classifier.'):state[name]=initial[name]
    model.load_state_dict(state)
    torch.manual_seed(seed+1000)
    optimizer=torch.optim.AdamW(model.parameters(),lr=config['lr'],weight_decay=.01)
    weights=torch.tensor(len(labeled)/(2*counts),dtype=torch.float32)
    best_score=-1;best_state=None;best_epoch=epochs;history=[];stale=0
    for epoch in range(epochs):
        model.train();losses=[]
        for ids in torch.tensor(labeled)[torch.randperm(len(labeled))].split(64):
            visible=augment(m[ids]);logits,_=model(x[ids].masked_fill(~visible,0),visible,days[ids])
            loss=nn.functional.cross_entropy(logits,labels[ids],weight=weights,label_smoothing=.02)
            optimizer.zero_grad();loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step();losses.append(loss.item())
        score=None
        if val is not None:
            p=probabilities(model,x[val],m[val],days[val]);score=float(f1_score(y[val],p>=.5,average='macro',zero_division=0))
            if score>best_score+1e-8:
                best_score=score;best_state=copy.deepcopy(model.state_dict());best_epoch=epoch+1;stale=0
            else:stale+=1
        history.append(dict(epoch=epoch+1,loss=float(np.mean(losses)),validation_macro_f1=score))
        if early_stop and val is not None and epoch+1>=20 and stale>=12:break
    if early_stop and best_state is not None:model.load_state_dict(best_state)
    state=dict(model=model.state_dict(),mean=mean.tolist(),std=std.tolist(),config=config,seed=seed,epochs=best_epoch if early_stop else epochs)
    return state,dict(best_epoch=state['epochs'],validation_macro_f1=best_score if val is not None else None,history=history,pretrain_loss=prehistory)


def save_state(path,state):
    if state['config']['kind']=='rf':joblib.dump(state,path)
    else:torch.save(state,path)


def load_state(path):
    return joblib.load(path) if str(path).endswith('.joblib') else torch.load(path,map_location='cpu',weights_only=True)


def state_probability(state,d):
    torch.set_num_threads(2)
    z=np.where(d['observed'],(d['x']-np.array(state['mean']))/np.array(state['std']),0).astype('float32')
    if state['config']['kind']=='rf':return state['model'].predict_proba(rf_features(z,d['observed']))[:,1]
    net=TemporalNet(state['config']);net.load_state_dict(state['model'])
    return probabilities(net,torch.tensor(z),torch.tensor(d['observed']),torch.tensor(d['days'],dtype=torch.float32))


def view(d,idx):
    return {k:(v[idx] if isinstance(v,np.ndarray) and v.ndim and len(v)==len(d['x']) else v) for k,v in d.items()}


def cross_validate():
    d,parts=context();train=parts['train'];groups=d['groups'];y=d['y']
    cv=StratifiedGroupKFold(4,shuffle=True,random_state=92026)
    folds=[(train[a],train[b]) for a,b in cv.split(train,y[train],groups[train])]
    manifest=[]
    for a,b in folds:
        if set(groups[a])&set(groups[b]) or len(np.unique(y[b]))!=2:raise ValueError('Invalid spatial CV')
        manifest.append(dict(train_ids=d['ids'][a].tolist(),validation_ids=d['ids'][b].tolist(),validation_counts=np.bincount(y[b],minlength=2).tolist()))
    write_json(OUT/'folds.json',manifest)
    rows=[]
    for config in CONFIGS:
        for fold,(a,b) in enumerate(folds):
            path=OUT/'cv'/f'{config["name"]}_{fold}.json'
            if path.exists():row=json.loads(path.read_text())
            else:
                start=time.time();state,log=fit(config,d,a,b)
                p=state_probability(state,view(d,b))
                row=dict(config=config,fold=fold,macro_f1=float(f1_score(y[b],p>=.5,average='macro')),best_epoch=log['best_epoch'],
                         seconds=time.time()-start,validation_ids=d['ids'][b].tolist(),probabilities=p.tolist(),log=log)
                write_json(path,row)
            rows.append(row);print('CV',config['name'],fold,round(row['macro_f1'],4),'epoch',row['best_epoch'],flush=True)
    ranking=[]
    for config in CONFIGS:
        group=[r for r in rows if r['config']['name']==config['name']]
        ranking.append(dict(config=config,mean_macro_f1=float(np.mean([r['macro_f1'] for r in group])),std=float(np.std([r['macro_f1'] for r in group],ddof=1)),
                            final_epochs=max(20,int(np.median([r['best_epoch'] for r in group])))))
    ranking.sort(key=lambda r:(-r['mean_macro_f1'],r['config']['name']))
    write_json(OUT/'selection.json',dict(ranking=ranking,selected=ranking[:2],criterion='Mean training-only spatial CV macro-F1; no test selection'))


def sigmoid(x):return 1/(1+np.exp(-np.clip(x,-50,50)))
def logit(p):p=np.clip(p,1e-6,1-1e-6);return np.log(p/(1-p))


def train_final():
    d,parts=context();selection=json.loads((OUT/'selection.json').read_text());members=[];valprob=[]
    for item in selection['selected']:
        config=item['config']
        for seed in SEEDS:
            suffix='.joblib' if config['kind']=='rf' else '.pt'
            path=MODEL/f'{config["name"]}_{seed}{suffix}'
            if path.exists():state=load_state(path)
            else:
                state,log=fit(config,d,parts['train'],seed=seed,epochs=item['final_epochs'],early_stop=False)
                save_state(path,state);write_json(OUT/'final_training'/f'{config["name"]}_{seed}.json',log)
            valprob.append(state_probability(state,view(d,parts['validation'])))
            members.append(dict(path=path.name,sha256=digest(path),config=config,seed=seed,epochs=item['final_epochs']))
            print('FINAL member',path.name,flush=True)
    p=np.mean(valprob,axis=0);y=d['y'][parts['validation']]
    calibrator=LogisticRegression(C=1,solver='lbfgs',random_state=7).fit(logit(p)[:,None],y)
    slope=float(calibrator.coef_[0,0]);intercept=float(calibrator.intercept_[0])
    calibrated=sigmoid(slope*logit(p)+intercept)
    thresholds=np.round(np.arange(.10,.901,.02),2)
    threshold=min(thresholds,key=lambda t:(-f1_score(y,calibrated>=t,average='macro'),abs(t-.5)))
    bundle=dict(version='advanced_v3',members=members,calibration=dict(slope=slope,intercept=intercept),threshold=float(threshold),
                channels=json.loads(str(d['metadata']))['channels'],classes=['undisturbed_forest','clear_cut'],
                metadata=json.loads(str(d['metadata'])),protocol_sha256=digest(OUT/'protocol.json'),
                calibration_ids=d['ids'][parts['validation']].tolist(),training_ids=d['ids'][parts['train']].tolist(),
                test_status='Previously examined benchmark; not external field validation')
    write_json(MODEL/'bundle.json',bundle)
    write_json(OUT/'calibration.json',dict(ids=d['ids'][parts['validation']].tolist(),raw_probabilities=p.tolist(),calibrated_probabilities=calibrated.tolist(),
                                          threshold=float(threshold),apparent_macro_f1=float(f1_score(y,calibrated>=threshold,average='macro')),note='Fitted development scores, not independent estimates'))


def ensemble_predict(bundle_path,data):
    validate_input(data);bundle_path=Path(bundle_path);bundle=json.loads(bundle_path.read_text());preds=[]
    for member in bundle['members']:
        path=bundle_path.parent/member['path']
        if digest(path)!=member['sha256']:raise ValueError('Model member hash mismatch: '+member['path'])
        preds.append(state_probability(load_state(path),data))
    values=np.stack(preds);raw=values.mean(0);cal=bundle['calibration']
    p=sigmoid(cal['slope']*logit(raw)+cal['intercept']);m=data['observed'].any(-1)
    eligible=(m[:,:12].sum(1)>=6)&(m[:,12:].sum(1)>=6)
    return dict(ids=data['ids'].tolist(),predictions=(p>=bundle['threshold']).astype(int).tolist(),
                probabilities=np.stack([1-p,p],axis=1).tolist(),raw_probabilities=raw.tolist(),member_std=values.std(0).tolist(),
                quality_eligible=eligible.tolist(),classes=bundle['classes'],threshold=bundle['threshold'],
                note='Calibrated on development geography only. Member spread is disagreement, not an uncertainty interval. Low-quality samples are flagged, not silently treated as reliable.')


def low_labels():
    d,parts=context();rows=[]
    for fraction in [.05,.1,.2]:
        for seed in [7,17,27]:
            labeled=subset(d['y'],parts['train'],fraction,seed)
            for config in CONFIGS[-2:]:
                dest=OUT/'low_labels'/f'{config["name"]}_{fraction}_{seed}.json'
                if dest.exists():rows.append(json.loads(dest.read_text()));continue
                state,log=fit(config,d,parts['train'],seed=seed,epochs=40,labeled=labeled,early_stop=False)
                # Save development outputs only; test evaluation happens in the separate evaluation stage.
                path=OUT/'low_labels'/f'{config["name"]}_{fraction}_{seed}.pt';path.parent.mkdir(exist_ok=True,parents=True);save_state(path,state)
                row=dict(config=config,seed=seed,fraction=fraction,labeled_ids=d['ids'][labeled].tolist(),checkpoint=str(path.relative_to(ROOT)),log=log)
                write_json(dest,row);rows.append(row);print('LOW LABEL',config['name'],fraction,seed,flush=True)
    write_json(OUT/'low_label_training.json',rows)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['cv','final','low-label','all'],default='all');args=parser.parse_args()
    OUT.mkdir(exist_ok=True,parents=True);MODEL.mkdir(exist_ok=True,parents=True)
    signature=dict(data=digest(ROOT/'data/processed/real_series.npz'),code=digest(__file__),protocol=digest(OUT/'protocol.json'))
    lock=OUT/'training_signature.json'
    if lock.exists() and json.loads(lock.read_text())!=signature:raise ValueError('Training inputs/code changed; use a fresh experiment version instead of mixing cached runs')
    write_json(lock,signature)
    if args.stage in ['cv','all']:cross_validate()
    if args.stage in ['final','all']:train_final()
    if args.stage in ['low-label','all']:low_labels()

if __name__=='__main__':main()
