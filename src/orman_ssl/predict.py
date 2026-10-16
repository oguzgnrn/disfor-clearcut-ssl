"""Inference for locally trained checkpoints. Never load untrusted joblib models."""
import argparse,json
from pathlib import Path
import numpy as np
import torch,joblib
from .experiment import TemporalModel,rf_features
from .inputs import validate_input

def predict(checkpoint,data):
 d=dict(np.load(data,allow_pickle=False)) if isinstance(data,(str,Path)) else data
 validate_input(d)
 x=d['x'];m=d['observed'];days=d['days']
 meta=json.loads(str(d['metadata']))
 checkpoint=Path(checkpoint)
 if checkpoint.suffix=='.joblib': saved=joblib.load(checkpoint)
 else:saved=torch.load(checkpoint,map_location='cpu',weights_only=True)
 if meta['channels']!=saved['metadata']['channels']:raise ValueError('Channel order differs from training')
 if x.shape[1]!=saved.get('timesteps',24):raise ValueError('Expected 24 monthly timesteps')
 z=np.where(m,(x-np.array(saved['mean']))/np.array(saved['std']),0).astype('float32')
 if checkpoint.suffix=='.joblib':probs=saved['model'].predict_proba(rf_features(z,m))
 else:
  torch.set_num_threads(2)
  model=TemporalModel(saved['channels'],saved['classes']);model.load_state_dict(saved['model']);model.eval();parts=[]
  with torch.no_grad():
   for start in range(0,len(x),128):
    ix=slice(start,start+128);logits=model(torch.tensor(z[ix]),torch.tensor(m[ix]),torch.tensor(days[ix],dtype=torch.float32))[0];parts.append(logits.softmax(-1).numpy())
  probs=np.concatenate(parts)
 eligible=(m.any(-1)[:,:12].sum(1)>=6)&(m.any(-1)[:,12:].sum(1)>=6)
 return dict(ids=d['ids'].tolist(),predictions=probs.argmax(1).tolist(),probabilities=probs.tolist(),quality_eligible=eligible.tolist(),classes=saved['metadata']['classes'],
  note='Model scores are not calibrated certainty. Domain: DISFOR 24-month retrospective clear-cut pilot.')

def main():
 p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--data',required=True);p.add_argument('--out',required=True);a=p.parse_args()

 try: result=predict(a.checkpoint,a.data)
 except (ValueError,KeyError) as exc: p.error(str(exc))
 Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(result,indent=2));print('Predicted',len(result['ids']),'samples')
if __name__=='__main__':main()
