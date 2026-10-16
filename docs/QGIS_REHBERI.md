# CBS ve QGIS: ilk inceleme

## Kavramları proje üzerinden anla

CBS, konumu olan veriyi saklama, birlikte gösterme ve sorgulama sistemidir. Uzaktan algılama, yeryüzü hakkında sensörden bilgi üretir. Bu projede uydu ölçümü uzaktan algılama verisi; olay poligonu, görüntü ve bozulma haritasını aynı yerde karşılaştırmak CBS işidir.

Raster hücre ızgarasıdır: uydu bandı veya sınıf kodu. Vektör nokta/çizgi/poligondur: etiket noktası, sınır veya olay alanı. CRS koordinatların ne anlama geldiğini söyler; EPSG:4326 derecedir, metre değildir. QGIS bunları incelemek, üst üste getirmek, kesmek, sembolleştirmek ve harita üretmek için kullanılan açık kaynak uygulamadır. [QGIS rehberi](https://docs.qgis.org/3.44/en/docs/gentle_gis_introduction/introducing_gis.html)

Optik Sentinel-2 güneşten yansıyan enerjiyi ölçer; bitki ve yanık alan incelemesine yarar, bulut/gölge sorunları vardır. S2A 2015'te başlamıştır; 13 bant aynı çözünürlükte değildir (10/20/60 m). Sentinel-1 aktif C-band SAR'dır; gece ve bulut koşullarında gözlem sağlayabilir, yüzey yapısı ve nemle ilişkilidir. [ESA S2](https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-2), [ESA S1](https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Introducing_Sentinel-1)

Landsat uzun tarihsel arşiviyle 2000'li yılları incelemeye uygundur; Landsat 8'in multispektral çözünürlüğü 30 m'dir. NASA ve USGS görev programında birlikte rol alır; ESA Avrupa uzay ajansıdır. Sentinel Asia, Copernicus Sentinel uydu ailesiyle aynı şey değildir: JAXA'nın önemli rol oynadığı Asya-Pasifik afet bilgi paylaşımı işbirliğidir. [USGS](https://www.usgs.gov/landsat-missions/landsat-8), [JAXA](https://earth.jaxa.jp/en/application/disaster/sentinel-asia/index.html)

## Hazır veriyi QGIS'te aç

1. QGIS'i aç. `data/processed/GFC30_inspection.tif` dosyasını sürükle. Yanındaki `.qml` otomatik yüklenmezse Layer Properties → Symbology → Style → Load Style ile seç.
2. “Identify Features” ile en az 10 hücreye tıkla; gerçek sınıf kodunu ve lejandını karşılaştır. Harita model çıktısıdır, fotoğraf değildir.
3. Layer Properties → Information altında EPSG:4326, boyut ve piksel aralığını kontrol et. NoData tanımı bulunmadığını kaydet. 0'ı “sağlam orman” kabul etme.
4. `GFC22_inspection.tif` ile karşılaştır. Seçili pencereler bilerek yoğun kod içeren alanlardır; küresel istatistik üretmek için kullanma.
5. `data/processed/dnbr.tif` aç. Singleband pseudocolor; sıfırı ortalayarak negatiften pozitife yeşil-sarı-kırmızı skala kullan. Bu raster EPSG:32635, 20 m griddedir. Boş alanlar geçersiz gözlemdir.
6. `ndvi_before.tif`, `ndvi_after.tif` katmanlarını ekle. Aynı renk aralığını kullan; sadece otomatik min/max'a bakarak değişim çıkarma.
7. Katman grubunu `qgis/inceleme.qgz` olarak kaydet. İki GFD örneği Türkiye'de değildir; Sentinel demosuyla üst üste gelmeleri beklenmez.

QGIS uygulaması bu çalışma sırasında canlı olarak açılıp doğrulanmadı. GeoTIFF'lerin CRS, grid, piksel değerleri ve stil XML'leri programatik kontrol edildi; yönergeyle QGIS incelemesi yapılabilir.

## Ne indirildi, nereden?

Figshare `28465178` v1: toplam altı büyük ZIP içinden `GFC0/GFC22.tif` ve `GFC0/GFC30.tif`. Seçim coğrafi temsil değil, küçük ve indirilebilir örnek hedefiyle yapıldı. Arşiv ve üye bağlantıları/hash kayıtları `data/metadata/` altında. Kesitler `audit_gfd.py` tarafından 512×512 pencerelerden üretilir; tüm piksel sayımları asıl dosyalardan yapılır.

Sentinel-2: Element 84 [Earth Search](https://github.com/Element84/earth-search) açık kataloğunda sabit bir Marmaris çevresi kutusu, Temmuz/Ağustos 2021. İndirme tüm sahne yerine COG içinden küçük pencere okur. Görüntü tarihi ve işleme tarihi farklıdır; sahne JSON'ları saklanır.

Kendin veri aramak için [Copernicus Browser](https://browser.dataspace.copernicus.eu/) veya Landsat için [USGS EarthExplorer](https://earthexplorer.usgs.gov/) kullanılabilir. Hesap ve indirme koşulları hizmete göre değişir; mevcut demo indirmesi hesap gerektirmedi.

## İlk incelemenin çıktısı

Bir ekran görüntüsü yerine şu bilgileri kaydet: alan koordinatı, tarih, CRS, bandın fiziksel birimi, NoData/mask bilgisi, görülen sınıf kodları ve kaynağın sürümü. GFD piksel sayısını sabit 900 m² ile çarpma: dosyanın grid aralığı derece cinsinden; alan için uygun eş-alan projeksiyonu veya jeodezik hesap gerekir.

NDVI=(NIR-red)/(NIR+red), NBR=(NIR-SWIR2)/(NIR+SWIR2). dNBR=önce NBR-sonra NBR. Pozitif fark tek başına yangın veya ağaç kaybı kanıtı değildir. Fenoloji, nem, tarım, geometrik hata ve kalite maskesi etkileri kontrol edilir.

## Sürüm 2: gerçek modelin test noktaları

`reports/real_experiment/test_predictions.geojson` dosyasını QGIS'e sürükle. CRS EPSG:4326; `truth`, `prediction`, `score`, `correct`, `year` alanları bulunur. `correct` alanına göre kategorik sembolleştirme hataları görünür yapar. Bunlar 486 test noktasının tahminidir; sürekli raster veya Türkiye haritası değildir. Kaynaklar arasında minimum mesafe kontrolü ayrı rapordadır. Bu sürümde de QGIS canlı arayüz kontrolü yapılmadı.
