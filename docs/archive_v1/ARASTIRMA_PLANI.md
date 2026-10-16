# Proje önerisi: az etiketle orman bozulması tespiti

26 Eylül 2026 · İlk toplantı için öneri · Araştırmacı: Mehmet Oğuz Güneren

## 1. Araştırma sorusu

**Coğrafi olarak ayrılmış test alanlarında, sınırlı sayıda etiket kullanıldığında maskeli zaman serisi ön eğitimi, aynı mimarinin sıfırdan eğitilmesine göre orman bozulması sınıflandırmasını iyileştiriyor mu? Optik gözlem kayıpları arttığında Sentinel-1 katkısı değişiyor mu?**

Bu bir hipotezdir. SSL'nin kesin üstünlüğü veya yayın yeniliği henüz gösterilmemiştir. Çalışmanın değeri başlangıçta yeni bir büyük mimari tasarlamaktan çok adil etiket bütçesi, coğrafi genelleme ve eksik gözlem koşullarını birlikte ölçmek olabilir. Yenilik iddiası için daha geniş sistematik literatür taraması gerekir.

## 2. Kapsamı nasıl daraltalım?

İlk gerçek deneyde tek bölge, tek olay dönemi ve iki sınıf önerilir: bağımsız olarak doğrulanmış bozulma / olay görülmeyen orman. Olay görülmeyen örnekler, gözlem penceresinde incelenmiş olmalıdır; “etiket yok” bozulma yok demek değildir. Yeterli sayıda bağımsız yangın ve kesim olayı bulunursa ikinci aşamada bozulma türleri ayrılır. Hastalık ve kuraklık, arazi veya uzman kanıtı yoksa ilk deneye alınmaz.

Türkiye'deki Marmaris çevresi mevcut görüntü demosudur; nihai eğitim sahası seçimi değildir. Kamuya açık yabancı bir bölgede güvenilir etiket bulunursa ilk bilimsel deney orada yapılabilir. Türkiye aktarımı ayrı dış test olarak saklanır. Böylece veri erişimi tüm araştırmayı kilitlemez.

## 3. Veri kapısı: modelden önce geçilmesi gereken koşullar

Her örnekte konum, olay/izleme tarih aralığı, olay grubu, etiket kaynağı, yorumlayıcı güveni ve görüntü kalite bilgisi bulunmalı. Önerilen pilot hedef: sınıf başına en az 20 bağımsız olay/orman poligonu ve toplam 300-600 gözden geçirilmiş örnek; bunlar güç analizi sonucu değil, başlangıç hedefidir. Komşu pikseller bağımsız örnek sayılmaz. Etiketlerin en az %20'sini ikinci yorumlayıcı incelemeli; anlaşmazlıklar karara bağlanmadan test kümesine alınmamalı.

Figshare ürünü, aday alan bulmak ve coğrafi dağılım görmek için yardımcı olabilir. Dönem boyunca baskın türü özetleyen bir haritanın olay yılı bilinmiyorsa 2017-2020 görüntülerine otomatik olarak etiket atanamaz. Referans haritadan öğrenip yine aynı haritayla test etmek, bağımsız olay doğruluğunu ölçmez. Böyle bir ek deney yapılırsa “ürünle uyum” olarak adlandırılmalıdır.

Uydu penceresi olaydan yaklaşık bir yıl öncesi ve bir yıl sonrası olabilir; kesin pencere olay tarihinin güvenilirliğine göre seçilir. Sentinel-2'nin 2015 öncesi görüntüsü yoktur. 2000-2020 GFD dönemi ile Sentinel döneminin tümü eşleşmez. GFD bitişinden sonraki 2021 Marmaris demosu, bu ürünle etiketlenmez.

## 4. İşleme protokolü

Sentinel-2 L2A'da B4, B8, B11, B12; NDVI ve NBR aday değişkenlerdir. Bulut, gölge, kar, hatalı piksel ve gözlem yokluğu ayrı kalite maskesinde tutulur. Ölçek ve ofset veri sürümüne göre okunur. Ortak 20 m veya 30 m grid seçilir; sürekli yansıtım verisi uygun ortalama/bilinear yöntemle, kategorik sınıflar en yakın komşuyla taşınır. 30 m etiketin 10 m'ye taşınması yeni etiket bilgisi üretmez.

Sentinel-1 için VV/VH, sabit yörünge yönü ve mümkünse aynı göreli yörünge seçilir. Geometrik/radyometrik düzeltme, arazi etkileri, dB ile lineer güç ayrımı belgelenir. SAR buluttan optik kadar etkilenmez; buna rağmen nem, geometri, speckle ve topoğrafya değişimleri biyolojik bozulmayla karıştırılabilir. Mevcut MVP gerçek SAR işlemez.

Aylık kompozit ilk gerçek pilotu sadeleştirir. Daha sonra gerçek edinim günleriyle düzensiz seri kullanılır. Gerçekte gözlenmeyen tarihleri doğruluk hedefi gibi kullanarak doldurmayız. Train/validation/test ayrımı veri artırma, standardizasyon ve SSL ön eğitiminden önce yapılır.

## 5. Deney tasarımı

| Boyut | İlk ana deney | Sonraki kontrollü deney |
|---|---|---|
| Yöntem | RF, supervised Transformer, SSL Transformer | Hazır uydu ön eğitimli model, erişim uygunsa |
| Etiket bütçesi | Eğitim örneklerinin %5, %10, %20, %100'ü | Eşit toplam etiket maliyeti: validation dahil |
| Tekrar | Aynı ayrımda 3 seed (MVP) | 5 seed + birden fazla coğrafi fold |
| Girdi | Sentinel-2 | Sentinel-1; Sentinel-1+2 |
| Eksik gözlem | Doğal kalite maskesi | Ek optik gözlem silme %0/%20/%40/%60 |
| Zaman bilgisi | Edinim günü + yıllık sin/cos | Sıra numarasıyla karşılaştırma |
| Test | Olay/poligon ve coğrafi blok ayrımı | Başka bölge; mümkünse başka yıl |

MVP'de Transformer 32 boyutlu, bir encoder katmanlıdır. Değerler ve gözlenme maskesi birlikte verilir. SSL, eğitim gruplarında gözlenen hücrelerin %30'unu kapatır ve yalnızca kapatılan gerçek gözlemler üzerinde MSE en aza indirilir. Ardından sınıflandırıcı az etiketle fine-tune edilir. Bu, Zhang makalesinin IRMST modelinin birebir reprodüksiyonu değildir; anlaşılır bir başlangıç uygulamasıdır.

Sıfırdan Transformer ile SSL Transformer aynı başlangıç ağırlıklarını ve aynı etiketli örnekleri kullanır. Fine-tune adım sayısı ve model seçimi politikası aynıdır. SSL'nin fazladan hesaplama kullandığı ayrıca raporlanır; gerçek deneyde eşit hesaplama bütçeli kontrol eklenmelidir. RF zaman özetleri kullandığı için yararlı bir pratik referanstır, aynı temsil gücünde mimari kontrol değildir.

MVP'de 60/20/20 grup ayrımı sabittir. Gerçek veride grup kimlikleri tek başına yeterli değildir: aynı olay farklı gruplara dağıtılamaz. Bloklar arasına en az en büyük patch çapı kadar tampon konur; mekânsal korelasyon daha uzunsa tampon genişletilir. Aynı poligonun farklı tarihleri farklı splitlere giremez. Test coğrafyası SSL'de etiketsiz olarak da kullanılmaz (indüktif değerlendirme).

## 6. Ölçüm ve yorum

Birincil metrik macro-F1; sınıf bazında precision/recall/F1, confusion matrix ve destek sayıları birlikte raporlanır. Accuracy ikincildir. Gerçek deneyde güven aralığı piksellerden değil bağımsız olay/bloklardan bootstrap ile hesaplanır; seed standart sapması güven aralığı değildir. Uygun olursa en az 1.000 blok bootstrap örneği ve eşleştirilmiş yöntem farkı raporlanır.

Önerilen proje içi başarı eşiği: %10 ve %20 eğitim etiketi koşullarında SSL'nin supervised Transformer'a karşı en az +0,03 macro-F1 farkı göstermesi ve farkın coğrafi değerlendirmede tutarlı kalması. Bu eşik literatür yasası veya istatistiksel anlamlılık değildir; hocayla önceden belirlenecek karar ölçütüdür. RF daha iyi kalırsa bu sonuç saklanmaz. Kazanç yoksa maskeleme, etiket kalitesi, veri çeşitliliği ve eğitim rejimi araştırılır; test sonucu kullanılarak sürekli ayar yapılmaz.

Validation etiketleri mevcut %5/%10/%20 oranlarına dahil değildir. Bu nedenle “toplam etiket maliyetini %95 azalttık” sonucu çıkarılamaz. Mevcut rapor hem eğitim etiketi hem validation büyüklüğünü saklar.

## 7. Altı haftalık uygulanabilir çalışma

| Hafta | Teslim | Geçiş kararı |
|---|---|---|
| 1 | Makale yöntemine erişim, bölge ve sınıf kararı, 20 olaylık ön inceleme | Bağımsız etiket ve tarih bulunabiliyor mu? |
| 2 | Versiyonlu etiket tablosu, S2 küpü, QGIS kontrolü | Sınıflar ve tüm splitler yeterince temsil ediliyor mu? |
| 3 | RF + supervised baseline, dondurulmuş split | Veri sızıntısı ve kalite sorunları giderildi mi? |
| 4 | SSL ve etiket oranları, seed tekrarları | Az etikette karşılaştırma güvenilir mi? |
| 5 | SAR katkısı, eksik gözlem ve zaman kodlama deneyleri | Kazanç başka açıklamalardan ayrılabiliyor mu? |
| 6 | Dış bölge testi, hata atlası, yöntem ve sonuç taslağı | Yeterli katkı var mı; daraltma veya yayın yolu ne? |

Pilot için 16 GB RAM ve CPU yeterli olabilir; gerçek zaman serisi büyüdüğünde tek GPU erişimi süreyi azaltır. İlk hedef binlerce küçük örnektir; dağıtık mimariyi veri ihtiyacı kanıtlanınca ekleriz. Büyük veri deneyimi daha sonra STAC, COG, Zarr, parça bazlı işleme ve veri versiyonlama tarafında değerlendirilebilir.

## 8. Tamamlanmış olan ile araştırma borcu

Mevcut teslim: çalışan kod, gerçek iki veri incelemesi, sentetik deney kayıtları, testler ve toplantı paketi. Kalan araştırma: olay etiketleme, çok tarihli gerçek S1/S2 veri küpü, gerçek coğrafi SSL deneyi, dış doğrulama ve yayın yeniliğinin kanıtı. Bu adımlar yapılmadan sonuç tablosu bir makalenin gerçek uydu başarım tablosu olarak kullanılamaz.
