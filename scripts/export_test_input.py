from pathlib import Path
import numpy as np,json
root=Path(__file__).resolve().parents[1]
d=dict(np.load(root/'data/processed/real_series.npz',allow_pickle=False));ids=json.loads((root/'reports/real_experiment/selected_test_predictions.json').read_text())['ids']
lookup={v:i for i,v in enumerate(d['ids'])};ix=np.array([lookup[s] for s in ids]);v={k:d[k][ix] for k in ['x','observed','days','ids']};v['metadata']=d['metadata']
np.savez_compressed(root/'data/processed/test_inference.npz',**v)
