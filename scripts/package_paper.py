"""Compact scientific reproduction archive with a package-specific README."""
import hashlib
import json
import zipfile
from pathlib import Path
from verify_package import verify

ROOT = Path(__file__).resolve().parents[1]
ROOTS = [
    'paper', 'output/paper', 'output/pdf/Orman_SSL_Manuscript.pdf',
    'experiments/paper_v4', 'src', 'tests/test_paper.py',
    'data/processed/real_series.npz', 'data/disfor/sample_manifest.json',
    'data/disfor/LICENSE', 'data/disfor/downloads.json',
    'reports/disfor_preparation.json', 'reports/paper_v4.html',
    'requirements-lock.txt', 'requirements-paper.txt', 'PAPER_RAPORUNU_AC.command',
    'scripts/train_paper.py', 'scripts/analyze_paper.py', 'scripts/verify_paper.py',
    'scripts/plot_paper.py', 'scripts/compose_paper.py',
    'scripts/audit_paper_errors.py', 'scripts/build_paper_hub.py',
    'scripts/build_paper_docx.py', 'scripts/verify_package.py',
    'scripts/package_paper.py',
]
OPTIONAL_FILES = [
    'output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.docx',
    'output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf',
    'docs/ARASTIRMA_VE_URUN_RAPORU.md',
    'docs/GORUSME_AKISI_VE_SORULAR.md',
    'docs/URUN_KILAVUZU.md',
    'docs/VERI_SOZLESMESI.md',
    'docs/NIHAI_BILIMSEL_DENETIM.md',
    'docs/NIHAI_TEKNIK_DENETIM.md',
    'reports/final_delivery_verification.json',
    'reports/product_ui_verification.json',
    'reports/final_science_review.json',
    'reports/final_report_document_qa.json',
    'reports/final_engineering_review.json',
    'reports/final_engineering_tests.log',
    'output/paper_document_qa.json',
]

PAPER_README = '''# Orman-SSL — paper_v4 bilimsel tekrar üretim paketi

Bu arşiv 2.213 konumlu işlenmiş veri, sabit protokol, 180 tamamlanmış koşu,
ayrılmış tahminler, bilimsel kod, sekiz paper testi ve İngilizce makaleyi
içerir. Hazır Word/PDF dosyaları Python kurulmadan okunabilir.

## İlk açılacak dosyalar

- `output/pdf/Orman_SSL_Manuscript.pdf`: İngilizce makale.
- `output/paper/Orman_SSL_Manuscript.docx`: düzenlenebilir makale.
- `reports/paper_v4.html`: çevrimdışı Türkçe araştırma özeti.
- `paper/SUPPLEMENT.md`: ayrıntılı yöntem ve tekrar üretim açıklaması.
- `paper/CLAIM_LEDGER.md`: iddiaların kanıt dosyalarıyla eşleştirmesi.

Türkçe araştırma ve ürün raporu varsa `output/final/` içindedir; raporun
ürün bölümü tam proje paketindeki ayrı advanced_v3 uygulamasını anlatır.
Bu bilimsel arşiv canlı ürün çalıştırmak için hazırlanmış değildir.

## Bu arşivin içeriğiyle çalışan bilimsel komutlar

Terminali bu README'nin bulunduğu `Orman_SSL` klasöründe açın. Python 3.11
ve ilk kurulumda bağımlılıkları indirmek için internet gerekir:

```bash
python3.11 -m venv .venv-paper
.venv-paper/bin/python -m pip install -r requirements-lock.txt
.venv-paper/bin/python scripts/verify_paper.py
.venv-paper/bin/python -m unittest discover -s tests -p test_paper.py -v
```

İşlenmiş veriyle bilimsel eğitim ve analiz zinciri:

```bash
.venv-paper/bin/python scripts/train_paper.py --workers 3
.venv-paper/bin/python scripts/analyze_paper.py
.venv-paper/bin/python scripts/verify_paper.py
.venv-paper/bin/python scripts/plot_paper.py
.venv-paper/bin/python scripts/compose_paper.py
.venv-paper/bin/python scripts/audit_paper_errors.py
.venv-paper/bin/python scripts/build_paper_hub.py
```

Eğitim komutu, imzaları eşleşen mevcut 180 koşuyu tekrar kullanır; komutu
çalıştırmak tek başına yeniden eğitim yapıldığı anlamına gelmez. Gerçekten
sıfırdan tekrar için arşivi ayrı bir klasöre çıkarın; o kopyadaki
`experiments/paper_v4/runs` klasörünü ve `experiments/paper_v4/completion.json`
dosyasını proje klasörünün dışına taşıyıp eğitim komutunu çalıştırın.
Orijinal sonuçları karşılaştırma için koruyun. Kod/veri/protokol değişikliği
ayrı deney sürümü gerektirir. Farklı ortamda sayısal eşitlik garanti edilmez.

Word makalesini yeniden üretmek için:

```bash
.venv-paper/bin/python -m pip install -r requirements-paper.txt
.venv-paper/bin/python scripts/build_paper_docx.py
```

PDF çıktısı ayrıca uyumlu bir belge dönüştürücü gerektirir; hazır PDF
pakete dahildir. Bu paketteki sekiz test yalnız paper kapsamındadır;
tam projenin ürün ve ham veri testleri burada yer almaz.

## Tam proje gerektiren işler

Ham Parquet gözlemleri, ham veriden örnek hazırlama ve kullanılmamış nokta
taraması, advanced_v3 model ağırlıkları, yerel ürün sunucusu ve bütün
proje testleri `Orman_SSL_Proje_Paketi.zip` içindedir. Ürünü çalıştırmak
veya ham gözlemlerden yeni tahmin üretmek için tam proje arşivini kullanın.
Hazır NPZ üzerinde yalnız advanced_v3 çıkarımı için
`Orman_SSL_Nihai_Model.zip` ve onun README'si kullanılabilir.

Buradaki `src/` kodu bilimsel eğitimin bağımlılığıdır; tek başına ürünün
ağırlıklarını veya ham gözlemleri içermez. Yöntem ekindeki ham-veri
denetimleri ve Türkçe rapordaki ürün komutları tam proje paketini gerektirir.

## Bilimsel kapsam ve bütünlük

paper_v4 aynı kaynak üzerindeki önceki geliştirmelerden sonra yapılan
geriye dönük coğrafi denetimdir. Sonuçlar bağımsız Türkiye saha doğrulaması,
yeni mimari veya makale kabulü iddiası değildir. advanced_v3 ürün modeli
ayrı bir değerlendirmedir. Yazar ve yayın beyanları araştırmacılarla
kesinleştirilmelidir; kaynak lisansı `data/disfor/LICENSE` içinde korunur.

`PACKAGE_MANIFEST.json`, bu pakete özgü README dahil bütün içeriklerin
boyutlarını ve SHA-256 değerlerini taşır. Arşiv, projedeki
`scripts/verify_package.py` ile açılmadan önce doğrulanabilir.
'''


def collect_files():
    files = []
    for name in ROOTS:
        path = ROOT / name
        if not path.exists():
            raise FileNotFoundError(name)
        files.extend([path] if path.is_file() else
                     [item for item in path.rglob('*') if item.is_file()])
    files.extend(ROOT / name for name in OPTIONAL_FILES if (ROOT / name).is_file())
    return sorted(set(path for path in files
                      if '__pycache__' not in path.parts and path.suffix != '.pyc'
                      and path.name != '.DS_Store'))


def main():
    files = collect_files()
    manifest = []
    path = ROOT / 'output/Orman_SSL_Paper_Paketi.zip'
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for item in files:
            relative = str(item.relative_to(ROOT))
            payload = item.read_bytes()
            info = zipfile.ZipInfo.from_file(item, arcname='Orman_SSL/' + relative)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)
            manifest.append(dict(path=relative, bytes=len(payload),
                                 sha256=hashlib.sha256(payload).hexdigest()))
        payload = PAPER_README.encode('utf-8')
        archive.writestr('Orman_SSL/README.md', payload)
        manifest.append(dict(path='README.md', bytes=len(payload),
                             sha256=hashlib.sha256(payload).hexdigest()))
        archive.writestr('Orman_SSL/PACKAGE_MANIFEST.json',
                         json.dumps(sorted(manifest, key=lambda row: row['path']), indent=2))
    result = verify(path)
    result.update(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                  sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    (ROOT / 'output/paper_package_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
