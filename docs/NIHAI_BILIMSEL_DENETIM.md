# Orman-SSL: nihai bilimsel denetim

**Denetim tarihi:** 27 Eylül 2026  
**Araştırma sürümü:** paper_v4  
**Karar:** Mevcut dar kapsamıyla hocaya sunulabilecek, sayısal kayıtları doğrulanmış bir araştırma dosyasıdır. Bağımsız saha genellemesi, Türkiye başarımı veya yöntem üstünlüğü kanıtlanmış bir çalışma olarak sunulmamalıdır.

Bu denetim mevcut deneyleri yeniden eğitmeden; makale, veri hazırlama ve eğitim kodları, 180 koşunun kayıtları, birleştirilmiş tahminler, bootstrap hesabı ve birincil kaynaklar üzerinden yapılmıştır. İnceleme sırasında dondurulmuş eğitim, model ve veri dosyaları değiştirilmemiştir. Makinece okunabilir kanıt: `reports/final_science_review.json`.

## 1. Hocaya sunulacak esas katkı

Araştırmanın güçlü sorusu şudur: **Az etiketle gözlenen özdenetimli öğrenme kazancı, daha güçlü ve daha uzun eğitilmiş bir denetimli karşılaştırıcı karşısında sürüyor mu?**

2.213 DISFOR konumunda, beş mekânsal kat ve üç tohumla, kısa eğitilmiş Transformer'a karşı görülen SSL kazancı doğrulanmaktadır. Ancak optimizasyon adımı eşlenen denetimli model daha yüksek macro-F1 verir. Dolayısıyla çalışma, kendi ilk hipotezini daha güçlü kontrollerle sınayan ve karşıt bulguyu saklamayan, yeniden üretilebilir bir deney denetimi sunar. Aynı protokolde maskeleme kontrolü, yalnızca eksiklik bilgisiyle tahmin, yalnızca konum/yıl/kampanya bilgisiyle tahmin ve kullanılmamış örneklerin destek denetimi de bulunur.

Bu katkı yeni bir Transformer mimarisi, bütün görevlerde en iyi model, Zhang ve arkadaşlarının doğrudan tekrarı veya Presto'dan üstünlük değildir. Literatür taraması bir sistematik derleme değildir; öncelik iddiası için kapsamlı bir tarama yapıldığı söylenmemelidir.

**Sunumda kullanılabilecek cümle:** “Gerçek Sentinel-2 serilerinde çalışan bir kesim sınıflandırma aracı geliştirdim. Araştırma tarafında ise SSL'nin az etiket avantajını 180 koşuluk mekânsal deneyle sınadım; daha uzun denetimli eğitim bu avantajı geçtiği için sonucu optimizasyon bütçesi ve değerlendirme tasarımı açısından raporladım.”

## 2. Bağımsız hesapla doğrulanan bulgular

| Kontrol | Sonuç |
|---|---|
| Dondurulmuş kod, veri ve protokol SHA-256 kayıtları | Tamamı eşleşiyor |
| Önceden tanımlanan koşular ile gerçek kayıtlar | 180 benzersiz koşu, eksik veya fazla kayıt yok |
| Ana veri | 2.213 konum; 1.937 bozulmamış orman, 276 kesim; 874 mekânsal bileşen |
| Kat ayrımı | Her konum her yöntem/tohum için bir kez testte; eğitim/test kimlik ve bileşen çakışması yok |
| En yakın eğitim–test çifti | 5,001115 km |
| Kaynak olay kimlikleri | Kontrol edilen 215 olay anahtarının her biri tek katta |
| Etiket altkümeleri | Aynı kat/tohum/bütçe için yöntemler arasında birebir eşleşiyor |
| Eğitim geçmişleri | Sabit epoch sayıları, SSL için 60 ön eğitim epoch'u; yeni deneyde validation seçimi yok |
| Kayıt bazında macro-F1, AP, ROC-AUC, karışıklık matrisleri | Yeniden hesapla birebir eşleşiyor |
| Kayıt bazında Brier skoru | En büyük fark 6,25 × 10⁻⁹'dan küçük; float32/float64 gösterim farkı |
| Birleştirilmiş dış-kat tahminleri | 36 tam vektör, toplam 79.668 tahmin değeri; kayıtlarla birebir eşleşiyor |
| Eşlenmiş mekânsal bootstrap | Bileşen bazında karışıklık sayılarıyla bağımsız formülasyon kullanılarak 2.000 çekiliş yeniden hesaplandı; aralıklar eşleşiyor |

Brier farkının kaynağı ayrıca kontrol edildi: ilgili kayıttaki olasılıklar float32 olarak okununca saklanan değer aynen geri geliyor. Bu, raporlanan dört ondalık haneyi etkileyen bir hesap hatası değildir.

| %20 etiket karşılaştırması | SSL eksi karşılaştırıcı macro-F1 | Koşullu %95 bootstrap aralığı | Yorum |
|---|---:|---|---|
| 40 epoch Transformer | +0,03676 | [0,02446; 0,05057] | Bu kısa eğitim tarifine göre SSL kazancı var |
| Optimizasyon adımı eşlenmiş Transformer | −0,02973 | [−0,04304; −0,01793] | Uzun denetimli tarif macro-F1 açısından daha iyi |
| Bağımsız hücre maskelemesi | +0,00804 | [−0,00132; 0,01779] | Yapılı maskenin üstünlüğü gösterilmiyor |
| CNN | −0,00309 | [−0,01942; 0,01254] | SSL'nin CNN üstünlüğü gösterilmiyor |

Ana karşılaştırma kısa Transformer'dır; diğer karşılaştırmalar keşifseldir. Aralıklar sabit kohort, katlar ve eğitilmiş tahminler için koşulludur. Yeni veri toplama, modelleri yeniden eğitme ve önceki uyarlamalı model geliştirme belirsizliğini kapsamaz. Üç tohum × beş kat, 15 bağımsız deney değildir.

## 3. Kod ile yöntem metninin uyumu

`scripts/prepare_disfor.py` içindeki seçim, makaledeki dar göreve uygundur: yüksek güvenli etiketler, konum başına tek 24 aylık pencere, ilk yılda bozulmamış orman, ikinci yılda uygun kesim olayı veya iki yıl boyunca stabil örnek. Aylık değerler `clear` ve SCL 4/5 koşullarından sonra medyanla üretilir; her yılda en az altı gözlenen ay aranır. Olay tarihleri girdi özelliği değildir. Bununla birlikte etiket geçmişleri pencere seçimini belirlediğinden deney geriye dönük, seçilmiş pencerelerde sınıflandırmadır.

`src/orman_ssl/advanced.py` normalizasyonu yalnızca dış eğitim bölümünden öğrenir. SSL kaybı yalnızca yapay olarak gizlenmiş ve başlangıçta gözlenmiş hücrelere uygulanır; doğal eksik değerler hedef değildir. Eşlenen modellerin sınıflandırıcı başlangıçları ve denetimli rastgelelikleri kontrol edilmektedir. Etiket azaltma sınıf bilgisinden yararlanan kontrollü bir simülasyondur; gerçek dünyada etiketleme maliyetinin %80 azaldığını kanıtlamaz.

320 epoch'luk kontrol, optimizer güncelleme sayısını eşler. FLOP, süre, öğrenme oranı, etiketli örnek gösterim sayısı ve amaç fonksiyonu eşlenmez. Bu yüzden sonuç “kazancın tek nedeni ek eğitimdir” biçiminde nedensel yorumlanmamalıdır. Makale bu ayrımı doğru yapmaktadır.

Önceki ham-veri yeniden üretim denetimi yedi kaynak dosyası ve yedi dizi alanının birebir eşleştiğini kaydeder. Bu son incelemede tüm ham veri hazırlama işlemi tekrar çalıştırılmadı; ilgili kayıt ve hazırlama kodu incelendi. Aynı şekilde 180 model yeniden eğitilmedi; eldeki eğitim ve tahmin kayıtları bağımsız hesapla denetlendi.

## 4. Birincil kaynakların doğrulanması

Kontrol tarihi 27 Eylül 2026'dır. Aşağıdaki kontroller erişilebilen birincil sayfa, yayın kaydı, özet ve yazar deposuna dayanır. Bütün makalelerin tam metinlerinin ayrıntılı incelendiği iddia edilmez.

| Kaynak | Doğrulanan durum ve doğru kullanım |
|---|---|
| [Viehweger ve ark., DISFOR / ESSD](https://essd.copernicus.org/preprints/essd-2026-185/) | Başlık, altı yazar, 2026 ve DOI doğrulandı. Yayın sayfası hâlen değerlendirmedeki ön baskı olarak gösteriyor. Özette 3.822 konum var. Hakemli kabul edilmiş veri makalesi denmemeli. |
| [Resmî DISFOR veri kartı](https://huggingface.co/datasets/JR-DIGITAL/DISFOR) | 110 bozulmamış orman, 211 kesim, 242 yangın etiketleri; yüksek güven tanımı; DN bantları ve EUPL-1.2 lisans etiketi doğrulandı. Kart metnindeki 3.823 ile tablodaki 3.822 farkını makale zaten açıklıyor. |
| [Zhang ve ark., 2025](https://www.tandfonline.com/doi/abs/10.1080/17538947.2025.2537325) | Yayıncı arama kaydında başlık, dergi, DOI, Sentinel-1/2 birleşimi, düzensiz zaman kodlaması ve contrastive ön eğitim doğrulandı. Doğrudan sayfa açılışı hata verdi; yayıncının indekslenmiş içeriği erişilebildi. Farklı görev/veri/ölçüt nedeniyle makaledeki skorla doğrudan yarışılmıyor. |
| [Zerveas ve ark., yazar deposu](https://github.com/gzerveas/mvts_transformer) ve [arXiv](https://arxiv.org/abs/2010.02803) | Çok değişkenli zaman serisinde Transformer temsil öğrenmesi öncü çalışması mevcut. Maskeleme ile temsil öğrenmesi bu projenin icadı olarak sunulmuyor. |
| [Roberts ve ark., 2017](https://epub.uni-regensburg.de/39299/) | Yazar kurumu arşivinde DOI, yazarlar, Ecography 40 ve 913–929 doğrulandı. Yapısal bağımlılığı dikkate alan değerlendirmeyi destekler; 5 km'nin evrensel yeterlilik garantisi değildir. |
| [Breiman, 2001](https://link.springer.com/article/10.1023/A:1010933404324) | Random Forests, Machine Learning 45, 5–32 ve DOI yayıncıdan doğrulandı. |
| [Guo ve ark., 2017](https://proceedings.mlr.press/v70/guo17a.html) | Dört yazar, PMLR 70, 1321–1330 doğrulandı. Kalibrasyon ile sınıflandırma başarısının ayrı değerlendirilmesi uygundur. |
| [Tseng ve ark., Presto](https://arxiv.org/abs/2304.14065) | Altı yazar, başlık, v1'in 2023 ve v4'ün 5 Şubat 2024 tarihi doğrulandı. Kaynakçada “2024, v4” yazılması savunulabilir; ilk yayın yılı 2023'tür. Hazır Presto modeli bu deneyde karşılaştırılmadı. |
| [Saget ve ark., 2025](https://proceedings.mlr.press/v292/saget25a.html) | TerraBytes ICML Workshop, PMLR 292, 32–45 doğrulandı. Tarımsal Sentinel-2 görevlerinde contrastive zaman artırmasıdır; orman görevi için doğrudan başarı kanıtı değildir. |

Mevcut kaynakçada sonucu değiştiren somut bir künye yanlışı veya uydurma referans bulunmadı. Dergi biçimlendirmesinde Schröder, Cornuéjols ve Gançarski gibi aksanlı yazar adlarının resmî yazımı korunabilir; mevcut ASCII yazım bilimsel sonucu etkilemez. Veri DOI'si `10.57967/hf/7983` ayrıca veri erişim satırına eklenebilir; veri revision'ı zaten sabittir.

## 5. Blokajlar ile tamamlanmış işleri ayırma

**Hocayla araştırma değerlendirmesi için kritik veri/hesap blokajı bulunmadı.** “Tamamlandı” sözü; mevcut geriye dönük ikili deney, kayıtların analizi, makale taslağı ve önceki eğitilmiş modelin mühendislik ürünü için kullanılabilir.

| Hedef | Durum | Gereken tamamlayıcı iş |
|---|---|---|
| Hocaya yöntem ve bulguları sunmak | Hazır | Sonuçlar ve sınırlar birlikte anlatılmalı |
| Yeni bir SSL mimarisi veya genel üstünlük iddiası | Desteklenmiyor | Mevcut bulgularla böyle bir iddia kurulamaz |
| Türkiye'ye veya yeni ülkeye aktarım başarısı | Henüz ölçülmedi | Ayrı coğrafyadan yeterli kesim ve stabil örneği, uygun ön işleme ve kilitli değerlendirme gerekir |
| Sürekli haritada hata oranı / operasyonel alarm | Henüz ölçülmedi | Temsil edici mekânsal örnekleme, uygulama eşiği ve bağımsız etiket gerekir |
| Dergiye gönderim | Yazar değerlendirmesi bekliyor | Gerçek yazarlar, katkılar, kurum/fon/çıkar beyanları, hedef dergi biçimi ve kod/veri arşiv kararı gerekir |
| Her çapraz-kat ağırlığını doğrudan teslim etmek | Sağlanmıyor | Bu ağırlıklar saklanmamış; kayıt, tarif, tohum ve tahminler mevcut. Gerekirse ayrı yeniden eğitimle üretilebilir |

Kullanılmamış konum taramasındaki 111 uygun pencerenin yalnızca biri kesimdir. Bu nedenle skor üretilmemesi doğru karardır. Aynı kaynaktan gelen bu pencere kümesi, yeterli sayıda kesim içerse bile bağımsız saha verisi olmazdı.

Önceki `advanced_v3` ürününün 486 konumluk testi daha önce incelenmiştir ve kalibre edilmiş bir topluluğa aittir. `paper_v4` sabit eşikli tekil modellerin farklı değerlendirmesidir. Ürünün 0,9187 macro-F1'i, makalenin 0,9299 CNN ortalaması veya %20 etiket sonucu ile tek bir liderlik tablosunda birleştirilmemelidir.

## 6. Sonraki araştırma kararı

Bugünkü teslimi güçlü kılan şey yeni denemeler ekleyip en iyi skoru seçmek değildir; tanımlı deneyin tamamını denetlenebilir biçimde sunmaktır. Hocayla sonraki aşama kararlaştırılırsa en değerli ek çalışma, hedef bölgeden bağımsız ve iki sınıfta yeterli destek içeren bir doğrulama kümesidir. Mekânsal yarıçap duyarlılığı, ülke dışarıda bırakma ve Presto karşılaştırması farklı soruları yanıtlayan ek çalışmalardır; mevcut protokolün içine geriye dönük eklenip başlangıçtan planlanmış gibi sunulmamalıdır.

Bu rapor, AI destekli teknik denetimdir; hakem değerlendirmesi veya insan araştırmacı onayı yerine geçmez. Denetlenen dosyaların özet hash'leri, kaynak doğrulama notları ve kapsam kararları `reports/final_science_review.json` içinde tutulur.
