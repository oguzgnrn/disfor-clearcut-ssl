# Son teslim — 26 Eylül 2026

Bu sürüm, gerçek veriyle tamamlanmış bir araştırma MVP'sidir. Toplantıda önce `reports/demo.html`, ardından yedi sayfalık toplantı dosyası açılabilir. E-posta taslağı `TOPLANTI_REHBERI.md` içinde; gönderilmedi.

## Tamamlanan kapsam

- Kaynak veriden 2.213 gerçek, yüksek güvenli Sentinel-2 zaman serisi hazırlandı.
- En az 5 km mesafe ve kaynak olay grupları korunarak eğitim / validation / test ayrıldı.
- Random Forest, Transformer ve SSL Transformer aynı etiket bütçelerinde 36 koşulda karşılaştırıldı.
- Validation ile seçilen yöntemden sabit seed 7 modeli kaydedildi. Etiketsiz yeni NPZ girdisi kabul eden tahmin komutu hazır.
- 486 test örneğinin model tahminleri, hata analizi, GeoJSON noktaları ve bant eğrileri teslim edildi.
- 1.000 mekânsal grup bootstrap tekrarı ve gözlem kaybı deneyleri tamamlandı.
- 18 otomatik test, veri hash kontrolleri ve 486 örneğin çıkarım eşleşmesi geçti.
- PDF'nin yedi sayfası görsel olarak incelendi. Tarayıcıda kaçırılan 12 kesim filtresi, zaman serisi grafikleri ve hata günlüğü kontrol edildi.
- Tam kod/veri/model arşivi ve küçük sunum arşivi üretildi; CRC ve SHA-256 kayıtları `output/package_manifest.json` içinde.

## Hocaya söylenecek temel sonuç

“Gerçek etiketli veride coğrafi ayrımlı bir kesim sınıflandırıcısı kurdum. Dağıttığım modelin test macro-F1'i 0,861; 38 kesimin 26'sını buluyor. Az etikette Random Forest güçlü kaldı, bu SSL ön eğitiminde tutarlı kazanç gösteremedim. Hataları ve tekrarlanabilir kodu birlikte getirdim.”

## İddia edilmeyenler

Bu teslim Türkiye saha doğrulaması, gerçek Sentinel-1 füzyonu, tüm bozulma türlerinin sınıflandırılması, yangın erken uyarısı veya yayıma kabul edilmiş makale değildir. Bu alanlara genişlemek yeni veri ve ayrı deney gerektirir. Buradaki başarım yalnızca belirtilen veri hazırlığı, görev ve coğrafi ayrım için ölçülmüştür.
