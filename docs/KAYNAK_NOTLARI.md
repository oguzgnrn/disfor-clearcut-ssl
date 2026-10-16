# Kaynak notları ve kanıt durumu

Erişim: 26 Eylül 2026. Kaynakların bildirdiği sonuçlarla bu projenin ürettiği sonuçlar farklıdır. Aşağıdaki kısa özetler, bir reprodüksiyon yapıldığı anlamına gelmez.

## 1. Küresel orman bozulması ürünü

Wang ve ark. (2026), [Global high-resolution forest disturbance type dataset](https://essd.copernicus.org/articles/18/1601/2026/), ESSD, DOI: 10.5194/essd-18-1601-2026. Tam HTML incelendi. Çalışma 2000-2020 için 30 m ürün; Landsat/CCDC, yardımcı değişkenler ve CART kullanıyor. Yayımlanmış metin 57.000 örnek ve %99 genel doğruluk bildiriyor; eğitim/validation ayrımı 7:3. Bu oran coğrafi aktarım başarımız değildir. Makale kuraklık ve hastalık gibi zayıf bozulmaları dışarıda bırakıyor.

[Figshare v1](https://doi.org/10.6084/m9.figshare.28465178) açıklaması ise 16.000 doğrulama örneği, %95 doğruluk ve farklı sınıf oranları veriyor. Kod 0 burada “other disturbance”, makalenin örnek sınıflarında “undisturbed”. Makale anlatımında sel için 19 yazılan bir yer var; Figshare seli 20 olarak tanımlıyor. Kaynak sürümü ve sınıf sözlüğü yazarlarla netleştirilmeli; sıfır sınıfı otomatik negatif etiket yapılmamalı.

Yerel denetim, makale iddiasından bağımsız bir gözlemdir: iki örnek GeoTIFF'te CRS EPSG:4326, dtype int16, NoData tanımı yok. Dosyalardaki kodlar `reports/gfd_audit.json` içinde tam sayılmıştır. Örnekler küçük dosya boyutları nedeniyle seçildi; küresel temsili örneklem değildir.

## 2. Ana SSL çalışması

Zhang ve ark. (2025), [Self-supervised deep learning for detection of forest disturbance types in a subtropical ecosystem using transformer and Sentinel-1 and Sentinel-2 time series data](https://doi.org/10.1080/17538947.2025.2537325). DOI ve yazar bilgisi Crossref'ten doğrulandı. Yayıncı PDF/HTML doğrudan erişimi 403 verdi; yayıncının arama indeksindeki özet ve 3.2.2 bölümü görülebildi. Tam yöntem ve ek dosyalar eksiksiz okunmuş değildir.

Erişilen metin, düzensiz Sentinel-2 zamanları için konumsal kodlama, Sentinel-1/2 birleştirme ve SSL yaklaşımını anlatıyor. Kesim ve hastalık tespiti için F1 0,95 bildiriliyor. %20 eğitim verisinde 0,95/0,86 karşılaştırması var; bölüm çevresinde “overall F1” ile “accuracy” adlandırmaları birlikte geçtiğinden ana tablodaki metrik tanımı tekrar denetlenmeli.

**Bizim çıkarımımız:** benzer bir az etiket sorusunu coğrafi ayrım ve eksik gözlem deneyleriyle araştırabiliriz. Mevcut maskeli-rekonstrüksiyon Transformer uygulamamız IRMST'nin birebir kopyası değildir. Bölge, tüm veri yılları, SSL kaybının kesin ayrıntıları, örnek bağımsızlığı, hiperparametreler ve kod/veri paylaşımı tam metinden kontrol edilecek.

## 3. Nil Deltası / tarım sınıflandırması

Maze ve ark. (2025), [Enhanced agricultural land use/land cover classification in the Nile Delta using Sentinel-1 and Sentinel-2 data and machine learning](https://doi.org/10.1016/j.isprsjprs.2025.08.019). Yayıncı özeti ve bölüm özetleri erişilebilir. Sentinel-1/2 ile piksel tabanlı tarım/arazi örtüsü sınıflandırması; XGB için %94,4 OA, bağımsız harita değerlendirmesinde RF için %91,4 OA bildiriliyor. Bunlar farklı değerlendirmelerdir ve birleştirilmez. Projeye katkısı: radar/optik katkısını ölçmek ve RF gibi güçlü basit referansları tutmak. Problem doğrudan orman bozulması değildir.

## 4. Sınıflandırma sonrası füzyon

Vyas ve ark. (2024 çevrimiçi / 2025 cilt), [A novel image fusion-based post classification framework for agricultural variations detection using Sentinel-1 and Sentinel-2 data](https://doi.org/10.1007/s12145-024-01506-0). Yayıncı özeti ve veri erişim açıklaması incelendi; tam metin abonelikli. Punjab'da S1 VV/VH ve S2 L2A kullanıyor; GS/PCS füzyonu ve MLC/MDC/SVM karşılaştırıyor. Sınıflandırma ve değişim haritaları için sırasıyla %96,5 ve %92,74 OA bildiriliyor. Çıkarım: iki tarihin ayrı sınıflandırılmasındaki hatalar değişim haritasına taşınabilir; bizim pilotta doğrudan zaman serisi yaklaşımıyla karşılaştırma daha sonraki bir deneydir.

## 5. Teknik birincil kaynaklar

- [ESA Sentinel-2](https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-2): optik bantlar ve görev başlangıcı.
- [ESA Sentinel-1](https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Introducing_Sentinel-1): C-band radar ve gözlem özellikleri.
- [USGS Landsat 8](https://www.usgs.gov/landsat-missions/landsat-8): Landsat görev ve çözünürlük bilgisi.
- [QGIS: GIS'e giriş](https://docs.qgis.org/3.44/en/docs/gentle_gis_introduction/introducing_gis.html), [raster](https://docs.qgis.org/3.44/en/docs/gentle_gis_introduction/raster_data.html), [vektör](https://docs.qgis.org/3.44/en/docs/gentle_gis_introduction/vector_data.html).
- [JAXA Sentinel Asia](https://earth.jaxa.jp/en/application/disaster/sentinel-asia/index.html): afet bilgi paylaşımı işbirliği.
- [Element 84 Earth Search](https://github.com/Element84/earth-search): STAC koleksiyonları ve ölçek/ofset kuralları.
- [Copernicus S2 işleme](https://sentiwiki.copernicus.eu/web/s2-processing): kalite ve ürün işleme bilgisi.
- [Sentinel Hub SCL açıklaması](https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/scene-classification/): sınıf kodları.

## Okuma sırasında kapatılacak sorular

1. Ana SSL makalesinin ön eğitim hedefi, veri bölme yöntemi ve açık kodu nedir?
2. Figshare v1 ile nihai makalenin doğruluk/sınıf farkı hangi sürüm değişikliğinden geliyor?
3. Yıllık olay tarihi veya eğitim/validation noktaları kamuya açık mı?
4. Bizim seçtiğimiz bölgedeki bağımsız doğrulama kaynağı ne olacak?

Kaynak bildirimi ile bizim değerlendirmemiz her notta ayrılmıştır. Tam metne erişemediğimiz yerlerde yöntem ayrıntısı uydurulmamıştır.

## Sürüm 2: gerçek öğrenme verisi

[JR-DIGITAL DISFOR](https://huggingface.co/datasets/JR-DIGITAL/DISFOR), revision `2562332e35c94c2339aeb341ffaed2a99faae7d6`, EUPL-1.2. Gerçek Sentinel-2 serileri, yorumlanmış sınıf segmentleri, güven ve kaynak/grup bilgileri sağlıyor. Bu projede 10 DN bantlı piksel tablosu kullanıldı; büyük görüntü yongası arşivi indirilmedi. Kendi coğrafi ayrımımızı kullandığımız için skor resmi DISFOR benchmark sonucu değildir. Hazırlama ve ölçümler `GERCEK_DENEY_RAPORU.md` içinde; kaynak lisansı ve metadata indirilen dosyalarla korunmuştur.
