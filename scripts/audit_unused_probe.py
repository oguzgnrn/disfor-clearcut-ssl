"""Audit predeclared unused-point temporal windows before inspecting predictions."""
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
from shapely import from_wkb
from sklearn.neighbors import BallTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from orman_ssl.inputs import prepare_observations
from orman_ssl.advanced import write_json
OUT=ROOT/'experiments/paper_v4'
s=pd.read_parquet(ROOT/'data/disfor/samples.parquet');labels=pd.read_parquet(ROOT/'data/disfor/labels.parquet');pixels=pd.read_parquet(ROOT/'data/disfor/pixel_data.parquet')
labels['start']=pd.to_datetime(labels.start,utc=True);labels['end']=pd.to_datetime(labels.end,utc=True)
previous=json.loads((ROOT/'data/disfor/sample_manifest.json').read_text());used={r['sample_id'] for r in previous}
events={(r['dataset'],r['source_cluster']) for r in previous if r['dataset'] in [1,3] and r['source_cluster'] is not None}
coords=np.deg2rad([[r['lat'],r['lon']] for r in previous]);tree=BallTree(coords,metric='haversine')
groups={int(k):v for k,v in labels.groupby('sample_id')};candidates=[];reasons={}
def reject(k):reasons[k]=reasons.get(k,0)+1
for _,r in s.iterrows():
    sid=int(r.sample_id)
    if r.confidence!='high':reject('not_high_confidence');continue
    if sid in used:reject('previously_used_point');continue
    cluster=None if pd.isna(r.cluster_id) else str(r.cluster_id)
    if (int(r.dataset),cluster) in events:reject('shared_source_event');continue
    point=from_wkb(r.geometry);distance=float(tree.query(np.deg2rad([[point.y,point.x]]),k=1)[0][0,0]*6371.0088)
    if distance<=5:reject('within_five_km_of_used_point');continue
    ls=groups[sid];options=[]
    for year in [2017,2024]:
        start=pd.Timestamp(f'{year-1}-01-01',tz='UTC');mid=pd.Timestamp(f'{year}-01-01',tz='UTC');end=pd.Timestamp(f'{year+1}-01-01',tz='UTC')
        all_events=ls[(ls.label>=200)&(ls.start>=start)&(ls.start<end)]
        event=all_events[(all_events.label==211)&(all_events.start>=mid)]
        prior=ls[(ls.label==110)&(ls.start<=start)&(ls.end>=mid-pd.Timedelta(seconds=1))]
        stable=ls[(ls.label==110)&(ls.start<=start)&(ls.end>=end-pd.Timedelta(seconds=1))]
        if len(event)==1 and len(all_events)==1 and len(prior):options.append((year,1))
        elif len(stable) and len(all_events)==0:options.append((year,0))
    if not options:reject('no_eligible_2017_or_2024_window');continue
    options.sort(key=lambda v:(-v[1],v[0]));year,label=options[0]
    w=dict(id=f'probe-{sid}-{year}',sample_id=sid,target_year=year,lon=point.x,lat=point.y,label=label,dataset=int(r.dataset),distance_km=distance)
    try:
        data,detail=prepare_observations(pixels[pixels.sample_id==sid],[w],'DISFOR unused-point temporal audit')
    except ValueError:reject('no_valid_observations');continue
    if not detail[0]['quality_eligible']:reject('insufficient_monthly_support');continue
    candidates.append(w)
counts=[sum(r['label']==i for r in candidates) for i in [0,1]]
# A support audit is informative even when it cannot sustain an accuracy estimate.
result=dict(status='support_audit_only',candidates=len(candidates),class_counts=counts,rejections=reasons,
            minimum_distance_km=min([r['distance_km'] for r in candidates],default=None),windows=candidates,
            rule='Unused high-confidence points only; 2017/2024; >5 km from every previously used point; no shared event',
            limitation='Same-source temporal probe, not independent external data. No model scores computed by this audit.')
write_json(OUT/'unused_probe_audit.json',result);print(json.dumps({k:v for k,v in result.items() if k!='windows'},indent=2))
