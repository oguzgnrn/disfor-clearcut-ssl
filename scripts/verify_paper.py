"""Audit all cross-fit artifacts without refitting or selecting models."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from sklearn.metrics import f1_score,average_precision_score
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from analyze_paper import macro
OUT=ROOT/'experiments/paper_v4'
def check():
    complete=json.loads((OUT/'completion.json').read_text())
    for name,value in complete['signature'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value,name
    data=np.load(ROOT/'data/processed/real_series.npz');ids=data['ids'];lookup={v:i for i,v in enumerate(ids)}
    folds=json.loads((OUT/'folds.json').read_text());jobs=json.loads((OUT/'jobs.json').read_text())
    records=[json.loads(p.read_text()) for p in (OUT/'runs').glob('*.json')]
    assert len(records)==len(jobs)==180
    assert {(r['fold'],r['seed'],r['budget'],r['method']) for r in records}=={(r['fold'],r['seed'],r['budget'],r['method']) for r in jobs}
    pairs={}
    for r in records:
        f=folds[r['fold']];assert r['train_ids']==f['train_ids'] and r['test_ids']==f['test_ids']
        key=(r['fold'],r['seed'],r['budget']);labeled=r['labeled_ids']
        assert len(set(labeled))==len(labeled)==r['n_labeled']
        assert set(labeled)<=set(r['train_ids']) and not set(r['train_ids'])&set(r['test_ids'])
        if key in pairs:assert pairs[key]==labeled
        pairs[key]=labeled
        ix=[lookup[i] for i in r['test_ids']];y=data['y'][ix];p=np.asarray(r['probabilities'])
        assert np.array_equal(y,r['y']) and np.array_equal(data['groups'][ix],r['groups'])
        assert np.isfinite(p).all() and (p>=0).all() and (p<=1).all()
        assert abs(f1_score(y,p>=.5,average='macro')-r['metrics']['macro_f1'])<1e-12
        history=r['log'].get('history',[])
        if r['method'] not in ['mask_only','metadata_only','rf_leaf4']:
            assert len(history)==r['epochs'];assert all(v['validation_macro_f1'] is None for v in history)
        pre=r['log'].get('pretrain_loss',[])
        assert len(pre)==(60 if r['method'] in ['ssl_transformer48','iid_ssl'] else 0)
    oof=np.load(OUT/'oof_predictions.npz');analysis=json.loads((OUT/'analysis.json').read_text());assert np.array_equal(oof['ids'],ids)
    for s in analysis['summary']:
        probs=oof[f"{s['method']}_{s['budget']}"];assert probs.shape==(3,2213)
        scores=[]
        for j,seed in enumerate([7,17,27]):
            expected=np.full(2213,np.nan)
            for r in records:
                if (r['method'],r['budget'],r['seed'])==(s['method'],s['budget'],seed):
                    ix=[lookup[i] for i in r['test_ids']];assert np.isnan(expected[ix]).all();expected[ix]=r['probabilities']
            assert np.array_equal(probs[j],expected)
            scores.append(macro(data['y'],expected))
            assert abs(average_precision_score(data['y'],expected)-s['seed_results'][j]['pr_auc'])<1e-12
        assert abs(np.mean(scores)-s['macro_f1_mean'])<1e-12
    result=dict(status='passed',fits=180,oof_predictions=int(12*3*2213),checks=['frozen code/data/protocol SHA-256','exact declared jobs','fold identities','paired labeled subsets','training/test disjointness','prediction ranges and label alignment','fixed epochs and no validation selection','pretraining histories','complete OOF reconstruction','recomputed macro-F1 and average precision'])
    (OUT/'verification.json').write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':print(json.dumps(check(),indent=2))
