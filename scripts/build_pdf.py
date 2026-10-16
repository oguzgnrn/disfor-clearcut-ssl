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
r=json.loads((root/'reports/experiment/results.json').read_text())
s=json.loads((root/'reports/sentinel_summary.json').read_text())
g=json.loads((root/'reports/gfd_audit.json').read_text())
m=json.loads((root/'data/metadata/sentinel_manifest.json').read_text())

add('NİDA HOCA İLE İLK ARAŞTIRMA GÖRÜŞMESİ','tag');story.append(Spacer(1,25))
add('Ormanı izlemek.<br/>Az etiketle öğrenmek.','title')
add('Gerçek uydu verisi incelemesi ve self-supervised öğrenme için çalıştırılmış bir proje başlangıcı.','h2')
story.append(Spacer(1,15))
box('<b>Ana soru</b><br/>Coğrafi olarak ayrılmış test alanlarında, az sayıda etiket kullanıldığında etiketsiz zaman serilerinden ön öğrenme ne kadar fayda sağlıyor?')
table(['Hazır teslim','Ne gösteriyor?'],[
['Gerçek veri incelemesi','İki GFD GeoTIFF dosyası, kaynak/sınıf denetimi ve QGIS kesitleri.'],
['Gerçek uydu MVP’si','Marmaris çevresinde iki tarihli Sentinel-2 kalite maskesi ve indeks farkı.'],
['Öğrenme altyapısı','RF, Transformer ve SSL Transformer; 36 sentetik deney koşulu.'],
['Araştırma protokolü','Etiket, coğrafi ayrım, karşılaştırma, değerlendirme ve altı haftalık plan.']], [146,337])
box('Bu paket bir <b>araştırma başlangıcı ve teknik MVP</b> olarak tamamlandı. Gerçek olay etiketleriyle eğitilmiş sınıflandırıcı, dış saha doğrulaması ve tamamlanmış makale henüz yok.',True)
add('Toplantıdan beklenen karar: pilot bölge, ilk sınıflar ve bağımsız etiket kaynağı.','h2')
add('Hazırlayan: Mehmet Oğuz Güneren<br/>Yapay zekâ yardımıyla hazırlanmıştır. Yöntem ve bilimsel yorumlar araştırmacı incelemesine açıktır.','small')

page(2,'Gerçek görüntüyle çalışan MVP')
dates=' / '.join(x['datetime'][:10] for x in m['scenes'])
add(f'<b>Marmaris çevresi:</b> {dates}. Sentinel-2 L2A, 20 m ortak grid, EPSG:32635. Alan kutusu: {m["bbox"]}.')
fig('figures/sentinel_change.png')
add('Nasıl hesaplandı?','h2')
add('Kırmızı, NIR ve SWIR2 bantları aynı gride alındı. Ölçek/ofset sahne metadatasından okundu. SCL 4/5 dışındaki sınıflar ve geçersiz bantlar maskelendi. NBR=(NIR-SWIR2)/(NIR+SWIR2); dNBR=önce NBR-sonra NBR.')
table(['Kalite / tarama ölçümü','Bu koşudaki değer'],[
['Ortak geçerli piksel',f'{s["valid_pixels"]:,} / {s["total_pixels"]:,} (%{100*s["jointly_valid_fraction"]:.1f})'],
['Ortalama / medyan dNBR',f'{s["mean_dnbr"]:.4f} / {s["median_dnbr"]:.4f}'],
['dNBR > 0,20 tarama alanı',f'{next(x for x in s["thresholds"] if x["threshold"]==.2)["screened_hectares"]:.2f} ha; doğrulanmış yangın alanı değil']], [220,263])
box('Bu iki tarihli karşılaştırma <b>bir tür sınıflandırıcısı değildir</b>. Orman maskesi veya bağımsız olay etiketi yok. Pozitif fark; yangın, kesim, mevsimsellik, nem ve başka arazi değişimlerinden ayrıştırılmalıdır.',True)
add('Canlı gösterim','h2');add('reports/demo_v1.html internet olmadan açılır. Eşik kaydırıcısı gerçek dNBR rasterındaki pikselleri yeniden sayar; sonuç özeti indirilebilir. GeoTIFF çıktıları QGIS’e aktarılabilir.')
add('Veri: modified Copernicus Sentinel data (2021), Element 84 Earth Search. Sahne kimlikleri, kaynak adresleri ve SHA-256 kayıtları data/metadata/sentinel_manifest.json içinde. [5]','small')

page(3,'Etikete dönüşmeden önce veri denetimi')
add('Hocanın paylaştığı GFD ürününden iki küçük gerçek dosya indirildi. Tam raster sayımları bloklar halinde yapıldı; harita için ayrı inceleme kesitleri çıkarıldı.')
table(['Örnek','Boyut','Gözlenen kod','NoData'],[[x['file'],f'{x["shape"][0]:,} × {x["shape"][1]:,}',len(x['counts']),'Tanımlı değil'] for x in g],[105,168,112,98])
fig('figures/GFC30_inspection.png',400)
add('Karar değiştiren bulgular','h2')
add('Figshare v1 ve yayımlanmış makalede doğruluk, örnek sayısı ve 0 kodu açıklamaları uyuşmuyor. Kaynak sözlüğü netleşmeden sıfır hücreler negatif orman etiketi yapılmamalı. Ürün 2000-2020 dönemini özetliyor; olay yılı bilinmeden Sentinel gözlem penceresiyle eşleştirmek güvenilir değil. [1, 2]')
add('Yerel teknik gözlem: EPSG:4326, int16, yaklaşık 0,0002695 derece grid. NoData tanımı yok. Alan hesabı için derece gridindeki sayımlar sabit 900 m² ile çarpılmaz.','small')
box('Kesitler kodların yoğun olduğu pencerelerden seçildi; temsili örneklem değildir. Bu GFD örnekleri Türkiye’de değildir. 2021 Sentinel demosuna GFD etiketi atanmadı.')

page(4,'Öğrenme hattı: ölçüldü, kaydedildi')
box('<b>SENTETİK DENEY</b> - Aşağıdaki sayılar uydu başarımı değildir. 720 yapay seri; 24 zaman adımı; 6 temsili kanal; 60 yapay grup. Eğitim/validation/test: 432/144/144.',True)
fig('reports/experiment/label_efficiency.png',455)
rows=[]
for frac in [.05,.1,.2,1.]:
    rs=[x for x in r['summary'] if x['label_fraction']==frac]
    rows.append([f'%{int(frac*100)}']+[f'{x["macro_f1_mean"]:.3f} ± {x["macro_f1_std"]:.3f}' for x in rs])
table(['Eğitim etiketi','Random Forest','Transformer','SSL Transformer'],rows,[93,130,130,130])
add('Macro-F1 ortalama ± 3 seed standart sapması. Standart sapma güven aralığı değildir. Validation etiketleri eğitim yüzdelerine ek maliyettir.','small')
add('Sentetik kontrol koşulunda SSL az etiketli Transformer’a katkı verdi; RF güçlü kaldı. Gerçek uydu verisine veya başka bir veri dağılımına bu sonuç taşınamaz.')
add('32 boyutlu tek encoder; %30 gözlenen hücre maskeleme; 30 ön eğitim ve 25 fine-tune epoch. Aynı başlangıç ağırlıkları ve aynı etiket altkümeleri. Model seçimi yalnızca validation ile. Test grupları ön eğitime veya normalizasyona girmez. IRMST’nin birebir reprodüksiyonu değildir.','small')

page(5,'İlk gerçek deneyi nasıl kuracağız?')
add('Önerilen kapsam','h2');add('Tek bölge ve tek dönem; başlangıçta doğrulanmış bozulma / olay görülmeyen orman. Yangın-kesim ayrımı ancak yeterli bağımsız olay etiketi bulunursa eklenir. Hastalık ve kuraklık, güvenilir referans yoksa ilk kapsamın dışında kalır.')
table(['Adım','Uygulama'],[
['Etiket ve zaman','Konum, olay tarihi, kaynak, yorumlayıcı güveni ve ikinci kontrol. GFD aday alan sağlayabilir; tek başına bağımsız gerçek etiket sayılmaz.'],
['Veri küpü','S2 optik bantları ve kalite maskesi. Sonraki aşamada uyumlu S1 VV/VH; yörünge, birim ve topoğrafya denetimi.'],
['Ayrım','Olay/poligon ve coğrafi blok birlikte korunur. Komşu patchler arası tampon; aynı olay tüm tarihleriyle tek splitte.'],
['Karşılaştırma','RF + aynı Transformer’ın sıfırdan ve SSL ön eğitimli sürümleri. %5/%10/%20/%100 eğitim etiketi; toplam etiket maliyeti ayrıca.'],
['Ölçüm','Macro-F1, sınıf bazında precision/recall ve confusion matrix. Gerçek deneyde olay/blok bootstrap ve dış bölge testi.']], [99,384])
add('Aday katkı ve açık hipotez','h2')
add('Az etikette, eksik optik gözlem altında ve başka coğrafyada faydanın sürüp sürmediğini ölçmek. Başlangıç için yeni büyük mimari iddiası gerekmiyor. SSL+S1/S2 zaten literatürde var; yenilik sistematik taramayla ayrıca gösterilmeli. [3]')
box('Önerilen karar eşiği: %10 ve %20 etikette supervised modele göre en az +0,03 macro-F1 ve coğrafi deneylerde tutarlılık. Bu, hocayla netleştirilecek proje içi hedef; istatistiksel anlamlılık veya garanti değildir.')
add('RF daha iyi kalırsa sonuç raporlanır. SSL ek hesaplama kullanır; gerçek pilotta eşit hesaplama kontrolü eklenir. Test sonucu üzerinden sürekli hiperparametre seçilmez.','small')

page(6,'Altı hafta ve ilk toplantının kararları')
table(['Hafta','Somut çıktı','Karar kapısı'],[
['1','Bölge, sınıf, tam yöntem ve 20 olaylık inceleme','Bağımsız etiket bulunabiliyor mu?'],
['2','Etiket manifesti, S2 zaman serisi, QGIS incelemesi','Tarihler, maskeler, sınıf desteği yeterli mi?'],
['3','RF + supervised model; sabit split','Sızıntı kontrolü geçti mi?'],
['4','SSL, etiket oranları ve seed tekrarları','Az etiket karşılaştırması güvenilir mi?'],
['5','SAR, gözlem kaybı ve zaman kodlama deneyleri','Kazancı hangi bileşen açıklıyor?'],
['6','Dış test, hata örnekleri, yöntem/sonuç taslağı','Yayın için yeterli katkı var mı?']], [45,253,185])
add('Toplantıda sorulacaklar','h2')
for text in [
'1. Türkiye’de mi, açık ve güvenilir etiketli yabancı bir bölgede mi başlayalım?',
'2. İki sınıflı tespit mi, yeterli etiket varsa yangın/kesim ayrımı mı?',
'3. Olay tarihleri ve bağımsız doğrulama için hangi kaynaklara erişebiliriz?',
'4. Ana SSL makalesinin tam yöntemi, kodu ve veri erişimini netleştirebilir miyiz?',
'5. Gelecek hafta 20 olayın incelemesi ve ilk gerçek zaman serileri uygun teslim mi?']:add(text)
add('MVP’den bilimsel sonuca kalan işler','h2')
add('Gerçek olay etiketi toplama, çok tarihli S1/S2 küpü, gerçek coğrafi model değerlendirmesi, dış doğrulama ve yenilik taraması. Mevcut sonuçlar bu işlerin yerine geçmez.')
box('İlk pilot küçük veriyle CPU’da başlayabilir. GPU ihtiyacı örnek büyüklüğüne göre belirlenir. Büyük veri / dağıtık işleme ancak ölçek gereksinimi ortaya çıktığında eklenir.')

page(7,'Kaynaklar, kullanım ve teslim sınırı')
refs=[
('[1] Wang ve ark. (2026). Global high-resolution forest disturbance type dataset. ESSD 18, 1601-1617.','https://doi.org/10.5194/essd-18-1601-2026'),
('[2] Liu ve ark. Global forest main disturbance types between 2000 and 2020. Figshare v1. CC BY 4.0.','https://doi.org/10.6084/m9.figshare.28465178'),
('[3] Zhang ve ark. (2025). Self-supervised deep learning for detection of forest disturbance types... International Journal of Digital Earth.','https://doi.org/10.1080/17538947.2025.2537325'),
('[4a] Maze ve ark. (2025). Enhanced agricultural land use/land cover classification in the Nile Delta...','https://doi.org/10.1016/j.isprsjprs.2025.08.019'),
('[4b] Vyas ve ark. (2025; çevrimiçi 2024). A novel image fusion-based post classification framework...','https://doi.org/10.1007/s12145-024-01506-0'),
('[5] Element 84. Earth Search STAC API; veri koleksiyonları ve gain/offset açıklaması.','https://github.com/Element84/earth-search'),
('[6] Copernicus. Sentinel-2 işleme ve kalite bilgisi.','https://sentiwiki.copernicus.eu/web/s2-processing')]
for title,url in refs:add(escape(title)+f'<br/><link href="{url}" color="#2c6a51">{escape(url)}</link>','small')
add('Kaynak erişim sınırı','h2')
add('GFD tam HTML incelendi. SSL makalesinde yayıncı arama indeksindeki özet ve ilgili bölüm görüldü; doğrudan PDF/HTML 403 verdi. Tam yöntemin eksiksiz okunduğu veya reprodüksiyon yapıldığı iddia edilmiyor. İki tarım makalesi için erişilebilir özet/bölüm bilgileri incelendi. Ayrıntılar docs/KAYNAK_NOTLARI.md içinde.','small')
add('Paketi açma sırası','h2')
add('1. Bu toplantı dosyası.<br/>2. reports/demo_v1.html - çevrimdışı etkileşimli sonuçlar.<br/>3. docs/ARASTIRMA_PLANI.md ve TOPLANTI_REHBERI.md.<br/>4. README.md - kurulum, komutlar ve gerçek veri sözleşmesi.','small')
add('Kalite kontrolü','h2')
add('Deney hattında 9 otomatik test geçti. Sabit split, train-only normalizasyon, etiket bütçelerinin iç içe olması, maskenin hedef kaybına etkisi ve kayıt tutarlılığı kontrol edildi. QGIS uygulamasında canlı doğrulama yapılmadı; hazır raster ve stil dosyaları sağlandı.','small')
box('Hazır olan: somut araştırma başlangıcı ve çalışan MVP. Henüz olmayan: gerçek doğrulanmış orman türü sınıflandırma başarımı, tamamlanmış bilimsel makale. E-posta taslağı hazırlandı; gönderilmedi.')

out=root/'output/archive_v1/Orman_SSL_Baslangic_Dosyasi.pdf';out.parent.mkdir(parents=True,exist_ok=True)
doc=SimpleDocTemplate(str(out),pagesize=(595.28,841.89),rightMargin=56,leftMargin=56,topMargin=48,bottomMargin=59,
                      title='Orman-SSL - Araştırma Başlangıcı ve MVP',author='Mehmet Oğuz Güneren')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(out)
