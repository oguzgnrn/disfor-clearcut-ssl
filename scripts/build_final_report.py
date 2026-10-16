"""Build the Turkish meeting report from measured, frozen local evidence.

Run with a Python environment containing python-docx. The final PDF is rendered
from this DOCX, so the editable and printable report share one source.
"""
import json
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/final'
A = json.loads((ROOT / 'experiments/paper_v4/analysis.json').read_text())
CARD = json.loads((ROOT / 'models/advanced_v3/model_card.json').read_text())
REFS = json.loads((ROOT / 'paper/references.json').read_text())
SUMMARY = {(r['budget'], r['method']): r for r in A['summary']}
NAMES = {'rf_leaf4': 'Random forest', 'cnn64': 'Zamansal CNN',
         'transformer48': 'Transformer', 'ssl_transformer48': 'SSL Transformer',
         'iid_ssl': 'Bağımsız hücre SSL', 'step_matched': 'Adım eşlenmiş Transformer',
         'mask_only': 'Yalnız gözlem maskesi', 'metadata_only': 'Yalnız konum yıl kampanya'}

def number(v, n=4):
    return f'{v:.{n}f}'.replace('.', ',')

def make_document():
    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.left_margin = s.right_margin = Cm(2.1)
    s.top_margin = Cm(1.9); s.bottom_margin = Cm(1.8)
    s.footer_distance = Cm(.8)
    normal = doc.styles['Normal']
    normal.font.name = 'DejaVu Sans'; normal.font.size = Pt(10)
    normal.paragraph_format.line_spacing = 1.12
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.widow_control = True
    for name, size in [('Title', 23), ('Subtitle', 12), ('Heading 1', 17), ('Heading 2', 11.5)]:
        st = doc.styles[name]
        st.font.name = 'DejaVu Sans'; st.font.size = Pt(size)
        st.font.color.rgb = RGBColor(0, 0, 0); st.font.underline = False
        st.font.bold = name != 'Subtitle'
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.space_before = Pt(12 if name.startswith('Heading') else 0)
        st.paragraph_format.space_after = Pt(8)
        for border in st.element.xpath('./w:pPr/w:pBdr'):
            border.getparent().remove(border)
    for name in ['Caption']:
        doc.styles[name].font.name = 'DejaVu Sans'
        doc.styles[name].font.size = Pt(8)
        doc.styles[name].font.color.rgb = RGBColor.from_string('44515A')
    f = s.footer.paragraphs[0]
    f.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = f.add_run('Orman SSL  |  Araştırma ve ürün raporu  |  ')
    r.font.size = Pt(8); r.font.color.rgb = RGBColor.from_string('58646A')
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); f._p.append(field)
    doc.core_properties.title = 'Uydu zaman serilerinden orman kesimi sınıflandırması'
    doc.core_properties.subject = 'Nida Hocayla bilimsel değerlendirme için araştırma ve ürün sonuçları'
    doc.core_properties.author = ''
    return doc

DOC = make_document()
TEXT = []

def p(text, bold=False):
    para = DOC.add_paragraph()
    para.add_run(text).bold = bold
    TEXT.append(text)
    return para

def h(text, level=2):
    DOC.add_paragraph(text, f'Heading {level}')
    TEXT.append('#' * (level + 1) + ' ' + text)

def page(title):
    DOC.add_page_break(); h(title, 1)

def table(headers, rows, widths):
    t = DOC.add_table(rows=1, cols=len(headers)); t.autofit = False
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, width in enumerate(widths): t.columns[j].width = Cm(width)
    for j, value in enumerate(headers): t.rows[0].cells[j].text = str(value)
    for values in rows:
        cells = t.add_row().cells
        for j, value in enumerate(values): cells[j].text = str(value)
    for i, row in enumerate(t.rows):
        pr = row._tr.get_or_add_trPr(); pr.append(OxmlElement('w:cantSplit'))
        if i == 0: pr.append(OxmlElement('w:tblHeader'))
        for j, cell in enumerate(row.cells):
            cell.width = Cm(widths[j]); cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp = cell._tc.get_or_add_tcPr()
            borders = OxmlElement('w:tcBorders')
            for side in ['top', 'left', 'bottom', 'right']:
                el = OxmlElement('w:' + side)
                for key, val in [('val', 'single'), ('sz', '4'), ('color', 'D9D9D9')]: el.set(qn('w:' + key), val)
                borders.append(el)
            cp.append(borders)
            margins = OxmlElement('w:tcMar')
            for side in ['top', 'left', 'bottom', 'right']:
                el = OxmlElement('w:' + side); el.set(qn('w:w'), '85'); el.set(qn('w:type'), 'dxa'); margins.append(el)
            cp.append(margins)
            fill = '233C49' if i == 0 else ('EFF3F5' if i % 2 == 0 else 'FFFFFF')
            shade = OxmlElement('w:shd'); shade.set(qn('w:fill'), fill); cp.append(shade)
            for para in cell.paragraphs:
                para.paragraph_format.space_after = Pt(1); para.paragraph_format.space_before = Pt(1)
                para.paragraph_format.line_spacing = 1.05
                if j > 0: para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.font.size = Pt(8.5); run.bold = i == 0
                    run.font.color.rgb = RGBColor.from_string('FFFFFF' if i == 0 else '182B33')
    DOC.add_paragraph().paragraph_format.space_after = Pt(1)
    TEXT.append('| ' + ' | '.join(headers) + ' |')
    TEXT.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
    TEXT.extend('| ' + ' | '.join(map(str, r)) + ' |' for r in rows)

def figure(path, caption, width=16.2):
    para = DOC.add_paragraph(); para.paragraph_format.keep_with_next = True
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(); inline = run.add_picture(str(ROOT / path), width=Cm(width))
    inline._inline.docPr.set('descr', caption)
    DOC.add_paragraph(caption, 'Caption')
    TEXT.extend([f'![{caption}](../{path})', caption])


DOC.add_paragraph('Uydu zaman serilerinden orman kesimi sınıflandırması', 'Title')
DOC.add_paragraph('Araştırma ve ürün sonuç raporu', 'Subtitle')
p('Nida Hocayla araştırma görüşmesi için  |  27 Eylül 2026, uzantılarla güncellenmiş 16 Ekim 2026')
h('Çalışmanın sonucu')
p('Gerçek Sentinel-2 gözlemleriyle, iki yıllık bir zaman penceresinde orman kesimi olup olmadığını sınıflandıran bir araştırma ve çalışan yerel uygulama hazırladım. Veri hazırlama, model eğitimi, coğrafi değerlendirme ve tahmin çıktıları aynı proje içinde yeniden çalıştırılabiliyor. İngilizce makale, deney kayıtları ve Türkçe ürün kılavuzu teslim dosyasına eşlik ediyor.')
p('Araştırmanın ana sonucu karşılaştırma tasarımıyla ilgili: az etiketle ön eğitim kısa Transformer eğitimine göre fayda sağlıyor; ancak yaklaşık eşit optimizasyon adımı verilen denetimli model daha yüksek macro-F1 elde ediyor. Bu sonuç, ön eğitimin yararını tartışırken güçlü bir denetimli karşılaştırmanın gerekli olduğunu gösteriyor.')
table(['Somut çıktı', 'Doğrulanmış kapsam'], [
    ['Gerçek veri', '2.213 konum ve 874 mekânsal bileşen'],
    ['Bilimsel deney', '5 coğrafi kat ve 3 seed ile 180 eğitim'],
    ['Çalışan model', '10 üyeli CNN ve SSL Transformer birleşimi'],
    ['Yerel ürün', 'Örnek inceleme ve ham veriden gerçek çıkarım'],
    ['Teslim', 'Türkçe rapor ve İngilizce makale ile kod ve veri']
], [5.4, 11.4])
h('Bu teslimin kullanım amacı')
p('Dosya, hocayla yöntem ve yayın yönünü somut sonuçlar üzerinden tartışmak için hazırlandı. Ürün uyumlu veride yerel tahmin üretir; mevcut başarı ölçümleri Avrupa kaynaklı DISFOR verisinden gelir. Türkiye’de bağımsız saha başarımı henüz ölçülmedi. Bu ayrım, araştırma sonuçlarının uygulamaya aktarılmasında temel sınırdır.')
p('Görüşmeye ürün ekranıyla başlanabilir; ardından bu rapordaki sonuç tabloları ve İngilizce makale üzerinden yöntem tartışılabilir. Gerçek yazar, kurum, katkı ve fon bilgileri araştırmacılarla kesinleştirilecek; dosyada bu bilgiler varsayılmadı.')

page('Araştırma sorusu ve literatürdeki yeri')
p('Uydu zaman serilerinde etiketler sınırlı olduğunda, etiketsiz gözlemlerden öğrenilen temsil sınıflandırmayı iyileştirebilir. İncelediğim soru, bu iyileşmenin daha fazla eğitim adımı verilen denetimli bir model karşısında sürüp sürmediğidir. İkinci soru, zamansal blok ve bant maskelemesinin bağımsız hücre maskelemesine göre ölçülebilir bir üstünlük sağlayıp sağlamadığıdır.')
h('Önceki çalışmalarla ilişki')
table(['Çalışma', 'Bu projeyle ilişkisi'], [
    ['Zerveas ve ark. 2021 [3]', 'Maskeli çok değişkenli zaman serisi öğrenmesi yöntemsel dayanak.'],
    ['Zhang ve ark. 2025 [2]', 'Orman bozulmasında Sentinel-1 ve Sentinel-2 ile farklı çok modlu görev.'],
    ['Presto 2024 [7]', 'Ön eğitimli piksel zaman serisi modelleri için ilgili referans.'],
    ['Roberts ve ark. 2017 [4]', 'Yapılandırılmış veride uygun çapraz doğrulamanın gerekçesi.'],
    ['DISFOR 2026 [1]', 'Kaynak veri ve mevcut yorumlanmış orman bozulması etiketleri.']
], [5.4, 11.4])
p('Maskeli öğrenme, Transformer ve zamansal CNN yeni icatlar olarak sunulmuyor. Katkı; aynı konumlar, aynı etiket alt kümeleri ve sabit coğrafi katlar üzerinde yöntemleri karşılaştıran, eğitim adımı ve eksik gözlem kontrollerini birlikte raporlayan yeniden üretilebilir bir ampirik incelemedir. Temel model karşılaştırmalarının yanında olumsuz bulgular da korunmuştur.')
h('Karşılaştırmanın sınırı')
p('Zhang çalışmasındaki çok modlu yöntem burada yeniden uygulanmadı; Presto ile doğrudan bir başarı yarışı yapılmadı. Veri, görev ve değerlendirme tasarımları farklı olduğundan yayınlar arasındaki F1 değerleri tek tabloda üstünlük sıralaması olarak kullanılmıyor. Resampling augmentation çalışması [8] ise zaman serisi kontrolleri için ilgili bir yöntemsel bağlam sunuyor.')
p('Model tarifleri daha önce aynı kaynak veride geliştirilmişti. Son deneyin protokolü ve kod hash’leri yeni koşuların skorları üretilmeden sabitlendi; buna karşın bütün çalışma geriye dönük bir denetimdir. Yeni katlar, geçmişteki veri kümesi düzeyindeki uyarlamaları ortadan kaldırmaz. Bu nedenle katkıyı şeffaf ve kontrollü karşılaştırma olarak konumlandırıyorum.')

page('Veri hazırlama ve coğrafi ayrım')
p('DISFOR’un sabit kaynak sürümündeki 3.822 konumdan yüksek güvenli, iki yıllık zaman penceresi kurulabilen ve yeterli açık ayı bulunan örnekler seçildi. Son görev bozulmamış orman ile kesim ayrımıdır. Etiketler kaynak veri üreticilerinin yorumlarından gelir; bu proje için yeni arazi ölçümü yapılmadı. Veri makalesi kaynak denetimi tarihinde incelemedeki ön baskıdır [1].')
table(['Ardışık seçim adımı', 'Konum'], [
    ['Kaynak tablo', '3.822'], ['Düşük yorum güveni nedeniyle dışlanan', '598'],
    ['Uygun iki yıllık pencere bulunamayan', '606'], ['Açık ay sayısı yetersiz', '116'],
    ['İkili göreve alınmayan yangın örnekleri', '289'], ['Kalan orman ve kesim', '1.937 ve 276']
], [13, 3.8])
p('Her örnek 24 ay ve 10 bant içerir. Source clear ile SCL 4 veya 5 koşulunu sağlayan gözlemlerin aylık medyanı alınır; her yılda en az altı gözlenmiş ay gerekir. Eksik değerler enterpole edilmez, ayrı maskeyle tutulur. Kaynak DN ölçeği korunur; standardizasyon yalnız dış eğitim katında gözlenmiş değerlerle hesaplanır. Etiket veya olay tarihi sınıflandırıcıya girdi olarak verilmez.')
h('Aynı bölgenin iki tarafta görünmesini önleme')
p('Beş kilometre içindeki noktalar ve aynı kaynak bozulma olayını paylaşan uygun kampanya kayıtları bir grafikte birleştirilir. Ortaya çıkan 874 bağlı bileşen parçalanmadan beş coğrafi kata atanır. Eğitim ve test arasındaki en kısa uzaklık 5,0011 km’dir. Denetlenen 215 olay anahtarı katlar arasında bölünmez; birebir aynı gözlem dizisi bulunmamıştır.')
p('Bu tasarım yakın nokta ve aynı olay sızıntısını belirlenen kurala göre önler. Bütün mekânsal bağımlılığın yok olduğunu kanıtlamaz. Kampanya 2’deki örnekleme katmanları olay kimliği olarak değerlendirilmez. Tam seçim kuralları ve kaynak sürümü, yöntem eki ile veri manifestlerinde kayıtlıdır.')

page('Eğitim düzeni ve yeniden üretilebilir deney')
p('Ana deney dört yöntemi yüzde 20 ve yüzde 100 etiket bütçesinde karşılaştırır. Her yöntem beş coğrafi katta ve üç seed ile çalışır. Aynı kat ve seed içindeki yöntemler birebir aynı etiketli konumları kullanır; böylece sonuç farkı farklı etiket örneklemlerinden kaynaklanmaz. Bütün dış test konumları ön işleme ve ön eğitim dışında tutulur.')
table(['Yöntem', 'Eğitim tarifi'], [
    ['Random forest', '500 ağaç ve 60 zamansal özet özellik'],
    ['Zamansal CNN', '64 kanal genişliği ve 3 artık blok ile 40 epoch'],
    ['Transformer', '48 genişlik ve 2 katman ile 40 epoch'],
    ['SSL Transformer', '60 maskeli ön eğitim ve 40 sınıflandırma epoch’u'],
    ['Adım eşlenmiş kontrol', 'Yüzde 20 etikette 320 denetimli epoch'],
    ['Diğer kontroller', 'Bağımsız hücre maskesi ve iki bilgi kaynağı kontrolü']
], [5.2, 11.6])
p('Ana düzen 120 eğitimden, yüzde 20 etiketteki dört ek kontrol 60 eğitimden oluşur. Toplam 180 koşulun tamamı tutulmuştur. Son bilimsel deneyde erken durdurma, test skoruna göre seed seçimi, kalibrasyon veya karar eşiği optimizasyonu yoktur; eşik 0,5’tir. Etiket bütçesi sınıf içinden seçildiği için bu düzen kontrollü bir etiket azlığı benzetimidir; gerçek bir anotasyon maliyeti ölçümü değildir.')
h('Ölçütlerin hesaplanması')
p('Her seed için beş katın ayrılmış tahminleri birleştirilerek 2.213 konum üzerinde macro-F1 hesaplanır. Tablolardaki ortalama ve standart sapma bu üç seed’den gelir. Macro-F1, iki sınıfın F1 değerlerini eşit ağırlıkla birleştirir; örneklerin yüzde kaçının doğru bulunduğuyla aynı değildir. AP, average precision ölçütüdür.')
p('Ana yöntem farkı için 874 mekânsal bileşen 2.000 kez eşlenmiş bootstrap ile yeniden örneklenir. Aynı çekiliş her iki yönteme uygulanır ve üç seed birlikte korunur. Bu aralıklar sabit veri, katlar ve mevcut eğitimler koşulundadır; yeni bir veri kümesinde yeniden eğitim belirsizliğini veya geçmiş model geliştirme etkisini içermez.')

page('Ana sonuçlar')
rows = []
for budget in [.2, 1.]:
    for method in ['rf_leaf4', 'cnn64', 'transformer48', 'ssl_transformer48']:
        r = SUMMARY[budget, method]
        rows.append([f'%{int(budget*100)}', NAMES[method], f"{number(r['macro_f1_mean'])} ± {number(r['macro_f1_std'])}", number(r['pr_auc_mean']), number(r['recall_mean'])])
table(['Etiket', 'Yöntem', 'Macro F1 ve SD', 'AP', 'Kesim duyarlılığı'], rows, [1.3, 4.7, 4.2, 2.3, 4.3])
p('Yüzde 20 etikette SSL Transformer 0,8690, kısa denetimli Transformer 0,8322 macro-F1 elde etti. Tam hassasiyetli değerlerden hesaplanan fark 0,0368; koşullu yüzde 95 aralık [0,0245; 0,0506]. Aynı bütçede CNN’in ortalaması 0,8721’dir. SSL ile CNN farkının aralığı sıfırı içerdiği için genel bir SSL üstünlüğü sonucu çıkarılmıyor.')
figure('paper/figures/01_primary.png', 'Şekil 1. Sabit coğrafi katlardaki ayrılmış tahminlerin sonuçları. Büyük noktalar üç seed ortalaması, küçük noktalar seed sonuçları; hata çubukları standart sapmadır.', 15.7)
p('Tam etikette CNN, Transformer ve SSL Transformer ortalamaları 0,9285 ile 0,9299 arasındadır. Bu küçük farklar, her veri kümesi ve bölgede en iyi mimarinin belirlendiği anlamına gelmez. Sayılar bağımsız Türkiye saha başarımı olarak kullanılmamalıdır.')

page('Eğitim bütçesi ve maskeleme kontrolleri')
p('Daha uzun denetimli eğitim, ana bulgunun yorumunu değiştiriyor. Yaklaşık aynı toplam optimizasyon adımını alan Transformer 0,8987 macro-F1’e ulaşıyor. SSL eksi bu kontrol farkı -0,0297; koşullu yüzde 95 aralık [-0,0430; -0,0179]. Bu nedenle kısa eğitimli karşılaştırmada görülen yarar, ön eğitimin benzer ölçüde uzatılan her denetimli öğrenmeden daha iyi olduğunu göstermiyor.')
figure('paper/figures/02_controls.png', 'Şekil 2. Yüzde 20 etiketle kontroller ve SSL eksi karşılaştırıcı farkları. Aralıklar mekânsal bileşen bootstrap’ından gelir. Kısa Transformer dışındaki karşılaştırmalar keşifseldir.', 16.2)
h('Sonuçtan çıkarılabilecek yorum')
p('Adım eşleştirme FLOP, duvar saati veya etiketli örneğe maruz kalmayı eşitlemez. Uzun denetimli koşul aynı etiketleri daha çok kez görür. Bulgumuz ek optimizasyonun tek nedensel açıklama olduğunu kanıtlamıyor; kullanılan karşılaştırıcının bilimsel yorumu değiştirdiğini gösteriyor. Ayrıca SSL’nin AP değeri 0,8636 iken uzun denetimli kontrolünki 0,8445’tir; sıralama başarısı ile sabit eşikteki sınıflandırma başarısı aynı yönde değişmek zorunda değildir.')
p('Bağımsız hücre SSL 0,8609 elde etti. Yapılandırılmış maskelemenin 0,0080 farkına ait aralık sıfırı içeriyor. Yalnız eksik gözlem maskesi kullanan kontrol 0,5515, yalnız konum yıl kampanya kullanan kontrol 0,6455 macro-F1’e ulaşıyor. Bu sonuçlar örnekleme bağlamının tahmin edici bilgi taşıdığını gösterir; spektral modeldeki nedensel katkı yüzdesini ölçmez.')

page('Hatalar ve çalışan modelin davranışı')
p('Genel ortalama bütün alt grupları temsil etmiyor. Mevcut ayrılmış tahminlerin yıl ve kaynak kampanyasına göre sonradan incelenmesi, tam etiketli CNN’in 2022 grubunda 0,8188 macro-F1’e indiğini gösteriyor. Bu grupta 265 konum ve yalnızca 12 kesim var. Bu tablo ileri zamanlı veya kampanya dışı doğrulama yerine betimsel hata incelemesidir.')
table(['Hedef yıl', 'Konum', 'Kesim', 'CNN macro F1'], [
    ['2018', '645', '68', '0,9168'], ['2019', '388', '76', '0,9426'],
    ['2020', '328', '65', '0,9418'], ['2021', '286', '40', '0,9444'],
    ['2022', '265', '12', '0,8188'], ['2023', '301', '15', '0,9279']
], [4.2, 4.2, 4.2, 4.2])
p('CNN veya SSL modelinin üç seed’inden en az ikisinde yanlış sınıflandırılan 81 konum inceleme listesine alındı. Etiketleri model çıktısına bakılarak değiştirilmedi. GeoJSON ve hata tablosu, kaynak gözlemlerle insan incelemesini mümkün kılar; liste yeni ve düzeltilmiş bir gerçek etiket kümesi değildir.')
h('Üründeki modelin ayrı değerlendirmesi')
p('Yerel uygulama advanced_v3 modelini çalıştırır: beş CNN ve beş SSL Transformer üyesi, eğitim içindeki coğrafi seçimle belirlenmiş ve geliştirme verisinde kalibre edilmiştir. Bu birleşim paper_v4’teki tekil modellerden farklıdır. Daha önce incelenmiş 486 örnekte macro-F1 0,9187 ve AP 0,9359 elde etmiştir.')
table(['Gerçek sınıf', 'Orman tahmini', 'Kesim tahmini'], [
    ['Orman', '448', '0'], ['Kesim', '10', '28']
], [8.4, 4.2, 4.2])
p('38 kesimin 28’i bulundu; 10’u kaçırıldı. Bu 448 orman örneğinde yanlış kesim alarmı gözlenmemesi, yeni bölgede sıfır yanlış alarm garantisi değildir. Kalibre edilmiş skorlar da yeni coğrafyada doğrulanmış güven olarak yorumlanmamalıdır. Üyeler arası farklılık yalnız model anlaşmazlığı göstergesidir.')

page('Yerel ürünü kullanma ve gösterim')
p('Uygulama, eğitilmiş modeli araştırma görüşmesinde çalıştırılabilir hale getirir. Başlangıçta 486 örneğin kayıtlı çıktıları, konum görünümü ve gözlem serileri açılır. Kullanıcı bir örneği seçip aylık bant değerlerini, gözlenmeyen ayları, kesim skorunu ve kalite durumunu inceleyebilir. Nokta görünümü bir örnek dağılımıdır; kesintisiz ülke orman haritası değildir.')
h('Görüşmede beş dakikalık akış')
for text in [
    '1. URUNU_AC.command dosyasını çalıştır ve yerel arayüzü aç. Hazır örnek kümesinin DISFOR’dan geldiğini ve gerçek modeli kullandığını belirt.',
    '2. Kesim tahminlerini filtrele. Bir örneğin 24 aylık gözlem serisini aç; eksik ayları ve kalite bilgisini göster.',
    '3. Ayrı değerlendirme bölümünde gerçek etiketi ve tahmini karşılaştır. Kaçırılan bir kesim örneğini de göster; başarıyı yalnız doğru örneklerle anlatma.',
    '4. Örnek veride analizi çalıştır düğmesiyle ham gözlemleri aylık girdiye dönüştürüp kayıtlı modeli gerçekten çalıştır. Bu işlem modeli yeniden eğitmez.',
    '5. JSON veya GeoJSON çıktısını indir. Sonra araştırma sonuçlarına geçerek ürünün 486 örnekli değerlendirmesiyle makalenin 2.213 konumlu çapraz doğrulamasını ayır.'
]: p(text)
h('Yeni gözlemle çalışma')
p('Özel veri için komut satırı akışı vardır. Gözlem tablosu sample_id, timestamps, clear, SCL ve on Sentinel-2 bandını; pencere dosyası id, sample_id ve target_year alanlarını içermelidir. Harita için WGS84 lon ve lat eklenir. Etiket sütunu gerekmez. Kaynak ve DN işleme geçmişi --source ile belirtilir. Ayrıntılı alanlar docs/VERI_SOZLESMESI.md ve ürün kılavuzundadır.')
p('Her pencere iki tam takvim yılını kapsar; hedef ikinci yıldaki kesimdir. Bu nedenle ürün, tek bir uydu görüntüsünden anlık kesim algılayan veya erken uyarı veren bir servis değildir. Kalite bayrağı yalnız aylık gözlem desteğini denetler; yeni bölgenin ekolojik ve radyometrik uyumunu doğrulamaz.')
p('Sunucu yalnız bu bilgisayardaki 127.0.0.1 adresinde çalışır. Model veya gözlemler harici bir sunucuya gönderilmez. İnternet olmadan hazır veri ve kayıtlı modelle gösterim yapılabilir; ilk ortam kurulumu paket indirme gerektirebilir.')

page('Tekrar üretim ve teslim dosyaları')
p('Araştırma sonucunu yalnız tablodan okumakla sınırlamayan bir kanıt zinciri kuruldu: sabit ham dosyalar, işlenmiş örnekler, kat ve etiket kimlikleri, koşu kayıtları, ayrılmış tahminler ve yeniden hesaplanan ölçütler. Ham Parquet dosyalarından ayrı bir klasörde kurulan 2.213 örneğin tüm dizileri ve örnek manifesti birebir eşleşti.')
p('Kompakt bilimsel paket başka bir klasöre açılarak bir SSL koşulu sıfırdan yeniden eğitildi. Aynı ortamda bütün tahmin olasılıkları kayıtlı koşulla aynı çıktı. Bu denetim tek bir koşunun tekrar üretimidir; bütün 180 koşulun bu son kontrolde yeniden eğitildiği iddia edilmiyor. Farklı donanım ve kitaplıklarda küçük sayısal farklar oluşabilir.')
table(['Teslim', 'İçerik ve kullanım'], [
    ['Hocaya sunum paketi', 'Türkçe sonuç raporu ve İngilizce makale ile çevrimdışı araştırma özeti.'],
    ['Tam proje paketi', 'Ürün, ham ve işlenmiş veri, model ağırlıkları, testler ve tüm deney kayıtları.'],
    ['Paper paketi', 'Makale deneyini tekrar üretmek için işlenmiş veri ve 180 koşul kaydı.'],
    ['Nihai model paketi', '10 üyeli model ve etiketsiz örnek NPZ ile bağımsız çıkarım.']
], [5.3, 11.5])
h('Hangi kontrol neyi kanıtlıyor')
p('Otomatik testler girdi sözleşmesi, eksik gözlem işleme, etiket ayrımı ve değerlendirme sınırlarını kontrol eder. Model kabul denetimi üye dosyalarının hash’lerini, eğitim ve kalibrasyon kimliklerini ve 486 örnekte çıkarım eşitliğini denetler. Bilimsel denetim 180 kayıttan tahminleri birleştirir; macro-F1 ve AP değerlerini yeniden hesaplar. Güncel test sayısı ve son çalıştırmalar reports/final_delivery_verification.json dosyasında tutulur.')
p('ZIP arşivleri dosya boyutu, CRC, yol güvenliği ve SHA-256 manifestiyle doğrulanır. Paket bütünlüğü verinin bilimsel doğruluğundan farklı bir kontroldür. Deney modelleri ve protokolü korunmuş; son teslim çalışması ürün, raporlama ve doğrulama katmanını tamamlamıştır.')
h('Kaynak ve kullanım koşulları')
p('DISFOR kaynak lisansı ve atıfları pakette korunur. Yeni proje kodunun yayın lisansı araştırmacılarla seçilecektir. Yapay zekâ; kodlama, analiz denetimi ve rapor yazımında kullanılmıştır. Nihai bilimsel sorumluluk, yazarlık, kurum ve fon beyanları gerçek katkılara göre belirlenmelidir. Hiçbir dosya gönderilmedi veya kamuya yayımlanmadı.')

V5 = ROOT / 'experiments/paper_v5_exploratory/analysis.json'
V6 = ROOT / 'experiments/paper_v6_label_curve/analysis.json'
if V5.exists() or V6.exists():
    page('Uzantılar: etiket bütçesi eğrisi ve mekânsal yarıçap')
    p('Ana deney dondurulduktan sonra iki ek deney ayrı protokollerle ilan edilip koşuldu. İkisi de paper_v4 dosyalarını ve ürün modelini değiştirmez; aynı DISFOR kohortu üzerinde geriye dönük analizlerdir ve dış doğrulama değildir.')
    if V6.exists():
        v6 = json.loads(V6.read_text())
        if v6.get('status') == 'complete_verified':
            s6 = {(r['budget'], r['method']): r for r in v6['summary']}
            p6 = {(r['budget'], r['comparator']): r for r in v6['paired_comparisons']}
            h('Etiket bütçesi eğrisi (paper_v6)')
            p(f"İlk araştırma planındaki %5 ve %10 etiket koşulları ile %50 koşulu, paper_v4'ün aynı beş katı, üç seed'i, iç içe etiket tahsisi ve tarifleriyle {v6['fits']} ek koşu olarak eğitildi. %5 etikette bir katın etiketli eğitim kümesi yaklaşık 90 konumdur ve bunların sadece 11–12'si kesimdir; bu yüzden düşük bütçelerde belirsizlik büyüktür.")
            rows = []
            for b in [.05, .1, .2, .5, 1.]:
                row = [f"%{int(round(b*100))}"]
                for m in ['rf_leaf4', 'cnn64', 'transformer48', 'ssl_transformer48', 'step_matched']:
                    r = s6.get((b, m)) or SUMMARY.get((b, m))
                    row.append(number(r['macro_f1_mean']) + ' ± ' + number(r['macro_f1_std']) if r else '—')
                rows.append(row)
            table(['Etiket', 'RF', 'CNN', 'Transformer', 'SSL', 'Adım eşlenmiş'], rows, [1.8, 3.0, 3.0, 3.0, 3.0, 3.0])
            p(f"SSL eksi kısa Transformer farkı: %5'te {number(p6[.05,'transformer48']['mean_difference'])}, %10'da {number(p6[.1,'transformer48']['mean_difference'])}, %50'de {number(p6[.5,'transformer48']['mean_difference'])}. SSL eksi adım eşlenmiş Transformer farkı: %5'te {number(p6[.05,'step_matched']['mean_difference'])}, %10'da {number(p6[.1,'step_matched']['mean_difference'])}, %50'de {number(p6[.5,'step_matched']['mean_difference'])}. Aralıklar makalenin Bölüm 5.1 ve Tablo 5'inde; %20 ve %100 satırları paper_v4'ün dondurulmuş sonuçlarıdır.")
            if (ROOT / 'paper/figures/04_label_curve.png').exists():
                figure('paper/figures/04_label_curve.png', 'Şekil: Etiket bütçesi eğrisi. Noktalar üç seed ortalaması, çubuklar seed standart sapması; güven aralığı değildir.')
    if V5.exists():
        v5 = json.loads(V5.read_text())
        if v5.get('status') == 'complete_verified':
            s5 = {(r['radius_km'], r['method']): r for r in v5['summary']}
            h('Mekânsal gruplama yarıçapı duyarlılığı (paper_v5)')
            p('Aynı kohort 5, 10 ve 20 km yarıçapla yeniden gruplanıp beş yöntem yalnız seed 7 ve %20 etiketle yeniden eğitildi (75 koşu, bütün ağırlıklar saklandı). Yarıçap büyüdükçe bileşenler birleşir: 874 → 205 → 54. Bu tek seed, betimsel bir analizdir.')
            table(['Yarıçap', 'Bileşen', 'RF', 'CNN', 'Transformer', 'SSL', 'Adım eşlenmiş'],
                  [[f'{r} km', s5[r,'rf_leaf4']['groups']] + [number(s5[r, m]['macro_f1']) for m in ['rf_leaf4','cnn64','transformer48','ssl_transformer48','step_matched']] for r in [5, 10, 20]],
                  [1.6, 1.6, 2.6, 2.6, 2.6, 2.6, 3.2])
            p(f"5 km'de adım eşlenmiş denetimli model önde ({number(s5[5,'step_matched']['macro_f1'])} / SSL {number(s5[5,'ssl_transformer48']['macro_f1'])}); 20 km'de SSL en iyi tarif ({number(s5[20,'ssl_transformer48']['macro_f1'])} / adım eşlenmiş {number(s5[20,'step_matched']['macro_f1'])} / CNN {number(s5[20,'cnn64']['macro_f1'])}). Yani ana deneydeki 'uzun denetimli model SSL'yi geçer' bulgusu 5 km tasarımına özgüdür; eğitim ve test bölgeleri daha sert ayrılınca ön eğitimli temsil daha az bozulur. Bunu doğrulamak için ek seed'ler ve kampanyalardan bağımsız tanımlanmış dış bölgeler gerekir.")
            if (ROOT / 'paper/figures/05_radius.png').exists():
                figure('paper/figures/05_radius.png', 'Şekil: Yarıçap duyarlılığı, %20 etiket, yalnız seed 7. Her çubuk tek bir birleştirilmiş macro-F1 değeridir.')

page('Bilimsel değerlendirme ve sonraki karar')
p('Bu teslimde gerçek model eğitimi, kontrollü karşılaştırma, olumsuz bulguların raporlanması ve çalışan çıkarım ürünü tamamlandı. Araştırma sorusu ve sonucu hocayla tartışılabilecek kadar somut. Yayın yönünü belirleyecek esas ek çalışma, yeterli kesim desteği olan ve geliştirme sürecinde kullanılmamış bir değerlendirme kümesidir.')
h('Bağımsız değerlendirme için uygulanabilir sıra')
p('Önce hedef kullanım tanımlanmalı: iki yıllık pencere içinde orman kesimi sınıflandırması. Bölge ve dönem, model skorları görülmeden seçilmeli. Kaynak verinin hakları, işleme ölçeği, bantları ve gözlem takvimi mevcut veri sözleşmesiyle karşılaştırılmalı. Ardından etiketleyicinin model skorunu görmediği bir yorumlama düzeni ve belirsiz örnekler için ortak karar süreci kurulmalı.')
p('Örneklem büyüklüğü istenen kesim duyarlılığı ve yanlış alarm belirsizliğine göre önceden belirlenmeli; aynı olaydan gelen yakın noktalar bağımsız örnek sayılmamalı. Model ve karar eşiği değerlendirmeden önce dondurulmalı. Sonuçta macro-F1, AP, kesim duyarlılığı, yanlış alarm sayıları ve olay grubu belirsizliği birlikte raporlanmalı. Temsil edici bir harita örneklemi kurulmadıkça nokta precision değeri ülke ölçeğine taşınmamalı.')
h('Mevcut kullanılmamış veri neden yeterli değil')
p('DISFOR içinde önceki konumları, ortak olayları ve beş kilometre komşuluklarını dışlayan taramada 111 uygun pencere kaldı. Bunların 110’u orman, yalnız biri kesim. Bu destekle bağımsız kesim başarımı ölçülmedi ve skor üretilmedi. Üstelik aynı kaynaktaki yeni noktalar da bağımsız saha toplamasıyla aynı kanıt düzeyinde değildir.')
h('Hocayla netleştirilecek karar')
p('Önerim, mevcut çalışmayı eğitim bütçesine duyarlı SSL karşılaştırması olarak konumlandırmak ve bu soruya uygun bağımsız bir veri kaynağını birlikte seçmek. Ürün, yeni veri protokolü kesinleştikten sonra aynı girdileri işlemeyi ve hataları incelemeyi kolaylaştıracak hazır araştırma aracı olarak kullanılabilir. Sentinel-1 füzyonu veya temel model karşılaştırması seçilirse, yeni sürüm ve önceden tanımlı hipotezle ayrı deney olmalıdır.')
p('Toplantıda beklenen karar; yayın kapsamı, bağımsız doğrulama verisi ve fiilî katkılara göre araştırmacı rolleridir. Kabul, yeni mimari veya Türkiye’de doğrulanmış başarı sözü verilmiyor. Eldeki bulgu ve çalışan sistem, bu kararları varsayımlar yerine somut kanıtlarla vermeyi sağlar.')

page('Kaynakça ve kanıt dosyaları')
for i, r in enumerate(REFS, 1):
    url = 'https://doi.org/' + r['doi'] if r.get('doi') else r['url']
    text = f"[{i}] {r['authors']} ({r['year']}). {r['title']}. {r['venue']}. {url}"
    para = p(text)
    para.paragraph_format.keep_together = True
    para.paragraph_format.space_after = Pt(9)
    for run in para.runs: run.font.size = Pt(8.1)
h('Sayısal kanıtların adresi')
for text in [
    'Ana tablolar ve fark aralıkları: experiments/paper_v4/analysis.json. Kat ve koşu kayıtları: aynı dizindeki folds.json, jobs.json ve runs/.',
    'Alt grup ve hata analizi: paper/ERROR_AUDIT.md ve experiments/paper_v4/support_error_audit.json. İnceleme listesi: review_candidates.geojson.',
    'Ürün modeli ve ayrı değerlendirmesi: models/advanced_v3/model_card.json ve experiments/advanced_v3/evaluation.json.',
    'Tekrar üretim: paper/SUPPLEMENT.md. Kaynak denetimi: docs/NIHAI_BILIMSEL_DENETIM.md. Güncel teslim doğrulaması: reports/final_delivery_verification.json.'
]:
    para = p(text)
    for run in para.runs: run.font.size = Pt(8.5)

OUT.mkdir(parents=True, exist_ok=True)
DOC.save(OUT / 'Orman_SSL_Arastirma_ve_Urun_Raporu.docx')
markdown = '# Uydu zaman serilerinden orman kesimi sınıflandırması\n\n'
for i, block in enumerate(TEXT):
    previous_table = i > 0 and TEXT[i - 1].startswith('| ')
    separator = '\n' if previous_table and block.startswith('| ') else '\n\n'
    markdown += separator + block
(ROOT / 'docs/ARASTIRMA_VE_URUN_RAPORU.md').write_text(markdown.strip() + '\n')
print(OUT / 'Orman_SSL_Arastirma_ve_Urun_Raporu.docx')
