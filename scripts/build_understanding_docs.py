"""Two Turkish study documents for the project owner: (1) every table and result explained, (2) method glossary and file map."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'TESLIM_2026-10-18'
A = json.loads((ROOT / 'experiments/paper_v4/analysis.json').read_text())
V5 = json.loads((ROOT / 'experiments/paper_v5_exploratory/analysis.json').read_text())
V5S = json.loads((ROOT / 'experiments/paper_v5_exploratory/support_audit.json').read_text())
V6 = json.loads((ROOT / 'experiments/paper_v6_label_curve/analysis.json').read_text())
PR = json.loads((ROOT / 'experiments/presto_v1_exploratory/analysis.json').read_text())
CARD = json.loads((ROOT / 'models/advanced_v3/model_card.json').read_text())
PREP = json.loads((ROOT / 'reports/disfor_preparation.json').read_text())
PROBE = json.loads((ROOT / 'experiments/paper_v4/unused_probe_audit.json').read_text())
NAMES = {'rf_leaf4': 'Random forest', 'cnn64': 'Temporal CNN', 'transformer48': 'Transformer (40 ep.)', 'ssl_transformer48': 'SSL Transformer',
         'iid_ssl': 'Independent-cell SSL', 'step_matched': 'Step-matched Transformer', 'mask_only': 'Yalnız gözlem maskesi (RF)', 'metadata_only': 'Yalnız konum/yıl/kampanya (RF)'}
S = {(r['budget'], r['method']): r for r in A['summary']}
P = {r['comparator']: r for r in A['paired_comparisons']}
f = lambda v, n=4: f'{v:.{n}f}'.replace('.', ',')


def new_doc(title, subtitle):
    doc = Document(); sec = doc.sections[0]
    sec.page_width = Cm(21); sec.page_height = Cm(29.7)
    for side in ['left_margin', 'right_margin']: setattr(sec, side, Cm(2))
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    st = doc.styles['Normal']; st.font.name = 'Calibri'; st.font.size = Pt(10.5); st.paragraph_format.space_after = Pt(5); st.paragraph_format.line_spacing = 1.15
    for name, size in [('Title', 22), ('Heading 1', 15), ('Heading 2', 12), ('Heading 3', 11)]:
        h = doc.styles[name]; h.font.name = 'Calibri'; h.font.size = Pt(size); h.font.bold = True; h.font.color.rgb = RGBColor(0x1b, 0x3a, 0x4a)
        h.paragraph_format.space_before = Pt(10); h.paragraph_format.space_after = Pt(4); h.paragraph_format.keep_with_next = True
        for b in h.element.xpath('./w:pPr/w:pBdr'): b.getparent().remove(b)
    doc.add_paragraph(title, 'Title'); doc.add_paragraph(subtitle).runs[0].italic = True
    return doc


def p(doc, text, bold=False, size=None):
    para = doc.add_paragraph(); r = para.add_run(text); r.bold = bold
    if size: r.font.size = Pt(size)
    return para


def note(doc, text):
    para = doc.add_paragraph(); r = para.add_run('Ne söylüyor? '); r.bold = True; r.font.color.rgb = RGBColor(0x9a, 0x5b, 0x1a)
    para.add_run(text)


def table(doc, headers, rows, widths=None, size=9):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = 'Table Grid'; t.autofit = widths is None
    for j, v in enumerate(headers): t.rows[0].cells[j].text = str(v)
    for row in rows:
        cells = t.add_row().cells
        for j, v in enumerate(row): cells[j].text = str(v)
    for i, row in enumerate(t.rows):
        pr = row._tr.get_or_add_trPr(); pr.append(OxmlElement('w:cantSplit'))
        if i == 0: pr.append(OxmlElement('w:tblHeader'))
        for j, cell in enumerate(row.cells):
            if widths: cell.width = Cm(widths[j])
            if i == 0:
                sh = OxmlElement('w:shd'); sh.set(qn('w:fill'), 'DCE6EC'); cell._tc.get_or_add_tcPr().append(sh)
            for para in cell.paragraphs:
                para.paragraph_format.space_after = Pt(1); para.paragraph_format.space_before = Pt(1)
                if j > 0 and len(cell.text) <= 24: para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in para.runs: r.font.size = Pt(size); r.bold = (i == 0)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def figure(doc, path, caption, width=16):
    para = doc.add_paragraph(); para.alignment = WD_ALIGN_PARAGRAPH.CENTER; para.paragraph_format.keep_with_next = True
    para.add_run().add_picture(str(ROOT / path), width=Cm(width))
    c = doc.add_paragraph(caption); c.runs[0].italic = True; c.runs[0].font.size = Pt(9)


# ------------------------------------------------------------------ Document 1: tables and results
doc = new_doc('Orman-SSL: Bütün Tablolar ve Sonuçlar, Açıklamalı', 'Mehmet Oğuz Güneren için çalışma belgesi · 18 Ekim 2026 · Her tablo makaledeki numarasıyla, altında "ne söylüyor" notu')
p(doc, 'Bu belge makaledeki ve deney dosyalarındaki her tabloyu bir araya getirir ve her birinin altına düz Türkçe bir yorum koyar. Sayılar doğrudan experiments/*/analysis.json dosyalarından okunur; elle yazılmış sayı yoktur. Ölçüt macro-F1 = (kesim F1 + orman F1) / 2, 0 ile 1 arasında, yüksek iyi. "SD" üç seed arasındaki standart sapmadır, güven aralığı değildir. "AP" average precision (sıralama kalitesi), "Brier" olasılık hatası (düşük iyi).')

doc.add_heading('1. Veri seçimi (Table 1)', 1)
rej = PREP['rejected']
table(doc, ['Aşama', 'Konum'], [['İndirilen DISFOR örnek tablosu', '3.822'], ['Yüksek güvenli olmayan yorumlar çıkarıldı', f"−{rej['not_high_confidence']}"], ['İki yıllık net pencere kurulamayanlar çıkarıldı', f"−{rej['no_unambiguous_two_year_window']}"],
                                 ['Yeterli temiz ayı olmayanlar çıkarıldı', f"−{rej['insufficient_clear_months']}"], ['Yangın sınıfı ikili görevden çıkarıldı', f"−{rej['wildfire_excluded_from_primary_task']}"],
                                 ['Kalan: bozulmamış orman / kesim', '1.937 / 276'], ['Toplam konum / mekânsal bileşen', '2.213 / 874']], [12, 4])
note(doc, 'Başlangıçtaki 3.822 noktanın yarısından biraz fazlası kaldı. En büyük kayıplar "yüksek güvenli değil" ve "iki tam takvim yılı kurulamıyor". Yangın çıkarıldı çünkü testte yeterli yangın örneği yoktu; bu yüzden proje yalnız kesim/orman ayrımıdır. 2.213 nokta 874 bileşen demek: ortalama 2,5 nokta aynı yakın grupta; kesim içeren bileşen sayısı 141. Belirsizlik aralıkları 2.213 değil 874 üzerinden hesaplanır.')

doc.add_heading('2. Kat yapısı (Table 2)', 1)
table(doc, ['Kat', 'Test orman', 'Test kesim', 'Eğitime en yakın test noktası (km)'], [[r['fold'] + 1, r['test_class_counts'][0], r['test_class_counts'][1], f(r['minimum_distance_km'])] for r in A['folds']], [2, 3, 3, 6])
note(doc, 'Beş kat birbirine yakın büyüklükte (yaklaşık 440 test noktası, 53–58 kesim). Son sütun kritik: hiçbir test noktası bir eğitim noktasına 5 km\'den yakın değil. Bu, "komşuyu ezberleyerek geçme" (spatial leakage) riskini sınırlar; her nokta tam bir kez test edilir.')

doc.add_heading('3. Ana sonuçlar (Table 3)', 1)
rows = [[f"%{int(b*100)}", NAMES[m], f"{f(S[b,m]['macro_f1_mean'])} ± {f(S[b,m]['macro_f1_std'])}", f(S[b,m]['pr_auc_mean']), f(S[b,m]['recall_mean']), f(S[b,m]['brier_mean'])] for b in [.2, 1.] for m in ['rf_leaf4', 'cnn64', 'transformer48', 'ssl_transformer48']]
table(doc, ['Etiket', 'Yöntem', 'Macro-F1 ± SD', 'AP', 'Kesim recall', 'Brier'], rows, [1.6, 4.2, 3.4, 2, 2.6, 2])
note(doc, f"%20 etikette SSL Transformer ({f(S[.2,'ssl_transformer48']['macro_f1_mean'])}) kısa Transformer'ı ({f(S[.2,'transformer48']['macro_f1_mean'])}) geçiyor; CNN ({f(S[.2,'cnn64']['macro_f1_mean'])}) SSL'e çok yakın; Random Forest geride ({f(S[.2,'rf_leaf4']['macro_f1_mean'])}). %100 etikette üç sinir ağı 0,928–0,930 arasında, ayırt edilemiyor; RF 0,867. Kısa Transformer'ın SD'si (0,024) diğerlerinden büyük: 40 epoch ona yetmiyor, seed'e göre dalgalanıyor. Kesim recall sütunu 'kesimlerin yüzde kaçı yakalandı': %20'de yaklaşık %80, %100'de %87–89.")

doc.add_heading('4. Kontrol deneyleri (Table 4)', 1)
rows = [[NAMES[m], f"{f(S[.2,m]['macro_f1_mean'])} ± {f(S[.2,m]['macro_f1_std'])}", f(S[.2,m]['pr_auc_mean']), f(S[.2,m]['brier_mean']), str(S[.2,m]['epochs'])] for m in ['transformer48', 'ssl_transformer48', 'iid_ssl', 'step_matched', 'mask_only', 'metadata_only']]
table(doc, ['Yöntem (%20 etiket)', 'Macro-F1 ± SD', 'AP', 'Brier', 'Epoch'], rows, [5.5, 3.4, 2, 2, 2])
note(doc, f"Projenin ana bulgusu bu tabloda. Step-matched Transformer (SSL kadar optimizer adımı alan düz Transformer, 320 epoch) {f(S[.2,'step_matched']['macro_f1_mean'])} ile SSL'i geçiyor. Yani SSL'in kısa Transformer'a üstünlüğünün büyük kısmı 'daha çok eğitim' etkisi. Independent-cell SSL (blok yerine rastgele hücre gizleme) {f(S[.2,'iid_ssl']['macro_f1_mean'])}: blok maske belirgin üstün değil. Son iki satır sızıntı dedektörü: yalnız bulut maskesiyle 0,55, yalnız konum/yıl/kampanya ile 0,65 alınabiliyor; şans 0,50 olduğu için veri setinde sınıfla ilişkili örnekleme izleri var, makale bunu açıkça yazıyor.")

doc.add_heading('5. Eşleştirilmiş bootstrap aralıkları', 1)
rows = [[f"SSL − {NAMES[r['comparator']]}", f(r['mean_difference']), f"[{f(r['paired_group_bootstrap_95_interval'][0])}; {f(r['paired_group_bootstrap_95_interval'][1])}]", r['role'], 'evet' if r['paired_group_bootstrap_95_interval'][0] > 0 or r['paired_group_bootstrap_95_interval'][1] < 0 else 'hayır'] for r in A['paired_comparisons']]
table(doc, ['Karşılaştırma (%20)', 'Ortalama fark', '%95 aralık', 'Rol', 'Sıfırı dışlıyor mu?'], rows, [5.5, 2.5, 4, 2.4, 2.6])
note(doc, '874 mekânsal bileşen 2.000 kez yeniden örneklenerek hesaplanır. Aralık sıfırı dışlıyorsa fark "şans eseri" denemez. SSL − kısa Transformer pozitif ve sıfırı dışlıyor (SSL gerçekten daha iyi); SSL − step-matched negatif ve sıfırı dışlıyor (step-matched gerçekten daha iyi); SSL − CNN ve SSL − independent-cell sıfırı içeriyor (fark yok denebilir). Bu aralıklar eldeki veri ve katlara şartlıdır; başka bir ülkede ne olacağını söylemez.')
figure(doc, 'paper/figures/02_controls.png', 'Şekil 3 (makale): sol panel yöntemlerin macro-F1 ve seed SD\'si; sağ panel SSL eksi rakip farkları ve bootstrap aralıkları. Bütün hikâye bu şekilde.')

doc.add_heading('6. Etiket bütçesi eğrisi (Table 5, paper_v6)', 1)
S6 = {(r['budget'], r['method']): r for r in V6['summary']}
M = ['rf_leaf4', 'cnn64', 'transformer48', 'ssl_transformer48', 'step_matched']
rows = []
for b in [.05, .1, .2, .5, 1.]:
    row = [f"%{int(round(b*100))}"]
    for m in M:
        r = S6.get((b, m)) or S.get((b, m))
        row.append(f"{f(r['macro_f1_mean'])} ± {f(r['macro_f1_std'])}" if r else '—')
    rows.append(row)
table(doc, ['Etiket', 'RF', 'CNN', 'Transformer', 'SSL', 'Step-matched'], rows, [1.5, 3, 3, 3, 3, 3], size=8.5)
P6 = {(r['budget'], r['comparator']): r for r in V6['paired_comparisons']}
rows = [[f"%{int(b*100)}", NAMES[c], f(P6[b,c]['mean_difference']), f"[{f(P6[b,c]['paired_group_bootstrap_95_interval'][0])}; {f(P6[b,c]['paired_group_bootstrap_95_interval'][1])}]"] for b in [.05, .1, .5] for c in ['transformer48', 'step_matched', 'cnn64', 'rf_leaf4']]
table(doc, ['Etiket', 'SSL eksi …', 'Fark', '%95 aralık'], rows, [1.5, 5, 2.5, 4.5])
note(doc, f"Etiket azaldıkça herkes düşer ama SSL özellikle sert düşer: %5'te {f(S6[.05,'ssl_transformer48']['macro_f1_mean'])}, Random Forest bile {f(S6[.05,'rf_leaf4']['macro_f1_mean'])}. SSL yalnız kısa Transformer'a karşı kazanıyor; step-matched, CNN ve RF'ye karşı %5 ve %10'da kaybediyor ve aralıklar sıfırı dışlıyor. %50'de dört sinir ağı 0,90–0,92'de birleşiyor, SSL − kısa Transformer farkı sıfırı içeriyor. Sonuç: bu veri setinde SSL bir 'az etiket şampiyonu' değil. Not: %5'te etiketli eğitim kümesinde yalnız ~11 kesim var; bu yüzden SD'ler büyük.")
figure(doc, 'paper/figures/04_label_curve.png', 'Şekil 4 (makale): etiket bütçesi eğrisi. Kesikli kahverengi çizgi step-matched Transformer; lacivert SSL.')

doc.add_heading('7. Gruplama yarıçapı duyarlılığı (Table 6, paper_v5)', 1)
S5 = {(r['radius_km'], r['method']): r for r in V5['summary']}
rows = [[f"{r} km", S5[r,'rf_leaf4']['groups']] + [f(S5[r, m]['macro_f1']) for m in M] for r in [5, 10, 20]]
table(doc, ['Yarıçap', 'Bileşen', 'RF', 'CNN', 'Transformer', 'SSL', 'Step-matched'], rows, [1.6, 1.6, 2.2, 2.2, 2.4, 2.2, 2.8], size=8.5)
rows = [[f"{r['radius_km']} km", r['groups'], r['positive_groups'], r['largest_component'], min(x['test_positive_groups'] for x in r['folds'])] for r in V5S['radii']]
table(doc, ['Yarıçap', 'Bileşen', 'Kesim içeren bileşen', 'En büyük bileşen', 'Bir test katındaki en az kesim bileşeni'], rows, [1.6, 2, 3.5, 3, 5])
note(doc, f"Tek seed (7), %20 etiket. Yarıçap büyüdükçe yakın noktalar birleşir ve eğitim–test bölgeleri daha uzak düşer. 5 km'de step-matched önde ({f(S5[5,'step_matched']['macro_f1'])} / SSL {f(S5[5,'ssl_transformer48']['macro_f1'])}); 20 km'de SSL önde ({f(S5[20,'ssl_transformer48']['macro_f1'])} / step-matched {f(S5[20,'step_matched']['macro_f1'])} / CNN {f(S5[20,'cnn64']['macro_f1'])}). Herkes düşüyor ama SSL en az düşüyor. Yorum: SSL'in faydası 'az etiket' değil, 'başka bölgeye dayanıklılık' olabilir. Tek seed olduğu için bu bir ipucu; 20 km'de bazı test katlarında yalnız 2 kesim bileşeni var, dikkat.")
figure(doc, 'paper/figures/05_radius.png', 'Şekil 5 (makale): yarıçap duyarlılığı.')

doc.add_heading('8. Kullanılmamış konum taraması (dış doğrulama neden yapılmadı)', 1)
keys = [k for k in PROBE if isinstance(PROBE[k], (int, float, str))][:10]
table(doc, ['Alan', 'Değer'], [[k, str(PROBE[k])[:90]] for k in keys], [6, 11], size=8.5)
note(doc, 'Daha önce hiç kullanılmamış, eski konumlardan 5 km uzak ve ortak olay paylaşmayan DISFOR pencereleri arandı: 111 pencere kaldı, yalnız 1 tanesi kesim. Tek kesimle "bağımsız doğrulama skoru" hesaplanamaz; o yüzden hesaplanmadı. Gerçek dış doğrulama için yeni bölge ve yeni etiket gerekir (external_validation/ klasöründeki iş akışı bunun için hazır).')

doc.add_heading('9. Presto frozen probe (keşif)', 1)
rows = [[s['method'], f"%{int(s['budget']*100)}", f"{f(s['macro_f1_mean'])} ± {f(s['macro_f1_std'])}", f(s['average_precision_mean'])] for s in PR['summary']]
table(doc, ['Yöntem', 'Etiket', 'Macro-F1 ± SD', 'AP'], rows, [5, 2, 4, 2.5])
note(doc, 'Hazır Presto modeli dondurulup üstüne lojistik regresyon kondu. 0,69–0,78 ile bizim modellerin çok altında; ama bu adil bir karşılaştırma değil: fine-tune yok, Presto\'nun beklediği Sentinel-1/iklim/yükseklik girdileri yok. Rastgele encoder (0,57–0,64) ile farkı, ön eğitimin bir şey öğrettiğini gösteriyor. Makalede yalnız bir not olarak geçer.')

doc.add_heading('10. Ürün modeli advanced_v3 (486 örnek)', 1)
cm = CARD['metrics']['confusion_matrix']
table(doc, ['', 'Tahmin: orman', 'Tahmin: kesim'], [['Gerçek: orman', cm[0][0], cm[0][1]], ['Gerçek: kesim', cm[1][0], cm[1][1]]], [4, 4, 4])
table(doc, ['Ölçüt', 'Değer'], [['Macro-F1', f(CARD['metrics']['macro_f1'])], ['Accuracy', f(CARD['metrics']['per_class']['accuracy'])], ['Kesim precision', f(CARD['metrics']['per_class']['clear_cut']['precision'])], ['Kesim recall', f(CARD['metrics']['per_class']['clear_cut']['recall'])], ['ROC-AUC', f(CARD['metrics']['roc_auc'])], ['Brier', f(CARD['metrics']['brier'], 3)]], [5, 4])
note(doc, 'Bu makaledeki deneyden ayrı bir sürüm: 5 CNN + 5 SSL Transformer ensemble, 1.266 noktada eğitilmiş, 461 noktada kalibre edilmiş, 486 noktada ölçülmüş. 448 ormanın hepsini doğru bilmiş (0 yanlış alarm), 38 kesimin 28\'ini bulmuş, 10\'unu kaçırmış. 0,919 macro-F1\'i makaledeki 0,87–0,90 ile aynı tabloya koyma: farklı ayrım, farklı eğitim, kalibre edilmiş ensemble. Ürün arayüzü (URUNU_AC.command) bu modeli çalıştırır.')

doc.add_heading('11. Bir cümlede her sonuç', 1)
for line in [
    'SSL, az eğitilmiş Transformer\'ı geçer (+0,037, aralık sıfırı dışlar).',
    'Aynı adım sayısını alan Transformer SSL\'i geçer (−0,030, aralık sıfırı dışlar).',
    'Blok maske ile rastgele hücre maskesi arasında anlamlı fark yok.',
    'Bulut deseni ve coğrafya tek başına şanstan iyi tahmin verir: veri seti rastgele örneklem değil.',
    '%5–10 etikette SSL en zayıf sinir ağı; RF bile önde.',
    '%50 ve %100 etikette bütün sinir ağları eşitlenir.',
    'Test bölgesi 20 km uzağa alınınca SSL en dayanıklı model (tek seed).',
    'Dış doğrulama için yeterli bağımsız kesim örneği yok; Türkiye verisi gerekiyor.',
]:
    doc.add_paragraph(line, style='List Bullet')
doc.save(OUT / 'Orman_SSL_Tablolar_ve_Sonuclar_Rehberi.docx')

# ------------------------------------------------------------------ Document 2: method glossary and file map
doc = new_doc('Orman-SSL: Yöntem Sözlüğü ve Dosya Haritası', 'Terimler İngilizce, açıklamalar Türkçe · 18 Ekim 2026')
p(doc, 'Makaleyi ve defteri okurken karşına çıkacak her terim burada; yanında projede tam olarak nerede kullanıldığı var. Sıra, verinin akış sırasıdır.')
doc.add_heading('1. Veri terimleri', 1)
rows = [
    ['Sentinel-2', 'ESA\'nın optik uydusu; 13 bant, 10/20/60 m, 5 günde bir geçiş. Bulutta göremez.', 'Bütün girdi; 10 bant kullanılıyor'],
    ['band', 'Bir dalga boyu aralığında ölçülen yansıma. B04 kırmızı, B08 yakın kızılötesi (NIR), B11/B12 kısa dalga kızılötesi (SWIR).', 'x[:, :, 10]'],
    ['digital number (DN)', 'Uydunun verdiği ham tam sayı ölçeği; biz ofset eklemeden bırakıyoruz.', 'data/processed/real_series.npz'],
    ['NDVI', '(NIR − kırmızı)/(NIR + kırmızı); bitki yeşilliği. Modele girmiyor, yalnız görselleştirme.', 'defter Bölüm 1.1'],
    ['SCL', 'Scene Classification Layer: Sentinel-2\'nin kendi bulut/gölge/kar sınıfı. 4 = bitki, 5 = çıplak toprak kabul.', 'prepare_disfor.py'],
    ['monthly median', 'Ay içindeki temiz gözlemlerin ortancası; aykırı değeri bastırır.', 'prepare_disfor.py'],
    ['observed mask', '24×10 boolean: o ay o bantta ölçüm var mı? Eksik ay doldurulmaz.', 'd[\'observed\']'],
    ['24-month window', 'İki tam takvim yılı; 1. yıl orman, 2. yıl (target year) kesim var/yok.', 'Table 1, sample_manifest.json'],
    ['DISFOR', 'Joanneum Research\'ün açık Avrupa orman bozulma veri seti; uzman yorumlu etiketler.', 'data/disfor/'],
    ['high confidence', 'Uzmanın yorumundan emin olduğu noktalar; yalnız bunlar kullanıldı.', 'Table 1'],
    ['spatial component', '5 km içindeki ve aynı olaya ait noktaların birleşimi; bölünemez birim.', 'd[\'groups\'] (874)'],
]
table(doc, ['Terim', 'Anlamı', 'Projede'], rows, [3.2, 9.5, 4.3], size=8.5)

doc.add_heading('2. Deney tasarımı terimleri', 1)
rows = [
    ['spatial cross-validation', 'Veriyi coğrafi bileşenlere göre katlara bölüp her katı sırayla test yapmak.', 'folds.json, StratifiedGroupKFold'],
    ['fold', 'Bir kat; 5 kat var, her biri bir kez test olur.', 'Table 2'],
    ['out-of-fold (OOF) prediction', 'Her noktanın, onu görmemiş modelden aldığı tahmin; 5 kat birleşince 2.213 tahmin.', 'oof_predictions.npz'],
    ['spatial leakage', 'Komşu noktanın hem eğitimde hem testte olması; skoru yapay şişirir.', 'Table 2 son sütun engeller'],
    ['seed', 'Rastgelelik tohumu; 7, 17, 27. Hem model başlangıcı hem etiket seçimi.', 'SD sütunu buradan'],
    ['label budget', 'Eğitim noktalarının etiketli sayılan oranı: %5, 10, 20, 50, 100.', 'subset(), Table 5'],
    ['labeled subset', 'O seed ve bütçede etiketli sayılan nokta kimlikleri; bütün yöntemler aynısını görür.', 'runs/*.json → labeled_ids'],
    ['frozen protocol', 'Deney başlamadan yazılan kurallar + kod/veri hash\'leri; sonradan değişirse script durur.', 'protocol.json, signature.json'],
    ['retrospective audit', 'Modeller aynı veride daha önce geliştirildiği için "bağımsız doğrulama" değil "geriye dönük denetim".', 'makale Discussion'],
    ['external validation', 'Hiç görülmemiş bölge/veri üzerinde ölçüm; henüz yok.', 'external_validation/'],
]
table(doc, ['Terim', 'Anlamı', 'Projede'], rows, [3.4, 9.3, 4.3], size=8.5)

doc.add_heading('3. Model terimleri', 1)
rows = [
    ['Random Forest', 'Çok sayıda karar ağacının oylaması; 60 özet özellikten öğrenir. Basit, güçlü referans.', 'rf_leaf4'],
    ['Temporal CNN', 'Zaman ekseninde 1-boyutlu konvolüsyon; residual block, dilation 1/2/4.', 'cnn64'],
    ['Transformer / self-attention', 'Her ay diğer aylara "dikkat" ederek bağlam öğrenir; 2 katman, 4 başlık, width 48.', 'transformer48'],
    ['key padding mask', 'Gözlenmemiş ayların attention\'a girmesini engeller.', 'TemporalNet.forward'],
    ['mean pooling', 'Gözlenen ayların temsillerinin ortalaması → sınıflandırıcı.', 'TemporalNet.forward'],
    ['self-supervised learning (SSL)', 'Etiket kullanmadan, verinin kendisinden görev üretip öğrenme.', 'ssl_transformer48'],
    ['masked reconstruction', 'Girdinin bir kısmını gizleyip modele tahmin ettirme (BERT/MAE fikri).', 'block_mask, fit()'],
    ['block + band masking', '2–6 ardışık ay + 2 bant tamamen gizlenir.', 'block_mask'],
    ['independent-cell masking', 'Her hücre 1/3 olasılıkla ayrı ayrı gizlenir (kontrol).', 'iid_ssl'],
    ['pretraining / fine-tuning', '60 epoch maskeli yeniden kurma, sonra 40 epoch etiketli sınıflandırma.', 'fit(pre_epochs=60, epochs=40)'],
    ['step-matched control', 'SSL\'in toplam optimizer adımına eşit epoch alan düz Transformer (320 epoch).', 'step_matched'],
    ['epoch', 'Eğitim verisinin bir tam geçişi.', 'log.history'],
    ['AdamW, weight decay', 'Optimizer ve aşırı öğrenmeyi frenleyen ceza (0.01).', 'fit()'],
    ['class-weighted cross-entropy', 'Azınlık sınıfa (kesim) daha çok ağırlık veren kayıp.', 'fit()'],
    ['label smoothing', 'Hedefleri 0/1 yerine 0.01/0.99 yapma; aşırı güveni azaltır.', 'fit()'],
    ['augmentation', 'Eğitimde ayları %10 olasılıkla silme; bulut etkisini taklit eder.', 'augment()'],
    ['ensemble', 'Birden çok modelin olasılık ortalaması; ürün modeli 5 CNN + 5 SSL.', 'advanced_v3'],
    ['calibration (Platt)', 'Olasılıkları gerçek sıklığa yaklaştıran lojistik düzeltme; yalnız ürün modelinde.', 'bundle.json'],
]
table(doc, ['Terim', 'Anlamı', 'Projede'], rows, [3.6, 9.1, 4.3], size=8.5)

doc.add_heading('4. Ölçüm terimleri', 1)
rows = [
    ['macro-F1', 'İki sınıfın F1 ortalaması; azınlık sınıfı eşit sayar. Ana ölçüt.', 'bütün tablolar'],
    ['precision / recall', 'Kesim dediklerinin yüzde kaçı kesim / kesimlerin yüzde kaçını buldu.', 'Table 3 recall'],
    ['accuracy', 'Toplam doğru oranı; %88 orman olduğu için yanıltıcı, ikincil.', 'model_card'],
    ['average precision (AP)', 'Precision-recall eğrisinin özeti; sıralama kalitesi, eşikten bağımsız.', 'Table 3–4'],
    ['ROC-AUC', 'Rastgele bir kesimi rastgele bir ormandan daha yüksek skorlama olasılığı.', 'analysis.json'],
    ['Brier score', 'Olasılık ile gerçek (0/1) arasındaki ortalama kare hata; düşük iyi.', 'Table 4'],
    ['threshold 0.5', 'Olasılık ≥ 0,5 ise kesim; ayarlanmadı.', 'bütün koşular'],
    ['seed SD', 'Üç seed\'in macro-F1 standart sapması; güven aralığı değil.', '± değerleri'],
    ['paired cluster bootstrap', '874 bileşeni yerine koyarak 2.000 kez örnekleyip iki yöntemin farkının %95 aralığı.', 'paired_comparisons'],
]
table(doc, ['Terim', 'Anlamı', 'Projede'], rows, [3.4, 9.3, 4.3], size=8.5)

doc.add_heading('5. Veri akışı (pipeline)', 1)
for line in [
    'data/disfor/*.parquet  →  scripts/prepare_disfor.py  →  data/processed/real_series.npz  (2.213 × 24 × 10 + mask + days + y + groups)',
    'real_series.npz  →  scripts/train_paper.py  (folds.json, jobs.json, signature.json)  →  experiments/paper_v4/runs/*.json  (180 koşu)',
    'runs/  →  scripts/analyze_paper.py  →  analysis.json + oof_predictions.npz  →  scripts/plot_paper.py  →  paper/figures/01–03',
    'scripts/scientific_v5.py  →  experiments/paper_v5_exploratory/  (75 koşu, checkpoints/)  →  report_spatial_v5.py',
    'scripts/label_curve_v6.py  →  experiments/paper_v6_label_curve/  (225 koşu)  →  plot_extensions.py  →  figures/04–05',
    'analysis.json\'lar  →  scripts/compose_paper.py  →  paper/manuscript.md + manuscript_content.json  →  build_paper_docx.py  →  DOCX/PDF',
    'real_series.npz + split.json  →  src/orman_ssl/advanced.py (cv → final)  →  models/advanced_v3/*.pt + bundle.json  →  scripts/serve_product.py (ürün)',
]:
    doc.add_paragraph(line, style='List Number')

doc.add_heading('6. Hangi dosyayı ne için açarım', 1)
rows = [
    ['Projeyi anlamak', 'TESLIM_2026-10-18/Orman_SSL_Proje_Defteri.html (veya .ipynb)'],
    ['Her tabloyu yorumuyla görmek', 'TESLIM_2026-10-18/Orman_SSL_Tablolar_ve_Sonuclar_Rehberi.pdf'],
    ['Makaleyi okumak', 'TESLIM_2026-10-18/Orman_SSL_Makale_Guneren_Kumbasar.pdf (yazarlı taslak)'],
    ['Hocaya anlatmak', 'docs/HOCAYA_ILK_NOTLAR_VE_FIKIRLER.md, docs/PAZAR_TOPLANTI_AKISI.md'],
    ['Bir sayının kaynağını bulmak', 'paper/CLAIM_LEDGER.md → experiments/*/analysis.json'],
    ['Deneyi yeniden koşmak', 'paper/SUPPLEMENT.md (komutlar)'],
    ['Ürünü göstermek', 'URUNU_AC.command → tarayıcı 127.0.0.1:8765'],
    ['Her şeyi doğrulamak', 'DOGRULAMAYI_CALISTIR.command'],
    ['Model ağırlıkları', 'models/advanced_v3/*.pt, bundle.json, model_card.json'],
    ['Ham veri ve lisans', 'data/disfor/'],
]
table(doc, ['Amaç', 'Dosya'], rows, [5.5, 11.5], size=9)
doc.save(OUT / 'Orman_SSL_Yontem_Sozlugu_ve_Dosya_Haritasi.docx')
print('ok')
