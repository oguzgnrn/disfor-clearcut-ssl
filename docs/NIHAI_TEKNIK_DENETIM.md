# Nihai teknik denetim — Orman-SSL

**Denetim tarihi:** 27 Eylül 2026. **Karar:** Mevcut bilimsel sürüm ve eğitilmiş model, incelenen yerel ortamda yeniden üretilebilir ve çalışır durumdadır. Mevcut sürümü teslim etmek için yeniden eğitim gerekmiyor. Nihai paketleme sırasında değişen arşivler yeniden doğrulanmalıdır.

Bu kayıt önceki raporlardaki başarı ifadelerini tekrar etmek yerine komutların bu denetimde yeniden çalıştırılmasına dayanır. Makinece okunabilir kanıt `reports/final_engineering_review.json`, test dökümü `reports/final_engineering_tests.log` içindedir. Ürün arayüzüne sonradan eklenen testler ayrı nihai entegrasyon kontrolüne dahildir; buradaki **45 test**, bu denetimin gerçekten çalıştırdığı çekirdek test kümesidir.

## Gerçekten çalıştırılan kontroller

| Kontrol | Sonuç ve somut kapsam |
|---|---|
| `.venv/bin/python scripts/check_environment.py` | Python 3.11, doğrudan bağımlılıkların sabit sürümleri ve yerel çıkarım için gerekli varlıklar uygun. |
| `.venv/bin/python -m unittest discover -s tests -v` | **45 test geçti**, başarısızlık ve atlanan test yok. Girdi sözleşmesi, maskeler, veri ayrımları, model seçimi, paper protokolü ve arşiv bütünlüğü kapsandı. |
| `.venv/bin/python scripts/verify_paper.py` | **180 koşu ve 79.668 kayıtlı olasılık** doğrulandı. Kod/veri/protokol SHA-256 değerleri, kat kimlikleri, etiketli alt kümeler, eğitim/test ayrımı, OOF yeniden kurulumu ve ölçütler kontrol edildi. Bu sayı 79.668 bağımsız konum anlamına gelmez. |
| `.venv/bin/python scripts/verify_advanced.py` | 24 CV koşusu, 18 düşük etiket koşusu ve 10 nihai üye doğrulandı. Eğitim ve kalibrasyon kimliklerinin testten ayrılması, üye dosya hash'leri, olasılık normalizasyonu ve kayıtlı değerlendirme eşitliği geçti. |
| `.venv/bin/python scripts/smoke_paper_archive.py` | Gerçek compact paper ZIP'i geçici klasöre çıkarıldı. Bir SSL koşusu kaldırılıp **sıfırdan yeniden eğitildi**; orijinal olasılıklarla en büyük mutlak fark **0,0**. Arşivin 8 paper testi de geçti. |
| `scripts/run_advanced.py --out <geçici klasör>` | Ham Parquet gözlemlerinden 486 örnek yeniden hazırlandı. `x`, `observed`, `days`, `ids` hazır NPZ ile birebir aynı. 486 sınıf kararı ve tüm olasılıklar kayıtlı advanced değerlendirmesiyle aynı; en büyük fark **0,0**. |
| Taşınmış model ZIP'inden çıkarım | `Orman_SSL_Nihai_Model.zip` boşluk içeren farklı bir geçici klasöre çıkarılıp paket içindeki CLI çalıştırıldı. 486 örneğin kararları ve olasılıkları ham veri yoluyla aynı; en büyük fark **0,0**. |
| Harita çıktısı | 486 GeoJSON özelliğinin kimliği ve WGS84 noktası giriş pencereleriyle birebir eşleşiyor. |
| Dört teslim ZIP'i | Güvenli arşiv yolları, tekil girişler, CRC, bütün dosyaların SHA-256/uzunlukları ve manifest kapsamı geçti. |
| Araştırma sayfası bağlantıları | `reports/paper_v4.html` içindeki 8 yerel bağlantı çalışma klasöründe ve onu içeren üç arşivde mevcut. Önceki demo sayfasındaki 4 yerel bağlantı da mevcut. |

Tam test dökümü ve arşivlerin bu kontroldeki SHA-256 değerleri JSON kaydında tutulur. Sonradan üretilen bir ZIP, aynı dosya adını taşısa bile bu eski hash'in kapsamına girmez.

## Çıkarım sözleşmesi

Ürün iki tam takvim yılına ait **24 aylık, 10 bantlı Sentinel-2** gözlemlerini kullanır. İkinci yıl kesim olup olmadığına ilişkin geriye dönük sınıflandırma yapar. Girdi etiketi gerektirmez. Ham veri hazırlamada yalnız `sample_id`, `timestamps`, `clear`, `SCL` ve bant sütunları seçildiğinden kaynak etiketleri özelliklere taşınmaz.

Boş örnek kümeleri, tekrarlı kimlikler, yanlış kanal sayısı/sırası, uyumsuz birim beyanı, geçersiz aylık gün ofsetleri, gözlenmiş hücrelerde sonlu olmayan değerler ve tamamen gözlemsiz örnekler reddedilir. Kaynak `clear` ve SCL 4/5 filtresi aylık medyandan önce uygulanır. Her yılda en az altı gözlem ayı koşulu çıktıdaki `quality_eligible` bayrağını belirler. Bayrak, yeni coğrafyada model doğruluğunu kanıtlamaz.

`advanced_v3` çıktısındaki skorlar geliştirme verisinde kalibre edilmiştir. Bu kalibrasyon yeni bölge için güven garantisi değildir; `member_std` üyeler arası görüş ayrılığıdır, istatistiksel güven aralığı değildir. Eski MVP modelinin kalibre edilmemiş skor açıklaması advanced modelin kalibrasyonuyla karıştırılmamalıdır.

Nihai 10 üyeli paket hash doğrulaması yaparak yerel ağırlıkları yükler. Kaynak birimi beyanının doğru olması, kullanıcının farklı Sentinel işleme geçmişini fiziksel olarak uyumlu hale getirmez. Ürün rastgele tek görüntü veya SAR verisi için doğrulanmış değildir.

## Teslimde düzeltilmesi gereken sunum ayrımı

Denetlenen compact bilimsel ZIP, bütün `scripts/` klasörünü ve tam proje README'sini içeriyor; ancak ham Parquet verilerini ve `advanced_v3` ağırlıklarını içermiyor. Bu nedenle genel README'deki her komutun compact ZIP içinde çalışması beklenmemeli. **Bilimsel arşivde geçerli başlangıç noktası `paper/SUPPLEMENT.md`; ham veri ve bütün modeller için tam proje arşivi; yalnız çıkarım için model arşividir.** Son paketlemede bu kapsamın pakete özgü bir giriş notuyla açıklanması önerildi.

Fiziksel olarak eksik/broken bir `paper_v4.html` teslim bağlantısı bulunmadı. Eksik olan, genel README komutlarının bütün arşivlerde geçerli olmadığına dair ilk açılış yönlendirmesiydi. Nihai ürün, yeni raporlar ve yeni paket notları bu denetim sonrasında eklenirse ilgili bağlantılar tekrar kontrol edilmelidir.

## Yeniden eğitim kararı ve sınırlar

**Mevcut teslim için tam yeniden eğitim gerekmiyor.** Donmuş kaynak/veri/protokol imzaları eşleşiyor; bir gerçek SSL eğitimi aynı olasılıkları yeniden üretti; dağıtılan model ham ve hazırlanmış girdide aynı çıktıları verdi. 180 koşuyu tekrar etmek bağımsız saha verisi eksikliğini gidermeyecektir.

Bu denetimde yalnız bir paper koşusu yeniden eğitildi; diğer 179 tamamlanmış koşu tekrar kullanılmasına rağmen 180 koşunun kayıtları ve ölçütleri yeniden doğrulandı. Eğitim koduna, veriye, protokole ve ağırlıklara değişiklik yapılmadı. Yeni tasarım veya özellik değişikliği ayrı deney sürümü gerektirir.

Arşiv taşınabilirliği bu makinedeki kurulu sabit Python ortamıyla gösterildi; bu denetim sırasında yeni temiz ortam kurulmadı ve Windows/Linux üzerinde çalışma iddiasında bulunulmadı. İleriye dönük dış saha değerlendirmesi, yeni coğrafya doğruluğu veya makale kabulü bu mühendislik kontrollerinden çıkarılamaz. `advanced_v3` 486 noktalık daha önce incelenmiş benchmark'ı, `paper_v4` ise aynı kaynak üzerinde geriye dönük coğrafi araştırma protokolünü kullanır. Bu iki değerlendirme tek başarı skoru gibi sunulmamalıdır.
