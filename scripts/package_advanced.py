"""Create a portable inference-only archive for the completed advanced bundle."""
from pathlib import Path
import hashlib
import json
import zipfile
from verify_package import verify
ROOT=Path(__file__).resolve().parents[1]
paths=[]
for directory in ['src','models/advanced_v3']:
    paths += [p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
paths += [ROOT/n for n in ['requirements.txt','requirements-lock.txt','data/processed/test_inference.npz','scripts/verify_package.py',
    'experiments/advanced_v3/protocol.json','experiments/advanced_v3/selection.json','experiments/advanced_v3/evaluation.json','experiments/advanced_v3/acceptance.json']]
manifest=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(paths)]
readme='''# Orman-SSL — nihai model paketi

Bu paket 10 üyeli gelişmiş modeli ve etiketsiz örnek NPZ girdisini içerir.
Python 3.11 ile, bu klasörde:

    python3.11 -m venv .venv
    .venv/bin/python -m pip install -r requirements-lock.txt
    PYTHONPATH=src .venv/bin/python -m orman_ssl.predict_advanced --bundle models/advanced_v3/bundle.json --data data/processed/test_inference.npz --out predictions.json

Çıktıda sınıf, geliştirme verisinde kalibre edilmiş skor, model üyeleri arasındaki fark ve kalite bayrağı bulunur. Kalibrasyon yeni coğrafyada doğruluk garantisi değildir. Bu örnek önceden incelenmiş 486 test noktasıdır; yeni saha doğrulaması değildir.

Ham gözlemden aylık veri hazırlama, tam eğitim ve bütün deney kayıtları Orman_SSL_Proje_Paketi.zip içindedir. Bu küçük paket yalnızca çıkarım ve model incelemesi içindir. Eğitim sırasında hiçbir test etiketi kullanılmamıştır; benchmark daha önce incelendiğinden tamamen yeni bağımsız test olarak sunulmaz.

Yalnızca bu proje tarafından üretilmiş güvenilir model dosyalarını kullanın. DISFOR kaynak lisansı EUPL-1.2; kaynak ve kullanım sınırları bundle metadata içinde kayıtlıdır.
'''
readme_bytes=readme.encode();manifest.append(dict(path='README.md',bytes=len(readme_bytes),sha256=hashlib.sha256(readme_bytes).hexdigest()))
license_path=ROOT/'data/disfor/LICENSE';paths.append(license_path)
manifest.append(dict(path='data/disfor/LICENSE',bytes=license_path.stat().st_size,sha256=hashlib.sha256(license_path.read_bytes()).hexdigest()))
out=ROOT/'output/Orman_SSL_Nihai_Model.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(paths):z.write(p,arcname='Orman_SSL/'+str(p.relative_to(ROOT)))
    z.writestr('Orman_SSL/README.md',readme_bytes)
    z.writestr('Orman_SSL/PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
result=verify(out);result.update(path=str(out.relative_to(ROOT)),bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest())
(ROOT/'output/advanced_package_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
