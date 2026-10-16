"""Render the separate, explicitly descriptive v5 findings from checked result records."""
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from scientific_v5 import ROOT, OUT, METHODS, RADII, read, verify_signature

NAMES = {'rf_leaf4': 'Random forest', 'cnn64': 'CNN', 'transformer48': 'Kısa Transformer',
         'ssl_transformer48': 'SSL Transformer', 'step_matched': 'Adım eşlenmiş Transformer'}


def main():
    verify_signature()
    analysis = read(OUT / 'analysis.json')
    verification = read(OUT / 'verification.json')
    checkpoint_check = read(OUT / 'checkpoint_verification.json')
    if analysis['status'] != 'complete_verified' or verification['status'] != 'passed' or checkpoint_check['status'] != 'passed':
        raise ValueError('Complete verified results are required before reporting')
    support = read(OUT / 'support_audit.json')
    values = {(r['radius_km'], r['method']): r for r in analysis['summary']}
    fmt = lambda value: f'{value:.4f}'.replace('.', ',')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
    fig, ax = plt.subplots(figsize=(11.5, 6.1))
    colors = ['#748a85', '#dd9e52', '#6d8cbd', '#276e57', '#954f72']
    positions = np.arange(len(RADII)); width = .15
    for index, method in enumerate(METHODS):
        scores = [values[r, method]['macro_f1'] for r in RADII]
        bars = ax.bar(positions + (index - 2) * width, scores, width=width, label=NAMES[method], color=colors[index])
        for bar, value in zip(bars, scores):
            ax.text(bar.get_x() + bar.get_width()/2, value + .009, f'{value:.3f}', ha='center', va='bottom', fontsize=8, rotation=90)
    ax.set_xticks(positions, [f'{r} km\n{s["groups"]} bileşen / {s["positive_groups"]} kesim bileşeni' for r, s in zip(RADII, support['radii'])])
    ax.set_ylim(0, 1.08); ax.set_ylabel('Birleştirilmiş dış kat macro-F1')
    ax.set_title('Mekânsal gruplama duyarlılığı  •  %20 etiket  •  yalnız seed 7', loc='left', fontsize=14, pad=20)
    ax.spines[['top', 'right']].set_visible(False)
    ax.yaxis.grid(True, alpha=.16); ax.set_axisbelow(True)
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.14), ncol=3, frameon=False, fontsize=9)
    fig.text(.06, .015, 'Betimsel ek deney: yarıçapla birlikte katlar ve eğitim örnekleri değişir. Hata çubuğu / doğrulayıcı anlamlılık iddiası yok.', fontsize=9, color='#555555')
    fig.subplots_adjust(bottom=.25, left=.08, right=.98, top=.88)
    fig.savefig(OUT / 'radius_sensitivity.png', dpi=180)
    plt.close(fig)
    lines = [
        '# Mekânsal yarıçap duyarlılığı tamamlanan ek deney',
        '',
        '**Sürüm:** paper_v5_exploratory. **Durum:** 75 gerçek eğitim tamamlandı; 75 checkpoint yeniden yüklenerek tahminleri doğrulandı. paper_v4 ana deneyi ve ürün modeli değiştirilmedi.',
        '',
        'Bu çalışma, aynı sabit DISFOR kohortunda mekânsal gruplama kuralını 5, 10 ve 20 km olarak değiştirir. Her yarıçapta aynı beş yöntem, beş dış kat, seed 7 ve yüzde 20 etiketle çalıştırıldı. Sonuçlar tek seed için birleştirilmiş dış kat tahminleridir. paper_v4 tablosundaki üç seed ortalamasıyla aynı istatistik değildir.',
        '',
        '## Önceden sabitlenen düzen',
        '',
        'Kod, işlenmiş veri, örnek manifesti, protokol, bütün katlar ve paylaşılan etiket kimlikleri ilk v5 eğitimi başlamadan SHA-256 ile kaydedildi. Yerel hazırlama olayı `preparation_event.json` dosyasında sıfır koşu kaydıyla tutulur; dışarıda kaydedilmiş bir ön kayıt iddiası yapılmaz. Yeni eğitim kodu yalnız yeni deney dizinine yazar.',
        '',
        'Toplam 3 yarıçap × 5 kat × 1 seed × 1 etiket bütçesi × 5 yöntem = 75 koşu gerçekten yeniden eğitildi. Ana tarifler random forest, CNN, 40 epoch Transformer, 60 ön eğitim + 40 ince ayar epoch’lu SSL ve 320 epoch adım eşlenmiş Transformer’dır. Test eşiği 0,5’tir. Yeni model veya yarıçap seçimi, erken durdurma ve kalibrasyon yapılmadı. Adım eşleme işlem yükünü, süreyi, öğrenme oranını veya etiketli örnek gösterim sayısını eşitlemez.',
        '',
        '## Nokta desteği ile bağımsız bileşen desteği',
        '',
        '| Yarıçap | Bileşen | Kesim içeren bileşen | En büyük bileşen | Bir test katındaki en az kesim bileşeni |',
        '|---|---:|---:|---:|---:|',
    ]
    for r in support['radii']:
        lines.append(f'| {r["radius_km"]} km | {r["groups"]} | {r["positive_groups"]} | {r["largest_component"]} | {min(f["test_positive_groups"] for f in r["folds"])} |')
    lines += ['', 'Her yarıçapta aynı 2.213 konum, 1.937 orman ve 276 kesim korunmuştur; bütün test katlarında iki sınıf bulunur. Buna karşın 10 ve 20 km’de bazı katlardaki kesimler yalnız iki mekânsal bileşene dayanır. Çok sayıda yakın noktayı bağımsız kesim olayı gibi saymak belirsizliği küçümser. Örnekler yalnız uzaklıkla değil, uygun kampanyalardaki ortak kaynak olaylarıyla da birleştirilir.', '',
              '## Gerçekten ölçülen sonuçlar', '',
              '| Yarıçap | Yöntem | Macro-F1 | AP | Kesim duyarlılığı | Brier |',
              '|---|---|---:|---:|---:|---:|']
    for radius in RADII:
        for method in METHODS:
            r = values[radius, method]
            lines.append(f'| {radius} km | {NAMES[method]} | {fmt(r["macro_f1"])} | {fmt(r["average_precision"])} | {fmt(r["clear_cut_recall"])} | {fmt(r["brier"])} |')
    lines += ['', '![Yarıçap duyarlılığı ve bileşen desteği](../experiments/paper_v5_exploratory/radius_sensitivity.png)', '',
              'Her satırdaki ölçüt, beş test katındaki 2.213 tahmin birleştirildikten sonra hesaplandı. Kat F1 değerlerinin ortalaması alınmadı. AP average precision’dır; Brier için düşük değer tercih edilir. ROC-AUC dahil tam sayılar `results.csv` ve `analysis.json` içindedir.', '',
              '## Karşılaştırmanın yorumu', '']
    for radius in RADII:
        ssl = values[radius, 'ssl_transformer48']['macro_f1']
        short = values[radius, 'transformer48']['macro_f1']
        long = values[radius, 'step_matched']['macro_f1']
        lines.append(f'- {radius} km: SSL eksi kısa Transformer farkı {fmt(ssl-short)}; SSL eksi adım eşlenmiş Transformer farkı {fmt(ssl-long)}.')
    lines += ['', 'Bu farklar betimseldir. Bir seed üzerinden standart sapma, p değeri veya doğrulayıcı güven aralığı raporlanmaz. Yarıçap büyüdükçe bağlı bileşenler birleşir; katlar ve eğitime seçilen etiket kimlikleri de değişir. Bu deney, yalnız mesafenin nedensel etkisini ayıran bir deney değildir. Yarıçapların her biri içindeki yöntemler aynı etiketli örneklerle eşlenmiştir.', '',
              'Sonuçlar, coğrafi değerlendirme tasarımına duyarlılığı görünür kılar. Bir yarıçapta en yüksek skoru almak o yarıçapı seçme gerekçesi yapılmamalıdır. Yeni dış saha doğrulaması, ülke haritası veya genel mimari üstünlüğü kanıtı üretilmiş değildir.', '',
              '## Ülke dışarıda bırakma kapsamı', '',
              'Sabit kaynak `samples.parquet` tablosunda ve işlenmiş örnek manifestinde ülke alanı bulunmadı. Bu v5 protokolünde kaynakta olmayan bir ülke etiketi varsayılmadı; ülke başına sınıf ve olay desteği bu nedenle null olarak kaydedildi ve ülke dışarıda bırakma deneyi çalıştırılmadı. Kaynağı doğrulanmış sınır poligonlarından ayrıca ülke türetmek mümkündür; böyle bir alan kaynak DISFOR etiketi değil, yeni türetilmiş metadata olur ve ayrı destek denetimi/protokol gerektirir.', '',
              '## Yeniden üretim ve bütünlük', '',
              f'5 km koşullarının eski paper_v4 seed 7 olasılıklarıyla en büyük farkı {max(r["maximum_probability_difference"] for r in analysis["radius_5_v4_reproduction"]):.3g} olarak ölçüldü. Bu karşılaştırma yeniden üretim kontrolüdür; yeni bağımsız doğrulama değildir.',
              f'Yeni 75 kayıtlı ağırlık tekrar yüklendi. Çıkarım ile kaydedilmiş olasılıklar arasındaki en büyük fark {checkpoint_check["maximum_probability_difference"]:.3g}; kontrol edilen tahmin değeri sayısı {checkpoint_check["prediction_values"]} oldu. Bunlar aynı 2.213 konumun farklı model/yarıçap tekrarlarıdır.', '',
              '```bash', '.venv/bin/python scripts/scientific_v5.py prepare', '.venv/bin/python scripts/scientific_v5.py pilot --workers 1 --max-jobs 5', '.venv/bin/python scripts/scientific_v5.py train --workers 2 --max-jobs 75', '.venv/bin/python scripts/verify_spatial_v5.py', '.venv/bin/python scripts/report_spatial_v5.py', '.venv/bin/python -m unittest discover -s tests -p test_scientific_v5.py -v', '```', '',
              'Tamamlanan koşular aynı imzalarla tekrar çalıştırıldığında önbellekte tutulur. Gerçek sıfırdan tekrar için ayrı proje kopyasında yeni v5 koşu/ağırlık çıktı alanları kullanılmalıdır; özgün kayıtlar korunmalıdır. Kod veya protokol değişirse imza denetimi yürütmeyi durdurur. Dosyalar: `protocol.json`, `support_audit.json`, `folds_r*.json`, `groups.json`, `jobs.json`, `signature.json`, `runs/`, `checkpoints/`, `analysis.json`, `results.csv`, `oof_predictions.npz`, `verification.json`, `checkpoint_verification.json`.']
    (ROOT / 'docs/PAPER_V5_MEKANSAL_DUYARLILIK.md').write_text('\n'.join(lines) + '\n')
    print('Wrote docs/PAPER_V5_MEKANSAL_DUYARLILIK.md and radius_sensitivity.png')


if __name__ == '__main__':
    main()
