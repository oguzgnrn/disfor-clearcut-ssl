"""Post hoc support and error audit. Does not alter labels, fits or primary claims."""
import hashlib,json,sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from sklearn.metrics import f1_score,average_precision_score,confusion_matrix
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'experiments/paper_v4'
METHODS=['rf_leaf4','cnn64','transformer48','ssl_transformer48']

def subgroup_metrics(y,probabilities):
    y=np.asarray(y);p=np.asarray(probabilities)
    if p.shape!=(3,len(y)):raise ValueError('Expected paired seed probabilities')
    if not len(y):raise ValueError('Empty subgroup')
    counts=np.bincount(y,minlength=2);valid=bool(counts.min()>0)
    scores=[float(f1_score(y,row>=.5,average='macro',labels=[0,1])) for row in p] if valid else None
    ap=[float(average_precision_score(y,row)) for row in p] if valid else None
    return dict(n=len(y),class_counts=counts.tolist(),both_classes=valid,macro_f1_mean=None if scores is None else float(np.mean(scores)),average_precision_mean=None if ap is None else float(np.mean(ap)),confusion_matrices=[confusion_matrix(y,row>=.5,labels=[0,1]).tolist() for row in p],limited_positive_support=bool(counts[1]<10))

def fingerprint(x,mask,days):
    h=hashlib.sha256()
    for part in [np.where(mask,x,0).astype('<f4'),mask.astype('u1'),days.astype('<f4')]:h.update(part.tobytes())
    return h.hexdigest()

def main():
    d=np.load(ROOT/'data/processed/real_series.npz',allow_pickle=False);oof=np.load(OUT/'oof_predictions.npz',allow_pickle=False)
    manifest={r['id']:r for r in json.loads((ROOT/'data/disfor/sample_manifest.json').read_text())};meta=[manifest[i] for i in d['ids']]
    fold_id={i:f['fold'] for f in json.loads((OUT/'folds.json').read_text()) for i in f['test_ids']}
    duplicate=defaultdict(list)
    for i,identifier in enumerate(d['ids']):duplicate[fingerprint(d['x'][i],d['observed'][i],d['days'][i])].append(str(identifier))
    clusters=[v for v in duplicate.values() if len(v)>1];cross=[v for v in clusters if len({fold_id[i] for i in v})>1]
    if cross:raise ValueError('Identical feature trajectories cross outer folds: '+str(cross))
    events=defaultdict(list)
    for r in meta:
        if r['dataset'] in [1,3] and r['source_cluster'] is not None:events[(r['dataset'],r['source_cluster'])].append(r['id'])
    for ids in events.values():
        if len({fold_id[i] for i in ids})>1:raise ValueError('Source event crosses folds')
    groups=np.unique(d['groups']);positive_groups=np.unique(d['groups'][d['y']==1]);sizes=np.unique(d['groups'],return_counts=True)[1]
    strata=[]
    for field in ['dataset','year']:
        values=np.array([r[field] for r in meta])
        for value in np.unique(values):
            ix=values==value
            for budget in [.2,1.]:
                for method in METHODS:
                    strata.append(dict(field=field,value=int(value),budget=budget,method=method,**subgroup_metrics(d['y'][ix],oof[f'{method}_{budget}'][:,ix])))
    reviews=[]
    for i,r in enumerate(meta):
        predictions={}
        for method in METHODS:
            prob=oof[f'{method}_1.0'][:,i];wrong=int(np.sum((prob>=.5)!=d['y'][i]))
            predictions[method]=dict(wrong_seeds=wrong,probabilities=prob.tolist(),mean_probability=float(prob.mean()))
        if predictions['cnn64']['wrong_seeds']>=2 or predictions['ssl_transformer48']['wrong_seeds']>=2:
            reviews.append(dict(**r,outer_fold=fold_id[r['id']]+1,observed_months=int(d['observed'][i].any(-1).sum()),predictions=predictions,review_status='not reviewed; original label unchanged'))
    result=dict(status='passed',analysis_type='post hoc descriptive support audit; not a new benchmark or model-selection stage',locations=len(meta),groups=len(groups),positive_groups=len(positive_groups),largest_component=int(sizes.max()),median_component_size=float(np.median(sizes)),duplicate_feature_clusters=clusters,cross_fold_duplicate_clusters=cross,shared_event_keys_checked=len(events),strata=strata,review_candidates=len(reviews),limitations=['Subgroup results are descriptive; no subgroup-selected model or threshold','Subgroups with only one class have null macro-F1 and AP','Fewer than 10 positives is marked as limited support, not a formal inference cutoff','A persistent model error does not establish a label error; all original labels remain unchanged'])
    (OUT/'support_error_audit.json').write_text(json.dumps(result,indent=2));(OUT/'review_candidates.json').write_text(json.dumps(reviews,indent=2))
    geo={'type':'FeatureCollection','features':[dict(type='Feature',geometry=dict(type='Point',coordinates=[r['lon'],r['lat']]),properties={k:v for k,v in r.items() if k not in ['lon','lat']}) for r in reviews]}
    (OUT/'review_candidates.geojson').write_text(json.dumps(geo,indent=2))
    lines=['# Post hoc error and support audit','This is an additional descriptive audit performed after the fixed study. It changes no labels, trained models, thresholds or primary endpoints.',f"The cohort contains {len(groups)} spatial components, including {len(positive_groups)} with a clear-cut label. The largest component contains {sizes.max()} points. {len(clusters)} exact feature-trajectory duplicate clusters were found; none crosses outer folds. {len(events)} source-event keys were checked; none crosses folds.",f"The review list contains {len(reviews)} locations misclassified by at least two of three full-label CNN seeds or at least two of three full-label SSL seeds. These are review candidates, not corrected labels. Open `experiments/paper_v4/review_candidates.geojson` in QGIS; per-model probabilities and source metadata are retained.",'## Full-label CNN by source campaign and target year','| Stratum | N | Stable / cut | Macro-F1 | AP |','|---|---:|---:|---:|---:|']
    for r in strata:
        if r['method']=='cnn64' and r['budget']==1.:
            val=lambda k:'not defined' if r[k] is None else f'{r[k]:.4f}'
            lines.append(f"| {r['field']} {r['value']} | {r['n']} | {r['class_counts'][0]} / {r['class_counts'][1]} | {val('macro_f1_mean')} | {val('average_precision_mean')} |")
    lines += ['','All four primary methods at both label budgets are recorded in `support_error_audit.json`. The table uses the existing pooled out-of-fold predictions; it is not a leave-campaign-out or forward-time validation. Confidence intervals are not added to these post hoc subgroup summaries.','## Raw-data reproduction','`data_reproduction_audit.json` records an isolated rebuild from pinned original Parquet files and an exact comparison of every processed array and sample-provenance entry. The manifest checksum is recorded at final audit time; it was not part of the original pre-score training signature.']
    (ROOT/'paper/ERROR_AUDIT.md').write_text('\n\n'.join(lines).replace('\n\n|','\n|')+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['strata','duplicate_feature_clusters']},indent=2))
if __name__=='__main__':main()
