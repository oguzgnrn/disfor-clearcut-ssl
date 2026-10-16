# Orman-SSL ürün kılavuzu

Orman-SSL, gerçek Sentinel-2 zaman serilerini incelemek ve eğitimli modeli ham gözlemler üzerinde çalıştırmak için hazırlanmış yerel bir araştırma ürünüdür. Arayüz, daha önce incelenmiş 486 DISFOR örneğini açar. Uygulama internete bağlanmaz; veri, model ve sonuçlar bilgisayarınızda kalır.

## Ürünü aç

Mac'te proje klasöründeki **URUNU_AC.command** dosyasına çift tıklayın. Terminal penceresi ve tarayıcı açılır. Terminal açık kaldığı sürece ürün çalışır.

Terminal alternatifi, proje kökünden:

```bash
.venv/bin/python scripts/serve_product.py --open
```

Adres: `http://127.0.0.1:8765`. Durdurmak için sunucu terminalinde **Ctrl+C** kullanın. Başka bir uygulama 8765 portunu kullanıyorsa:

```bash
.venv/bin/python scripts/serve_product.py --port 8766 --open
```

Bu arayüz doğrudan HTML dosyasına çift tıklayarak çalışmaz; yukarıdaki yerel sunucu gerekir. Tüm stil, grafik ve uygulama kodu paket içindedir; çevrimiçi harita, font veya CDN bağımlılığı yoktur.

## Toplantıda beş dakikalık gösterim

1. **Örnekleri keşfet:** 486 kayıt ve kesim tahmini sayısını gösterin. Sayılar mevcut filtreleri izler; filtreli görünüm tüm veri kümesinin ölçümü değildir.
2. **Noktaya veya listedeki örneğe tıklayın:** gerçek konumu, 24 aylık gözlem penceresini, kesim skorunu ve gözlenen ayları birlikte inceleyin.
3. **Spektral izi okuyun:** kırmızı B04, yakın kızılötesi B08 ve kısa dalga kızılötesi B12 bantları kaynak DN birimindedir. Boş aylarda çizgi kesilir; eksik gözlem sıfır kabul edilmez. Grafik, modelin kullandığı 10 bandın üçüne odaklanır.
4. **Örnek veride analizi çalıştır:** sistem ham DISFOR Parquet gözlemlerini yeniden okur, aylık kalite maskesini uygular ve kayıtlı 10 modeli çalıştırır. Bu düğme gerçek çıkarım başlatır; önceden yazılmış bir animasyon göstermez. Model yeniden eğitilmez. İşlem sürerken sayfada örnekleri inceleyebilirsiniz.
5. **Sonucu teslim edin:** tamamlandığında JSON, GeoJSON ve kaynak/bütünlük kaydını indirin. GeoJSON, QGIS'e nokta katmanı olarak eklenebilir. “Geçmiş değerlendirme” alanından referans etiketlerle yapılan önceki ölçümü ayrı açın.

## Kontroller

- **Arama:** DISFOR örnek kimliğine veya kaynak örnek numarasına göre süzer.
- **Tahmin filtresi:** kesim veya bozulmamış orman model kararlarını gösterir.
- **Yıl filtresi:** 24 aylık pencerenin ikinci yılını seçer. Örneğin 2020 seçimi, Ocak 2019–Aralık 2020 pencerelerini gösterir.
- **Sıralama:** kesim skoru veya model üyeleri arasındaki standart sapmaya göre sıralar. Yüksek üye farkı inceleme önceliği oluşturabilir; bir doğruluk ölçüsü veya güven aralığı değildir.
- **Konum görünümü:** WGS84 boylam/enlem koordinatlarından üretilir. Noktalar gerçek konumlardır. Altlık harita, idari sınır veya arazi örtüsü katmanı yoktur. Yakınlaştırma seçili noktaya odaklanır; “Sığdır” filtreli noktaların tümünü gösterir.
- **Kalite:** her yılda en az altı gözlenen ay gerekir. Aylık hazırlamada kaynak `clear` alanı ile SCL 4/5 birlikte kullanılır. Kalite uygunluğu, sınıf tahmininin doğruluğunu kanıtlamaz.
- **İndirme:** ekran filtresinden bağımsız olarak aktif analizin tüm 486 örneğini indirir. İlk açılışta kayıtlı sonuçlar; başarılı çalıştırmadan sonra yeni üretilen sonuçlar sunulur.

## Sürümler ve bilimsel kapsam

| Bileşen | Sürüm / anlam |
|---|---|
| Çalıştırılan model | `advanced_v3`: beş SSL Transformer + beş CNN üyesi |
| Ürün arayüzü | `1.1`: yerel inceleme, ham veriden demo çıkarımı ve etiketsiz NPZ yükleme |
| Güncel araştırma | `paper_v4`: farklı protokolle yapılan coğrafi çapraz doğrulama ve kontrol deneyleri |
| Veri | DISFOR sabit revision `2562332e35c94c2339aeb341ffaed2a99faae7d6`; EUPL-1.2 |
| Örnek kümesi | Önceden incelenmiş 486 tarihsel test penceresi |

Ana ekranda referans etiket kullanılmaz. Kesim skoru, geliştirme kümesinde kalibre edilmiş model çıktısıdır; karar eşiği 0,50 olarak korunur. Eşik arayüzden değiştirilmez. Aylık grafikte kaynak DN gösterilir; fiziksel yansıtım veya düzeltilmiş NDVI iddiası yapılmaz.

“Geçmiş değerlendirme”, kayıtlı model kartındaki ayrı ölçümü gösterir: macro-F1 0,9187; 38 referans kesimin 28'i bulunmuş, 10'u kaçırılmış; 448 referans orman örneğinde sıfır yanlış kesim alarmı ölçülmüştür. Macro-F1, yüzde doğruluk değildir. Bu örnekler daha önce incelendiği için sonuçlar bağımsız dış saha doğrulaması sayılmaz. `paper_v4` deney sonuçları bu ensemble sonucu ile aynı deney değildir.

Ürün 24 aylık pencereden geriye dönük kesim sınıflandırması yapar. Türkiye saha performansı, yangın erken uyarısı, bütün orman bozulma türleri veya sürekli ülke haritası doğrulanmış değildir. Uygulamadaki koordinat noktaları herhangi bir bölgenin kesintisiz haritası anlamına gelmez.

## Çıktılar ve yeniden üretim

Başarılı arayüz çalıştırması yalnızca `output/product_demo/` alanında şu dosyaları üretir:

- `input.npz`: etiketsiz 24 aylık model girdisi ve gözlem maskesi.
- `predictions.json`: kimlik, tahmin sınıfı, skor, kalite ve üyeler arası fark.
- `predictions.geojson`: gerçek WGS84 noktaları ve tahmin alanları.
- `manifest.json`: kaynak, örnek bilgileri ve SHA-256 kayıtları.
- `inference.log`: çıkarım işleminin yerel günlüğü.

İlk açılış `output/advanced_prediction/` altındaki doğrulanmış kayıtlı sonuçları okur. Sunucu, model/pencere/girdi/tahmin hash'lerini ve kimlik sırasını kontrol eder; uyuşmazlık varsa sonuçları sessizce göstermez. Aynı sunucu çalışırken başarılı analiz yeni çıktıya geçer. Sunucu yeniden başlatıldığında tekrar kayıtlı başlangıç çıktısı açılır; demo çıktı dosyaları diskte kalır. Başarısız çalıştırma önceki geçerli görünümü korur.

Model ağırlıkları, eğitim kayıtları ve araştırma çıktıları ürün tarafından değiştirilmez. Aynı anda tek çıkarım işi çalışabilir; süre sınırı 10 dakikadır. Sayfayı kapatmak süren işi iptal etmez; sunucu terminalini kapatmadan önce işlemin bitmesini bekleyin.

## Kendi verini arayüzden yükle

1. **Kendi verini yükle** düğmesine basın, hazırlanmış etiketsiz `.npz` dosyasını seçin.
2. Dosyada `metadata.source` yoksa **Veri kaynağı ve DN işleme geçmişi** alanını doldurun. Alanı doldurursanız bu açıklama yeni analiz kaydında kullanılır; dosyadaki eski metin değiştirilmez.
3. **Dosyayı doğrula ve analiz et** düğmesine basın. Boyut, sıkıştırılmış arşiv, dizi başlıkları, bant sırası, birim, maske ve takvim sözleşmesi doğrulanır; ardından kayıtlı advanced_v3 modeli gerçekten çalışır.
4. Başarıyla tamamlanan analiz **Aktif veri** alanında **Son yüklenen veri** olarak açılır. **Paketli demo** seçeneği önceki demo görünümüne geri döner. Bu oturumda son yükleme tekrar seçilebilir.

Henüz kendi girdiniz yoksa yükleme penceresindeki **Uyumlu örnek NPZ indir** bağlantısıyla hazır etiketsiz örneği alın. Bu dosya eski 486 test girdisidir; yeniden yüklemek yeni bağımsız veri oluşturmaz.

Yükleme sınırları: sıkıştırılmış dosya en fazla **16 MiB**, açılmış diziler toplamı **64 MiB**, örnek sayısı **1–5.000**. Gereken alanlar `x`, `observed`, `days`, `ids`, `metadata` olarak kalır. `ids` en fazla 128 karakterlik Unicode kimliklerden oluşur. `metadata` tek JSON metnidir ve `channels`, kaynak DN için birebir `units` açıklaması ile kaynak bilgisi içerir. `y`, `groups`, nesne/pickle dizileri ve açıklanmamış ek alanlar reddedilir. Bu arayüz model dosyası yüklemez.

İsteğe bağlı alanlar:

| Alan | Biçim | Görünüm |
|---|---|---|
| `lon` ve `lat` | Birlikte, N uzunluğunda sonlu WGS84 dizileri | Yüklenen gerçek konumlar |
| `target_year` | N uzunluğunda 1901–9998 arası tam sayı; `days` ile uyumlu | Pencerenin ikinci takvim yılı |

Bu alanlar yoksa kimlikten konum veya yıl tahmin edilmez. Mekânsal görünüm konum bulunmadığını söyler; GeoJSON boş nokta koleksiyonudur. Grafik **1–24. ay** olarak açılır. Gerçek etiket yüklenmez ve yeni veride doğruluk ölçümü yapılmaz. **Geçmiş değerlendirme**, yüklenen veriden bağımsız olarak eski 486 örneği gösterir; bir tarihsel hata kimliğine tıklamak önce demo kümesine geri döner.

Her başarılı yükleme `output/product_uploads/run-…/` altında `input.npz`, `predictions.json`, `predictions.geojson`, `manifest.json`, `inference.log` üretir. Yeni yükleme eskisini veya demo dosyalarını değiştirmez. Yarım veya hatalı sonuç aktif hale getirilmez. Seçici, sunucunun mevcut oturumundaki son yüklemeyi tutar; sunucu kapanınca başlangıç yeniden demo olur. Eski başarılı yüklemelerin dosyaları diskte korunur. Bu kullanıcı girdileri teslim ZIP'lerine otomatik dahil edilmez.

Boyut ve biçim denetimleri fiziksel sensör uyumunu kanıtlamaz. Başka kaynaktaki sayısal değerleri yalnız `units` metnini değiştirerek uygun hale getiremezsiniz; kaynak DN işleme geçmişinin gerçekten eşleşmesi gerekir.

## Ham gözlemlerinden yeni girdi hazırlama

Henüz NPZ hazırlamadıysanız etiket gerektirmeyen komut satırı girişini kullanın; veri sözleşmesi `docs/VERI_SOZLESMESI.md` içindedir:

```bash
.venv/bin/python scripts/run_advanced.py \
  --observations /tam/yol/observations.parquet \
  --windows /tam/yol/windows.json \
  --source 'Veri kaynağı ve DN işleme geçmişi' \
  --out output/my_prediction
```

Gözlem tablosunda `sample_id`, `timestamps`, `clear`, `SCL` ve 10 bant gerekir. Pencere JSON'unda `id`, `sample_id`, `target_year` kullanılır; GeoJSON için WGS84 `lon`/`lat` eklenir. Biçim örneği `data/examples/inference_windows.json` dosyasındadır. Kaynak ve DN işleme uyumu sağlanmalıdır; program bir kaynak beyanından fiziksel sensör uyumunu kanıtlayamaz. Bu komutun ürettiği `input.npz` dosyasını ardından arayüzden yükleyebilirsiniz. Komutun konum ve yıl bilgisi ayrı pencere dosyasında kaldığı için temel NPZ yüklemesinde göreli aylar ve konumsuz görünüm açılır; yukarıdaki isteğe bağlı diziler sağlanırsa bu bilgiler de görünür.

## Kurulum ve sorun giderme

- **Python ortamı bulunamadı:** proje kökünde `bash scripts/setup.sh` çalıştırın. İlk bağımlılık kurulumu internet gerektirebilir; kurulu model, veri ve ortamla ürün çevrimdışı çalışır.
- **Eksik veri/model:** tam proje paketini kullanın. `models/advanced_v3/`, `data/disfor/pixel_data.parquet`, `data/examples/inference_windows.json` ve kayıtlı `output/advanced_prediction/` çıktıları gerekir.
- **Bütünlük uyuşmazlığı:** dosyaları elle düzeltmeyin. Proje kökünde `.venv/bin/python scripts/run_advanced.py` komutuyla başlangıç çıktısını tekrar üretin, ardından ürünü açın.
- **Analiz başarısız:** `output/product_demo/inference.log` dosyasını inceleyin. Ana ekran önceki geçerli sonuçları korur; başarılı analiz gibi göstermez.
- **Sayfa yüklenemiyor:** sunucu terminali açık olmalı. Gösterilen yerel adresteki portu kontrol edin; gerekirse yukarıdaki `--port 8766` seçeneğini kullanın.

Sunucu yalnızca `127.0.0.1` adresinde dinler. İzin verilen yollar sabittir; keyfi dosya okuma, model dosyası yükleme, çıktı yolu değiştirme veya uzaktan model çalıştırma API'si yoktur. Yalnız sınırlandırılmış etiketsiz NPZ yükleme desteklenir. Tarayıcıdan çalışma isteği aynı köken ve oturum anahtarıyla doğrulanır. Dış ağda yayımlamak için hazırlanmış bir sunucu değildir.

## Doğrulama

Ürün testleri veri/konum eşleşmesini, maskeli aylarda boş değer korunmasını, hash uyuşmazlığı reddini, izinli API yollarını, yerel erişim ve çalışma isteği doğrulamasını, tek iş sınırını, NPZ boyut/sıkıştırma/dtype kontrollerini, yüklenen verinin tarihsel ölçümden ayrılmasını ve başarısız işte önceki sonuçların korunmasını kapsar:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_product.py' -v
```

Bu testlerin geçmesi modelin dış sahada doğrulandığı anlamına gelmez; ürünün veri ve işlem sözleşmelerini kontrol eder.
