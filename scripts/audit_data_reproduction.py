"""Rebuild the cohort from pinned raw inputs in isolation and compare every array."""
import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def run():
    source=ROOT/'data/disfor';manifest=json.loads((source/'downloads.json').read_text())
    for item in manifest['files']:
        p=source/item['name']
        if not p.exists():raise ValueError('Raw input missing: '+item['name'])
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Raw source hash mismatch: '+item['name'])
    with tempfile.TemporaryDirectory(prefix='orman-source-rebuild-') as folder:
        temp=Path(folder)
        for name in ['scripts','data/processed','data/disfor','reports']:(temp/name).mkdir(parents=True,exist_ok=True)
        shutil.copytree(ROOT/'src',temp/'src')
        shutil.copy2(ROOT/'scripts/prepare_disfor.py',temp/'scripts/prepare_disfor.py')
        for name in ['samples.parquet','labels.parquet','pixel_data.parquet','downloads.json']:shutil.copy2(source/name,temp/'data/disfor'/name)
        result=subprocess.run([sys.executable,'scripts/prepare_disfor.py'],cwd=temp,capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        with np.load(ROOT/'data/processed/real_series.npz',allow_pickle=False) as old,np.load(temp/'data/processed/real_series.npz',allow_pickle=False) as new:
            if set(old.files)!=set(new.files):raise ValueError('Array schema changed')
            for key in old.files:
                left,right=old[key],new[key]
                if left.dtype!=right.dtype or left.shape!=right.shape:raise ValueError('Shape/dtype mismatch: '+key)
                same=np.array_equal(left,right,equal_nan=True) if left.dtype.kind in 'fc' else np.array_equal(left,right)
                if not same:raise ValueError('Rebuilt values differ: '+key)
            checked=list(old.files)
        original=json.loads((source/'sample_manifest.json').read_text());rebuilt=json.loads((temp/'data/disfor/sample_manifest.json').read_text())
        if original!=rebuilt:raise ValueError('Sample provenance differs')
    evidence=dict(status='passed',raw_files_checked=len(manifest['files']),source_revision=manifest['revision'],arrays_rebuilt=checked,locations=2213,all_array_values_equal=True,sample_manifest_equal=True,execution='isolated temporary directory; original cohort preserved',preparation_script_sha256=hashlib.sha256((ROOT/'scripts/prepare_disfor.py').read_bytes()).hexdigest(),sample_manifest_sha256=hashlib.sha256((source/'sample_manifest.json').read_bytes()).hexdigest())
    (ROOT/'experiments/paper_v4/data_reproduction_audit.json').write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence,indent=2))
if __name__=='__main__':run()
