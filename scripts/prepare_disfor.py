"""Versioned real-data adapter: retrospective 24-month forest condition classification."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
from shapely import from_wkb
from sklearn.neighbors import BallTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
from orman_ssl.experiment import validate,split_groups
src=root/'data/disfor'
s=pd.read_parquet(src/'samples.parquet');l=pd.read_parquet(src/'labels.parquet');p=pd.read_parquet(src/'pixel_data.parquet')
p['date']=pd.to_datetime(p['timestamps'],utc=True)
for k in ['start','end']: l[k]=pd.to_datetime(l[k])
bands=['B02','B03','B04','B05','B06','B07','B08','B8A','B11','B12']
label_groups={int(k):v for k,v in l.groupby('sample_id')};pixel_groups={int(k):v for k,v in p.groupby('sample_id')}
rows=[];xs=[];masks=[];times=[]
rejected={}
def reject(k): rejected[k]=rejected.get(k,0)+1
for _,sample in s.iterrows():
 sid=int(sample.sample_id)
 if sample.confidence!='high':reject('not_high_confidence');continue
 ls=label_groups.get(sid)
 if ls is None:reject('no_labels');continue
 candidates=[]
 # A fixed annual window avoids feeding annotated event day as a model feature.
 for year in range(2018,2024):
  start=pd.Timestamp(f'{year-1}-01-01',tz='UTC');mid=pd.Timestamp(f'{year}-01-01',tz='UTC');end=pd.Timestamp(f'{year+1}-01-01',tz='UTC')
  events=ls[(ls.label>=200)&(ls.start>=start)&(ls.start<end)]
  target=events[(events.start>=mid)&events.label.isin([211,242])]
  stable=ls[(ls.label==110)&(ls.start<=start)&(ls.end>=end-pd.Timedelta(seconds=1))]
  if len(target)==1 and len(events)==1:
   # Require interpreted intact forest throughout the preceding calendar year.
   prior=ls[(ls.label==110)&(ls.start<=start)&(ls.end>=mid-pd.Timedelta(seconds=1))]
   if len(prior): candidates.append((year,1 if int(target.iloc[0].label)==211 else 2))
  elif len(stable):candidates.append((year,0))
 events=[v for v in candidates if v[1]>0]
 if events:year,label=events[0]
 elif candidates:
  ordered=sorted(candidates,key=lambda v:((v[0]-2018-sid%6)%6));year,label=ordered[0]
 else:reject('no_unambiguous_two_year_window');continue
 start=pd.Timestamp(f'{year-1}-01-01',tz='UTC');end=pd.Timestamp(f'{year+1}-01-01',tz='UTC')
 obs=pixel_groups[sid];obs=obs[(obs.date>=start)&(obs.date<end)&obs.clear&obs.SCL.isin([4,5])].copy()
 obs['slot']=(obs.date.dt.year-(year-1))*12+obs.date.dt.month-1
 # Source supplies DN values. Keep units as provided; no undocumented reflectance offset.
 monthly=obs.groupby('slot')[bands].median().reindex(range(24))
 x=monthly.to_numpy(dtype='float32');mask=np.isfinite(x)
 if (mask.any(1)[:12].sum()<6) or (mask.any(1)[12:].sum()<6):reject('insufficient_clear_months');continue
 dates=pd.date_range(start,periods=24,freq='MS')+pd.Timedelta(days=14)
 days=((dates-start).total_seconds()/86400).to_numpy(dtype='float32')
 point=from_wkb(sample.geometry)
 rows.append(dict(id=f'disfor-{sid}-{year}',sample_id=sid,year=year,label=label,lon=point.x,lat=point.y,dataset=int(sample.dataset),
  source=str(sample.source),source_description=str(sample.source_description),confidence=str(sample.confidence),
  source_cluster=None if pd.isna(sample.cluster_id) else str(sample.cluster_id),cluster_description=None if pd.isna(sample.cluster_description) else str(sample.cluster_description)))
 xs.append(x);masks.append(mask);times.append(days)
# Freeze a supported primary task before inspecting model scores.
keep=[i for i,r in enumerate(rows) if r['label']!=2]
rejected['wildfire_excluded_from_primary_task']=len(rows)-len(keep)
rows=[rows[i] for i in keep];xs=[xs[i] for i in keep];masks=[masks[i] for i in keep];times=[times[i] for i in keep]
# Union all points within 5 km, and all samples of the same damage polygon/storm.
# Sampling strata are NOT events and are therefore not collapsed across continents.
n=len(rows);parent=list(range(n))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i

def union(i,j):
 a,b=find(i),find(j)
 if a!=b:parent[b]=a
coords=np.deg2rad([[r['lat'],r['lon']] for r in rows]);tree=BallTree(coords,metric='haversine')
for i,neighbors in enumerate(tree.query_radius(coords,r=5/6371.0088)):
 for j in neighbors:union(i,int(j))
clusters={}
for i,r in enumerate(rows):
 if r['source_cluster'] is not None and r['dataset'] in [1,3]:
  key=(r['dataset'],r['source_cluster'])
  if key in clusters:union(i,clusters[key])
  else:clusters[key]=i
roots=[find(i) for i in range(n)];mapping={k:i for i,k in enumerate(sorted(set(roots)))}
groups=np.array([mapping[k] for k in roots]);y=np.array([r['label'] for r in rows],dtype='int64')
meta=dict(kind='real',name='DISFOR retrospective clear-cut pilot',classes=['undisturbed_forest','clear_cut'],channels=bands,
 source='https://huggingface.co/datasets/JR-DIGITAL/DISFOR/tree/'+json.loads((src/'downloads.json').read_text())['revision'],
 label_provenance='DISFOR high-confidence human-interpreted segments; auxiliary sources in sample manifest; not newly collected field ground truth',
 group_definition='Connected components within 5 km plus same source damage polygon/storm; all years of a point kept together. Sampling strata excluded from event union.',
 temporal_alignment='Two full calendar years; event must be in second year, intact forest in preceding year; negatives intact entire window; no event dates in features',
 units='Source-provided DN, no added offset; per-channel standardization fitted on training only',
 task='Retrospective classification of selected 24-month windows, not early warning or continuous map validation',license='EUPL-1.2',
 monthly_quality='Median of source clear AND SCL 4/5; at least 6 valid months in each year. Missing months remain missing.')
d=dict(x=np.stack(xs),observed=np.stack(masks),days=np.stack(times),y=y,groups=groups,ids=np.array([r['id'] for r in rows]),metadata=json.dumps(meta))
validate(d);tr,va,te=split_groups(groups,y)
split_names={int(ix):name for name,part in zip(['train','validation','test'],[tr,va,te]) for ix in part}
for i,r in enumerate(rows):r['group']=int(groups[i]);r['split']=split_names[i]
out=root/'data/processed/real_series.npz';np.savez_compressed(out,**d)
(root/'data/disfor/sample_manifest.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
summary=dict(n=n,groups=len(set(groups)),class_counts=np.bincount(y).tolist(),rejected=rejected,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
 split={name:dict(n=len(ix),groups=len(set(groups[ix])),class_counts=np.bincount(y[ix],minlength=2).tolist()) for name,ix in zip(['train','validation','test'],[tr,va,te])},metadata=meta)
# Audit the actual nearest cross-split distances rather than assuming group IDs suffice.
for a,aa,b,bb in [('train',tr,'test',te),('train',tr,'validation',va),('validation',va,'test',te)]:
 dist=BallTree(coords[aa],metric='haversine').query(coords[bb],k=1)[0].min()*6371.0088
 summary.setdefault('minimum_cross_split_distance_km',{})[a+'_'+b]=float(dist)
 assert dist>5-1e-6
(root/'reports/disfor_preparation.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False));print(json.dumps(summary,indent=2,ensure_ascii=False))
