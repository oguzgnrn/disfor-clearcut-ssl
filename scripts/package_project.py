"""Build and integrity-check complete and meeting-only local delivery archives."""
from pathlib import Path
import hashlib
import json
import zipfile
from verify_package import verify

ROOT = Path(__file__).resolve().parents[1]
ROOTS = [
    'README.md', '.gitignore', 'DEMOYU_AC.command', 'MVP_CALISTIR.command',
    'MODELI_CALISTIR.command', 'URUNU_AC.command', 'PAPER_RAPORUNU_AC.command',
    'requirements.txt', 'requirements-report.txt', 'requirements-lock.txt',
    'requirements-paper.txt', 'paper', 'output/paper', 'output/final',
    'output/product_demo', 'assets', 'experiments', 'data', 'docs', 'figures',
    'models', 'reports', 'scripts', 'src', 'tests', 'output/pdf',
    'output/prediction', 'output/advanced_prediction',
    'output/release_verification.json', 'output/paper_package_verification.json',
    'output/paper_package_smoke.json',
]
MEETING_FILES = {
    'PAPER_RAPORUNU_AC.command', 'reports/paper_v4.html',
    'output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.docx',
    'output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf',
    'output/paper/Orman_SSL_Manuscript.docx',
    'output/pdf/Orman_SSL_Manuscript.pdf',
    'docs/ARASTIRMA_VE_URUN_RAPORU.md',
    'docs/GORUSME_AKISI_VE_SORULAR.md',
    'docs/HOCAYA_ILK_NOTLAR_VE_FIKIRLER.md',
    'docs/PAZAR_TOPLANTI_AKISI.md',
    'docs/PAPER_V5_MEKANSAL_DUYARLILIK.md',
    'docs/URUN_KILAVUZU.md',
    'docs/NIHAI_BILIMSEL_DENETIM.md',
    'docs/NIHAI_TEKNIK_DENETIM.md',
    'experiments/paper_v4/analysis.json',
    'experiments/paper_v4/review_candidates.geojson',
    'experiments/paper_v4/support_error_audit.json',
    'experiments/paper_v4/data_reproduction_audit.json',
    'experiments/paper_v5_exploratory/analysis.json',
    'experiments/paper_v5_exploratory/results.csv',
    'experiments/paper_v5_exploratory/radius_sensitivity.png',
    'experiments/paper_v6_label_curve/analysis.json',
    'experiments/paper_v6_label_curve/combined_curve.csv',
    'experiments/paper_v6_label_curve/protocol.json',
    'reports/product_ui_verification.json',
    'scripts/verify_package.py',
}

MEETING_README = '''# Orman-SSL — hocaya sunum ve inceleme paketi

Bu arşiv Türkçe araştırma raporu, İngilizce makale ve görüşme belgelerini
içerir. Hazır belgeleri okumak için Python kurulumu gerekmez.

## Önce açılacak dosyalar

1. `output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf`: Türkçe araştırma ve
   ürün raporu; düzenlenebilir Word karşılığı aynı klasördedir.
2. `docs/HOCAYA_ILK_NOTLAR_VE_FIKIRLER.md`: hocanın verdiği başlıklara
   karşılıklar, makale notları, pilot bulgular ve sorular;
   `docs/PAZAR_TOPLANTI_AKISI.md`: 18 Ekim görüşme akışı. Eski uzun akış
   `docs/GORUSME_AKISI_VE_SORULAR.md` içindedir.
3. `output/pdf/Orman_SSL_Manuscript.pdf`: İngilizce bilimsel makale;
   Word dosyası `output/paper/Orman_SSL_Manuscript.docx` içindedir.
4. `reports/paper_v4.html`: çevrimdışı araştırma özeti ve hata inceleme
   tablosu. Mac'te `PAPER_RAPORUNU_AC.command` ile de açılır.

`docs/URUN_KILAVUZU.md` ürünün kullanımını anlatır. Bu küçük sunum arşivi
ürün sunucusunu, ham veriyi ve model ağırlıklarını içermez. Ürünü gerçekten
çalıştırmak için `Orman_SSL_Proje_Paketi.zip` dosyasını açıp o paketin
README'sindeki kurulum ve `URUNU_AC.command` yönergelerini kullanın.

## Diğer paketler

- `Orman_SSL_Paper_Paketi.zip`: işlenmiş veri, 180 koşunun kayıtları ve
  paper_v4 deneyini yeniden çalıştırmak için bilimsel kod.
- `Orman_SSL_Proje_Paketi.zip`: yerel ürün, ham ve işlenmiş veri, bütün
  model ağırlıkları, eğitim kodu ve testler.
- `Orman_SSL_Nihai_Model.zip`: 10 üyeli advanced_v3 modeliyle hazır etiketsiz
  NPZ girdisinden çıkarım; bu paketin kendi README'si izlenmelidir.

Buradaki `paper/SUPPLEMENT.md` bilimsel tekrar üretim yöntemini açıklar;
komutları uygulamak için paper veya tam proje arşivi gerekir. Bu sunum
arşivi eğitim veya canlı ürün çalıştırma paketi değildir.

paper_v4, 2.213 konum üzerinde geriye dönük coğrafi araştırma denetimidir;
paper_v5 (gruplama yarıçapı, tek seed) ve paper_v6 (etiket bütçesi eğrisi)
aynı kohort üzerinde ilan edilmiş uzantılardır ve `experiments/` altında
özetleri bulunur.
Ürünün advanced_v3 modeli ayrı bir sürümdür; 486 noktalık değerlendirmesi
daha önce incelenmiş benchmark üzerindedir. İkisi bağımsız Türkiye saha
başarımı veya makale kabulü olarak sunulmaz. Yazar, kurum, katkı, fon ve
yayımlama kararları gerçek araştırmacılar tarafından kesinleştirilmelidir.

`docs/NIHAI_BILIMSEL_DENETIM.md` ve `docs/NIHAI_TEKNIK_DENETIM.md` kapsamı
açıklar. Mevcut `reports/final*.json`, `reports/final*.log` ve varsa
`reports/product_ui_verification.json` denetim kayıtları pakete eklenir.
Her kayıt, kendi tarihine ve kapsadığı sürüme göre okunmalıdır.

`PACKAGE_MANIFEST.json`, bu README dahil paketteki dosyaların boyut ve
SHA-256 değerlerini taşır. Yapay zekâ yardımı ve insan araştırmacı
sorumluluğu raporda belirtilmiştir.
'''


def collect_files():
    files = []
    for name in ROOTS:
        path = ROOT / name
        if not path.exists():
            raise FileNotFoundError(name)
        files.extend([path] if path.is_file() else
                     [item for item in path.rglob('*') if item.is_file()])
    return sorted(set(path for path in files
                      if '__pycache__' not in path.parts
                      and path.name != '.DS_Store' and path.suffix != '.pyc'))


def is_meeting_file(path):
    relative = path.relative_to(ROOT)
    return (relative.parts[0] == 'paper'
            or str(relative) in MEETING_FILES
            or (relative.parent == Path('reports')
                and relative.name.startswith('final')
                and relative.suffix in {'.json', '.log'}))


def build_archive(name, selected, embedded=None):
    embedded = embedded or {}
    selected = [path for path in selected
                if str(path.relative_to(ROOT)) not in embedded]
    manifest = []
    dest = ROOT / 'output' / name
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in selected:
            relative = str(path.relative_to(ROOT))
            payload = path.read_bytes()
            info = zipfile.ZipInfo.from_file(path, arcname='Orman_SSL/' + relative)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)
            manifest.append(dict(path=relative, bytes=len(payload),
                                 sha256=hashlib.sha256(payload).hexdigest()))
        for relative, value in sorted(embedded.items()):
            payload = value.encode('utf-8')
            archive.writestr('Orman_SSL/' + relative, payload)
            manifest.append(dict(path=relative, bytes=len(payload),
                                 sha256=hashlib.sha256(payload).hexdigest()))
        archive.writestr('Orman_SSL/PACKAGE_MANIFEST.json',
                         json.dumps(sorted(manifest, key=lambda row: row['path']), indent=2))
    verification = verify(dest)
    return dict(path=str(dest.relative_to(ROOT)), files=len(manifest),
                bytes=dest.stat().st_size,
                sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
                zip_crc_check='passed', sha256_manifest_check=verification['status'])


def main():
    files = collect_files()
    (ROOT / 'output').mkdir(exist_ok=True)
    records = [build_archive('Orman_SSL_Proje_Paketi.zip', files)]
    records.append(build_archive(
        'Orman_SSL_Hocaya_Sunum.zip',
        [path for path in files if is_meeting_file(path)],
        {'README.md': MEETING_README,
         'SUNUM_PAKETI.txt': 'Önce README.md ve output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf dosyasını açın.\n'},
    ))
    (ROOT / 'output/package_manifest.json').write_text(json.dumps(records, indent=2))
    print(json.dumps(records, indent=2))


if __name__ == '__main__':
    main()
