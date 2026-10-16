# Çalıştırma ve karar kaydı

26 Eylül 2026. Bu dosya yapılanları ve yapılmayanları ayırır.

## Gerçek veri

1. Figshare API'den v1 metadata indirildi. Altı ZIP'in yalnızca birinden iki küçük GeoTIFF, Range istekleriyle çıkarıldı. ZIP okuma CRC kontrolünü, yerel manifest SHA-256 kontrolünü içerir.
2. GeoTIFF'lerin tamamı 512 hücrelik bloklarla sayıldı. 0 kodu baskın ve NoData tanımı yok. Alan istatistiği üretilmedi. En yoğun kod içeren pencere yalnızca görselleştirme için kesildi.
3. İlk Sentinel AOI [28.16,37.00,28.20,37.04] idi. Komşu 35SNB karosu ve ardından 35SPA ile düşük ortak geçerli gözlem elde edildi. Kalite sonuçları `reports/sentinel_low_coverage_attempt.json` ve `reports/sentinel_coastal_attempt.json` içinde; kaynak sahne metadata'ları `data/metadata/rejected_*` klasörlerinde saklandı.
4. Gösterim için alan [28.30,36.88,28.34,36.92] olarak değiştirildi. Bu bir eğitim/test bölgesi veya sistematik olay örneklemesi değildir. Görüntü kalitesine göre seçilen keşif örneğidir. Nihai tarih aralıkları Temmuz/Ağustos 2021, karo 35SPA, orijinal baseline<4 ürünlerdir. Bulut oranı en düşük sahneler seçildi; ilk 100 STAC sonucu sınırı metadata'da kayıtlıdır.
5. Son örnekte 40.950 hücrenin 40.380'i ortak geçerli (%98,6). dNBR medyanı yaklaşık -0,0314; dNBR>0,20 yalnızca 1 piksel (0,04 ha). Bunu bir yangın tespiti sonucu diye sunmuyoruz. Negatif/belirsiz değişim de meşru bir inceleme sonucudur.

## Öğrenme hattı

- Sentetik üretim seed'i: 2026. Model seed'leri: 7,17,27.
- Grup ayrımı seed'leri: 1729/1730. Ayrım bütçe ve model tekrarlarında değişmez.
- %5/%10/%20/%100 eğitim etiketi; sınıf bazında yukarı yuvarlama nedeniyle gerçek örnek sayısı nominal orandan biraz fazla olabilir. Sayılar her koşulda `n_labeled` alanında kayıtlıdır.
- Toplam 36 koşul, 30 ön eğitim ve 25 fine-tune epoch. Sonuç görülerek hiperparametre taraması yapılmadı. Grafik bütün yöntemleri ve bütçeleri içeriyor.
- Test etiketleri yalnızca değerlendirmede kullanılır; sınıfların splitlerde bulunması için yapılan teknik kontrol veri toplama yeterliliği kontrolüdür. Model seçiminde test skoru kullanılmaz.
- RF nesnesi diske kaydedilmedi; Transformer checkpoint'leri, seçilen epoch, confusion matrix, test tahminleri, etiketli örnek ID'leri, veri hash'i ve çalışma süresi kaydedildi.
- Sentetik grup ayrımı, gerçek coğrafi ayrımın uygulanabilirliğini kontrol eder; sentetik grupların fiziksel coğrafyası yoktur.

## Kontroller

- `tests/test_pipeline.py`: 9 test geçti.
- `scripts/verify_outputs.py`: kaynak hash'leri, ortak UTM grid, indeks ve maskeler, eşik sayımları, hektar dönüşümü, GFD tam sayımları ve QML XML kontrolü geçti.
- Tarayıcıda gerçek harita yüklendi. Eşik 0,20'den 0'a değiştirildiğinde 1 piksel/0,04 ha → 1.530 piksel/61,20 ha oldu; Python sayımıyla eşleşti.
- PDF 7 sayfa olarak üretildi ve tüm sayfaları görüntüye dönüştürülerek görsel kontrol edildi.
- QGIS'in kendisi açılmadı; hazırlanmış veri ve yönerge sunuldu.

## Tekrarlanabilirlik sınırları

Paket içindeki yerel veriyle tekrar çalışmak internet gerektirmez. Uzak COG ve kataloglar daha sonra güncellenebilir; yeniden indirmede kaynak hash'leri karşılaştırılmalıdır. Sistemler arası Torch/BLAS farkları küçük sayısal farklılıklar yaratabilir. Sabit seed, farklı donanımda bit düzeyinde aynı sonuç garantisi değildir.

PDF üretimi için `reportlab`, `pypdf` ve DejaVu Sans fontları gerekir. Mevcut ortamda Codex'in belge çalışma zamanı kullanıldı. `scripts/build_pdf.py` için `ORMAN_FONT_DIR` ayarıyla font konumu değiştirilebilir; basılı PDF ve HTML demo zaten hazırdır.
