"""Build the meeting brief from measured results using the bundled PDF runtime."""
import json
import os
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Image,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
root=Path(__file__).resolve().parents[1]
fonts=Path(os.environ.get('ORMAN_FONT_DIR',str(root/'assets/fonts')))
pdfmetrics.registerFont(TTFont('DV',str(fonts/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DVB',str(fonts/'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DVB',italic='DV',boldItalic='DVB')
INK=colors.HexColor('#183d31');MUTED=colors.HexColor('#607068');LIGHT=colors.HexColor('#eaf0e7');AMBER=colors.HexColor('#fff0dc')
styles={
'title':ParagraphStyle('title',fontName='DVB',fontSize=32,leading=39,textColor=INK,spaceAfter=20),
'h1':ParagraphStyle('h1',fontName='DVB',fontSize=22,leading=29,textColor=INK,spaceAfter=16),
'h2':ParagraphStyle('h2',fontName='DVB',fontSize=12,leading=17,textColor=INK,spaceBefore=12,spaceAfter=7),
'p':ParagraphStyle('p',fontName='DV',fontSize=10,leading=15,textColor=INK,spaceAfter=9),
'small':ParagraphStyle('small',fontName='DV',fontSize=8.2,leading=12,textColor=MUTED,spaceAfter=7),
'tag':ParagraphStyle('tag',fontName='DVB',fontSize=8.5,leading=13,textColor=MUTED,spaceAfter=14),
}
story=[]
def p(text,style='p'): return Paragraph(text,styles[style])
def add(text,style='p'): story.append(p(text,style))
def box(text,warning=False):
    t=Table([[p(text)]],colWidths=[483]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),AMBER if warning else LIGHT),('LEFTPADDING',(0,0),(-1,-1),13),('RIGHTPADDING',(0,0),(-1,-1),13),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.extend([t,Spacer(1,12)])
def table(headers,rows,widths):
    data=[[p(str(v),'small') for v in headers]]+[[p(str(v),'small') for v in row] for row in rows]
    t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#d2dcd2')),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.append(t);story.append(Spacer(1,10))
def fig(path,width=483):
    from PIL import Image as PI
    with PI.open(root/path) as im: h=im.height/im.width*width
    story.extend([Image(str(root/path),width=width,height=h),Spacer(1,9)])
def page(n,title):
    if story:story.append(PageBreak())
    add(f'ORMAN-SSL / {n:02d} / ARAŞTIRMA BAŞLANGICI','tag');add(title,'h1')
def footer(c,doc):
    c.saveState();c.setStrokeColor(colors.HexColor('#d3ddd3'));c.line(56,43,539,43)
    c.setFont('DV',8);c.setFillColor(MUTED);c.drawString(56,29,'Mehmet Oğuz Güneren | 26 Eylül 2026');c.drawRightString(539,29,f'{doc.page}');c.restoreState()
r=json.loads((root/'reports/real_experiment/results.json').read_text());a=json.loads((root/'reports/real_analysis.json').read_text());prep=json.loads((root/'reports/disfor_preparation.json').read_text());card=a['selection']
add('NİDA HOCA İLE ARAŞTIRMA GÖRÜŞMESİ / SÜRÜM 2','tag');story.append(Spacer(1,22))
add('Gerçek veri.\nÖlçülmüş sonuç.','title')
add('Orman-SSL: Sentinel-2 zaman serilerinden orman kesimi sınıflandırması','h2')
box('<b>Tamamlanan araştırma MVP’si</b><br/>Gerçek etiketli veri hazırlama, üç yöntemle eğitim, coğrafi test, belirsizlik ve hata analizi, kayıtlı model ve yeni girdide çalışan tahmin komutu.')
table(['Ölçü','Gerçek deney'],[['Veri','2.213 gerçek 24 aylık seri; 10 Sentinel-2 bandı'],['Ayrım','1.266 eğitim / 461 validation / 486 test; en az 5 km ayrım'],['Karşılaştırma','3 yöntem × 4 etiket bütçesi × 3 seed = 36 koşul'],['Seçilen checkpoint',f'Transformer, sabit seed 7; test macro-F1 = {a["selected_test_macro_f1"]:.3f}'],['Kontrol','18 test; gerçek CLI çıkarımı ve GeoJSON çıktısı']], [143,340])
box('Tam etiketle Transformer güçlü çıktı; az etikette Random Forest daha güçlü. Uygulanan SSL ön eğitimi bu protokolde üstünlük sağlamadı. Sonuçlar seçilip gizlenmedi.')
add('Bu sürüm, ilk sentetik başlangıcın ötesinde gerçek veride tamamlanmış bir deneydir. Sürekli ülke ölçeğinde saha ürünü veya kabul edilmiş makale iddiası değildir.','small')
add('Mehmet Oğuz Güneren · 26 Eylül 2026<br/>Yapay zekâ yardımıyla hazırlanmıştır. Bilimsel değerlendirme ve yayın kararı araştırmacılara aittir.','small')
page(2,'Gerçek veri ve savunulabilir ayrım')
add('DISFOR: yorumlanmış etiket ve zaman serisi birlikte','h2')
add('JR-DIGITAL DISFOR’un sabit revision’ından ham tablo ve etiketler indirildi. Yerel dosyada 3.822 nokta var. Kaynak etiketler görüntü yorumu ve yardımcı olay kayıtlarına dayanır; yeni arazi ölçümleri toplandığı iddia edilmez. [1]')
table(['Hazırlama kuralı','Uygulanan seçim'],[['Etiket','High-confidence; bozulmamış orman (110) ve kesim (211)'],['Zaman','2018-2023 hedef yılları; önceki yıl + hedef yıl, 24 ay'],['Pozitif','Önceki yıl orman; ikinci yılda tek kesim; pencerede başka bozulma yok'],['Negatif','İki yıllık pencerenin tamamını bozulmamış orman segmenti örtüyor'],['Gözlem','Source clear ve SCL 4/5; her yıl en az altı açık ay'],['Girdi','10 DN bandının aylık medyanı; eksik aylar doldurulmadı']], [94,389])
add('Mekânsal koruma','h2')
add('5 km içinde bağlı noktalar ve aynı kaynak hasar poligonu/fırtına örnekleri tek grupta tutuldu. Örnekleme strata’ları olay sayılmadı. Her kaynak noktadan yalnızca bir pencere kullanıldı. Standardizasyon ve SSL yalnızca eğitim coğrafyasında yapıldı.')
table(['Split','Bozulmamış','Kesim','Toplam'],[[name,info['class_counts'][0],info['class_counts'][1],info['n']] for name,info in prep['split'].items()],[159,108,108,108])
add('Ölçülen minimum çapraz-split mesafeleri: '+', '.join(f'{k}: {v:.3f} km' for k,v in prep['minimum_cross_split_distance_km'].items())+'.','small')
box('İlk üç sınıflı hazırlıkta testte yalnızca bir yangın örneği kaldı. Model skorları okunmadan birincil görev kesim/bozulmamış orman olarak daraltıldı. Yangın başarımı iddiası kurulmadı.',True)
page(3,'Üç yöntem, aynı etiket bütçesi')
fig('reports/real_experiment/label_efficiency.png',475)
rows=[]
for f in [.05,.1,.2,1.]:
 rs=[x for x in r['summary'] if x['label_fraction']==f];rows.append([f'%{int(f*100)}']+[f'{x["macro_f1_mean"]:.3f} ± {x["macro_f1_std"]:.3f}' for x in rs])
table(['Eğitim etiketi','Random Forest','Transformer','SSL Transformer'],rows,[93,130,130,130])
add('Test macro-F1 ortalama ± üç seed standart sapması. Validation için 461 etiket, belirtilen eğitim yüzdelerine ek maliyettir. Seed standart sapması güven aralığı değildir.','small')
add('Deneyin yorumu','h2')
add('Tam etiketli supervised Transformer ortalaması 0,877. %20 etikette RF ortalaması 0,811, supervised Transformer 0,490 ve SSL Transformer 0,484. Az etiketli modellerde sınıf dengesizliği önemlidir; bu sabit koşuda Transformer fine-tune kaybı sınıf ağırlıksızdır.')
ci=a['ssl_minus_supervised_at_20_percent']['bootstrap_95_interval']
box(f'%20 etikette SSL-supervised farkı {a["ssl_minus_supervised_at_20_percent"]["mean"]:.4f}. 1.000 eşleştirilmiş mekânsal grup bootstrap tekrarında %95 aralık [{ci[0]:.4f}, {ci[1]:.4f}]. Sıfırı kapsayan bu aralık SSL üstünlüğünü desteklemiyor.')
add('Bu, SSL’nin genel olarak başarısız olduğu sonucu değildir. Yalnızca uygulanan model, maskeleme, veri hazırlama ve coğrafi ayrım için gözlemdir.','small')
page(4,'Kullanıma ayrılan model ve hataları')
add('Checkpoint seçimi testten bağımsız yapıldı','h2')
add('Yöntem, %100 eğitim etiketi koşulunda üç seed’in ortalama validation macro-F1’iyle seçildi. Seed 7 önceden sabitlendi. Seçilen yöntem Transformer; model dosyası models/model.pt.')
fig('figures/real_confusion.png',330)
table(['Ölçü','Değer'],[['Seçilen tek checkpoint test macro-F1',f'{a["selected_test_macro_f1"]:.3f}'],['Kesim precision','26 / 32 = %81,3'],['Kesim recall','26 / 38 = %68,4'],['Test desteği','486 nokta / 175 mekânsal grup; 20 pozitif grup']], [264,219])
box('12 kesim kaçırıldı; 6 bozulmamış örnek yanlış kesim olarak işaretlendi. Model skoru kalibre edilmiş güven değildir. Tek checkpoint’in 0,861 skoru ile üç seed ortalaması 0,877 farklı ölçümlerdir.',True)
add('Çıkarım aracı etiket gerektirmeyen NPZ girdisini okur. Bant sırası, zaman sırası, şekil ve gözlem değerlerini kontrol eder. Eğitimdeki minimum gözlem kalitesini karşılamayan örnekleri quality_eligible alanında işaretler.','small')
page(5,'Eksik gözlem ve hata incelemesi')
fig('figures/real_robustness.png',440)
add('Kontrollü dayanıklılık deneyi','h2')
add('%20 eğitim etiketiyle eğitilmiş modellerin test girdilerinden %0, %20, %40 ve %60 ek ay silindi. Modeller yeniden ayarlanmadı. Aynı seed için bütün yöntemler aynı maskeyi gördü. Bu silme, gerçek bulutların mevsimsel dağılımının tam modeli değildir.')
add('Etkileşimli hata incelemesi','h2')
add('reports/demo.html içinde 486 test örneğinden seçim yapılabilir. “Yalnız hatalı tahminler” ve “Kaçırılan kesimler” filtreleriyle kaynak etiket, tahmin, skor ve B04/B08/B12 eğrileri birlikte görülür. Bu arayüz kayıtlı gerçek test sonuçlarını açar; modeli yeniden eğitmez.')
add('Coğrafi çıktı','h2')
add('reports/real_experiment/test_predictions.geojson; test örneklerinin koordinat, hedef yıl, grup, gerçek etiket, tahmin ve skorlarını içerir. QGIS’e yüklenebilir. Noktalar arasında sürekli tahmin rasterı üretildiği iddia edilmez.')
box('Kaydedilmiş hata atlası ve bütün koşullar raporda bulunur. Test hataları bu çalışmada tekrar hiperparametre ayarlamak için kullanılmadı.')
page(6,'Yöntem, tekrar üretim ve sınırlar')
table(['Bileşen','Sabit ana deney'],[['Transformer','1 encoder, 32 boyut, 4 head, dropout 0,1; değer + maske + zaman'],['SSL','Gözlenen hücrelerin %30’unu maskeleme; 30 epoch; yalnızca train'],['Fine-tune','25 epoch; validation macro-F1 ile checkpoint'],['RF','200 ağaç; min_samples_leaf=2; balanced ağırlık; zaman özetleri'],['Tekrar','Seed 7/17/27; aynı iç içe etiket altkümeleri; aynı split']], [109,374])
add('Yeni girdide çalıştır','h2')
add('PYTHONPATH=src .venv/bin/python -m orman_ssl.predict<br/>--checkpoint models/model.pt<br/>--data data/processed/test_inference.npz<br/>--out reports/my_predictions.json','small')
add('Komut yukarıda satırlara bölünerek gösterildi; terminalde tek satır kullan. README’de kopyalanabilir sürümü vardır. Bu girdi 486 gerçek test örneğinin etiketsiz halidir.','small')
add('Tüm deney','h2');add('scripts/reproduce.sh: veri hazırlama → eğitim → analiz → örnek çıkarımı → 18 test → HTML ve PDF. Kurulum dosyaları, ham/işlenmiş veri, kaynak hash’leri ve bütün checkpoint’ler pakettedir.')
add('Sınırlar','h2')
add('Tek coğrafi ayrım, testte 38 kesim ve 20 pozitif grup, dengesiz sınıflar, kaynak kampanya/coğrafya etkileri ve DN işleme geçmişi. Bu koşular arasında eşit toplam hesaplama bütçesi yok; SSL ek ön eğitim kullanır. Sonuç resmi DISFOR split’inin benchmark skoru değildir.')
box('Tamamlanan görev Sentinel-2 ile geriye dönük kesim sınıflandırmasıdır. Gerçek SAR füzyonu, Türkiye’de dış saha doğrulaması, erken uyarı ve bütün bozulma türleri bu çıktının kapsamında değildir.',True)
page(7,'Toplantıda ne sunulacak?')
add('Sekiz dakikalık anlatım','h2')
for text in ['1. Soru: az etiket koşulunda SSL ek fayda sağlıyor mu?', '2. Veri: gerçek DISFOR etiketleri, 24 aylık pencereler ve 5 km ayrım.', '3. Sonuç: tam etikette Transformer; az etikette RF güçlü. SSL kazancı gösterilemedi.', '4. Demo: bir doğru karar ve bir kaçırılan kesimin eğrisini aç.', '5. Hata: 38 kesimden 12’si kaçırıldı; skorları genelleme iddiasıyla büyütme.', '6. Karar: bu sonucun hangi araştırma uzantısına değeceğini birlikte seç.']:add(text)
add('Kaynaklar','h2')
for title,url in [('[1] JR-DIGITAL. DISFOR; revision 2562332, EUPL-1.2.','https://huggingface.co/datasets/JR-DIGITAL/DISFOR'),('[2] Zhang ve ark. (2025). Self-supervised forest disturbance type detection.','https://doi.org/10.1080/17538947.2025.2537325'),('[3] Wang ve ark. (2026). Global high-resolution forest disturbance type dataset.','https://doi.org/10.5194/essd-18-1601-2026')]:add(escape(title)+f'<br/><link href="{url}" color="#2c6a51">{url}</link>','small')
add('Ana SSL makalesinin tam PDF’sine doğrudan erişim 403 verdi; mevcut uygulama makalenin birebir reprodüksiyonu değildir. Kaynak yönteminden esinlenen bağımsız başlangıç modelidir. İlk GFD ve Marmaris incelemeleri demo_v1.html içinde korunmuştur.','small')
box('Teslim: gerçek model ve veri, çalıştırılmış deneyler, çıkarım komutu, hata analizi, rapor ve gösterim. Bilimsel yayın yeniliği ve bağımsız saha doğrulaması ayrıca değerlendirilir. E-posta gönderilmedi.')
out=root/'output/pdf/Orman_SSL_Toplanti_Dosyasi.pdf';out.parent.mkdir(parents=True,exist_ok=True)
doc=SimpleDocTemplate(str(out),pagesize=(595.28,841.89),rightMargin=56,leftMargin=56,topMargin=48,bottomMargin=59,title='Orman-SSL - Gerçek Veri Deneyi',author='Mehmet Oğuz Güneren')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(out)
