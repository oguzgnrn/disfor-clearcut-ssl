"""Fetch the pinned public DISFOR tables; no accounts, no image tarballs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,requests
ROOT=Path(__file__).resolve().parents[1]
REVISION='2562332e35c94c2339aeb341ffaed2a99faae7d6'
FILES=['README.md','classes.json','samples.parquet','labels.parquet','pixel_data.parquet','train_ids.json','val_ids.json']
p=ROOT/'data/disfor';p.mkdir(parents=True,exist_ok=True)
def get(name):
 r=requests.get(f'https://huggingface.co/datasets/JR-DIGITAL/DISFOR/resolve/{REVISION}/{name}',timeout=240);r.raise_for_status()
 target=p/name;tmp=target.with_suffix(target.suffix+'.part');tmp.write_bytes(r.content);tmp.replace(target)
 return dict(name=name,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest())
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=3) as pool: rows=list(pool.map(get,FILES))
 (p/'downloads.json').write_text(json.dumps(dict(revision=REVISION,files=rows),indent=2))
 print('Pinned DISFOR data downloaded and hashed.')
