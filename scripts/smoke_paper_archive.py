"""Extract the actual delivery, rerun one neural fit and check identical predictions."""
import json,os,subprocess,sys,tempfile,zipfile,hashlib
from pathlib import Path
import numpy as np
from verify_package import verify
ROOT=Path(__file__).resolve().parents[1]
archive=ROOT/'output/Orman_SSL_Paper_Paketi.zip';verify(archive)
with tempfile.TemporaryDirectory(prefix='orman-paper-') as temporary:
    with zipfile.ZipFile(archive) as z:z.extractall(temporary)
    extracted=Path(temporary)/'Orman_SSL'
    target=extracted/'experiments/paper_v4/runs/ssl_transformer48_f0_s7_b0.2.json'
    original=json.loads(target.read_text());target.unlink()
    completed=subprocess.run([sys.executable,'scripts/train_paper.py','--workers','1'],cwd=extracted,capture_output=True,text=True)
    if completed.returncode:raise RuntimeError(completed.stdout+completed.stderr)
    repeated=json.loads(target.read_text());error=float(np.max(np.abs(np.array(original['probabilities'])-repeated['probabilities'])))
    assert error<1e-7,error
    tested=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_paper.py','-v'],cwd=extracted,capture_output=True,text=True)
    if tested.returncode:raise RuntimeError(tested.stdout+tested.stderr)
result=dict(status='passed',archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),fresh_neural_fit='ssl_transformer48_f0_s7_b0.2',maximum_probability_difference=error,isolated_paper_tests='8 passed',original_workspace_modified=False)
(ROOT/'output/paper_package_smoke.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
