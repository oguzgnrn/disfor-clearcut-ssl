"""Measure local end-to-end inference latency, including member loading."""
import json,sys,time,platform
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from orman_ssl.advanced import ensemble_predict,write_json
with np.load(ROOT/'data/processed/test_inference.npz',allow_pickle=False) as a:
    d={k:a[k] for k in a.files}
rows=[]
for n in [1,32,len(d['ids'])]:
    v={k:(x[:n] if x.ndim else x) for k,x in d.items()}
    timings=[]
    for _ in range(3):
        start=time.perf_counter();q=ensemble_predict(ROOT/'models/advanced_v3/bundle.json',v);timings.append(time.perf_counter()-start)
    rows.append(dict(samples=n,seconds=timings,median_seconds=float(np.median(timings)),samples_per_second=float(n/np.median(timings))))
write_json(ROOT/'experiments/advanced_v3/inference_benchmark.json',dict(platform=platform.platform(),device='cpu',torch_threads=2,
    includes='Model file hashing/loading, preprocessing and inference; does not include raw Parquet preparation',runs=rows))
print(json.dumps(rows,indent=2))
