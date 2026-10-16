# Nida Hocayla görüşme: yedi dakika ve sekiz zor soru

Bu not, tamamlanmış yerel araştırma ve ürünün anlatımını kolaylaştırır. Sayılar `paper_v4` bilimsel deneyi ve `advanced_v3` ürün değerlendirmesi olarak ayrı tutulmuştur. Amaç hocaya mevcut sonucu göstermek ve bir sonraki bilimsel kararı birlikte vermektir.

## Görüşmeden önce

Ürünü `URUNU_AC.command` ile aç; örnek çıktısının göründüğünü kontrol et. Türkçe raporu ve İngilizce makaleyi hazır tut. Üründe bir doğru kesim ve bir kaçırılan kesim örneğini önceden seç. Hazır çıktıyı göstermek ile “Örnek veride analizi çalıştır” üzerinden gerçek çıkarım yapmak arasındaki farkı söyle. Gerekirse komut satırında `scripts/run_advanced.py` ile aynı çıkarım akışını göster.

## Yedi dakikalık akış

| Süre | Gösterilecek şey | Söylenecek ana cümle |
|---|---|---|
| 0:00–0:35 | Ürün ekranı ve rapor | “Gerçek Sentinel-2 zaman serisinden iki yıllık pencere içinde kesim sınıflandıran bir sistem hazırladım. Veri hattı, eğitilmiş model, karşılaştırmalı deneyler ve makale aynı projede çalışıyor.” |
| 0:35–1:25 | 24 aylık bir gözlem serisi | “Girdi tek görüntü değil: 24 ay ve 10 bant. Bulutlu gözlemler eleniyor, eksik aylar maskeleniyor. Tahmin için etiket gerekmiyor; görev ikinci yıldaki kesimi geriye dönük sınıflandırmak.” |
| 1:25–2:20 | Veri ve kat özeti | “2.213 konumun 276’sı kesim. Yakın noktaları ve aynı kaynak olayını gruplayarak 874 mekânsal bileşen oluşturdum. Beş kat ve üç seed kullanıldı; toplam 180 eğitim kaydı var.” |
| 2:20–3:40 | Ana sonuç ve kontrol şekilleri | “Yüzde 20 etikette SSL 0,8690; kısa Transformer 0,8322 macro-F1. Ancak daha uzun, yaklaşık adım eşlenmiş denetimli Transformer 0,8987’ye çıkıyor. Ana bulgu, karşılaştırıcının eğitim bütçesinin SSL yorumunu değiştirmesi.” |
| 3:40–4:40 | Üründe gerçek çıkarım ve hata örneği | “Ürün ayrı bir sürüm olan 10 üyeli advanced_v3’ü kullanıyor. Mevcut 486 örnekte 38 kesimin 28’ini buluyor, 10’unu kaçırıyor. Şimdi aynı ham gözlemlerden tahmini tekrar üretiyorum; bu işlem yeniden eğitim değil.” |
| 4:40–5:45 | Kanıt dosyaları ve hata incelemesi | “180 koşunun ölçütleri kayıtlardan yeniden hesaplandı. Paket içinden bir SSL koşulunu yeniden eğittiğimde aynı ortamda olasılıklar birebir eşleşti. 81 hata adayı ayrıca listelendi; model yanlış dedi diye kaynak etiketleri değiştirilmedi.” |
| 5:45–7:00 | Sonraki deney önerisi | “Bu, aynı kaynak üzerinde geriye dönük araştırma; bağımsız Türkiye saha başarımı iddiam yok. Şimdi yayın sorusunu ve geliştirmede kullanılmamış, yeterli kesim olayı içeren değerlendirme verisini birlikte seçmek istiyorum.” |

**Kapanışta alınacak karar:** Çalışmanın eğitim bütçesine duyarlı SSL karşılaştırması olarak mı ilerleyeceği, bağımsız değerlendirme verisinin nereden sağlanacağı ve araştırmacıların fiilî katkılarının nasıl tanımlanacağı. Makale, ürün ve deney kayıtları bu kararı destekleyen somut çıktılardır.

## Sekiz zor soru ve kısa yanıt

### 1. “Burada bilimsel yenilik ne? Transformer ve SSL zaten vardı.”

“Yeni bir mimari icat ettiğimi söylemiyorum. Katkı, orman kesimi görevinde aynı etiket alt kümeleri ve coğrafi katlarla yapılan kontrollü, yeniden üretilebilir karşılaştırma. Kısa denetimli modele karşı SSL yararı görünüyor; eğitim adımı kontrolü eklenince yorum değişiyor. Bunun yayın katkısının yeterliliğini literatür ve bağımsız veriyle birlikte değerlendirmek istiyorum.”

**Kanıt:** `paper/manuscript.md`, `paper/CLAIM_LEDGER.md`, `experiments/paper_v4/analysis.json`.

### 2. “SSL en iyi değilse neden son üründe SSL var?”

“Üründeki advanced_v3, ayrı ve daha önce dondurulmuş bir mühendislik sürümü. O sürümün yalnız eğitim verisindeki coğrafi seçiminde ilk iki tarif SSL Transformer ve CNN olduğu için beşer üyeyle birleştirildi. Son paper deneyi farklı protokolde tekil modelleri inceliyor; yüzde 20 etikette uzun denetimli kontrolün üstün çıkması bu birleşimi doğrudan yeniden değerlendiren bir sonuç değil. Şimdi test skoruna bakıp ürünü değiştirmek yerine yeni bir model değişikliğini ayrı protokolde karşılaştırırım.”

**Kanıt:** `experiments/advanced_v3/selection.json`, `models/advanced_v3/bundle.json`, `experiments/paper_v4/protocol.json`.

### 3. “2.213 örnek yeterli mi?”

“Kontrollü bir araştırma için ölçülebilir veri var; ülke genellemesi için yeterli olduğunu söyleyemem. 2.213 konumun 276’sı kesim ve kesim içeren yalnız 141 mekânsal bileşen var. Aynı olaydaki noktalar bağımsız örnek sayılmıyor. Üç seed ve 180 koşu da yeni saha örneği yaratmıyor. Sonraki veri büyüklüğünü hedeflenen duyarlılık ve yanlış alarm belirsizliğine göre önceden planlamak gerekiyor.”

**Kanıt:** `experiments/paper_v4/analysis.json`, `experiments/paper_v4/support_error_audit.json`.

### 4. “Veri sızıntısı olmadığından emin misin?”

“Doğrudan eğitim/test karışmasını kapsamlı biçimde kontrol ettim: aynı mekânsal bileşen parçalanmıyor, denetlenen 215 olay anahtarı katlar arasında bölünmüyor, ölçekleyici yalnız eğitimde öğreniliyor ve dış test ön eğitime de girmiyor. Etiket veya olay tarihi modele özellik olarak verilmiyor. Fakat veri kümesi önceki geliştirmelerde görüldü; bu geçmiş uyarlama etkisini yeni katlar silemez. Bu yüzden çalışmayı geriye dönük denetim olarak sunuyorum.”

**Kanıt:** `experiments/paper_v4/verification.json`, `experiments/paper_v4/support_error_audit.json`, `paper/SUPPLEMENT.md`.

### 5. “Sıfır yanlış alarm gerçekçi mi?”

“Sıfır yanlış alarm, yalnız ürün modelinin daha önce incelenmiş 448 orman örneğindeki gözlenen sayı. Aynı değerlendirmede 38 kesimin 10’u kaçırıldı. Yeni bölge için sıfır alarm garantisi veya kusursuz model iddiası yok. Üstelik saha sınıf oranı değişirse precision da değişebilir; sayıyı örnek desteği ve kaçırılan kesimlerle birlikte raporluyorum.”

**Kanıt:** `experiments/advanced_v3/evaluation.json`; karışıklık matrisi `[[448, 0], [10, 28]]`.

### 6. “Bu gerçek ürün mü, yoksa yalnız hazırlanmış bir demo mu?”

“Yerel çalışan bir araştırma ürünü. Kayıtlı sonuçları inceleme ekranı var; ayrıca gerçek eğitilmiş ağırlıkları yükleyip ham gözlemlerden aylık girdi, sınıf skorları, JSON ve GeoJSON üreten çalışır hat var. Etiketsiz uyumlu yeni veri komut satırından işlenebilir. Sürekli uydu verisi toplayan, ülke haritası üreten veya anlık uyarı veren işletim hizmeti henüz değil.”

**Kanıt:** `scripts/run_advanced.py`, `docs/VERI_SOZLESMESI.md`, `docs/NIHAI_TEKNIK_DENETIM.md`. Arayüzün son test kapsamı `reports/final_delivery_verification.json` içindedir.

### 7. “Bunu Türkiye’de hemen kullanabilir miyiz?”

“Uyumlu veriyle tahmin çalıştırabiliriz; doğruluğunu varsayamayız. Bantlar, kaynak DN işleme geçmişi, iki yıllık takvim, gözlem desteği ve görev tanımı eşleşmeli. Türkiye’nin orman yapısı ve kesim örüntüleri farklı olabilir. Önce model skorlarından bağımsız seçilmiş ve etiketlenmiş bir Türkiye değerlendirme kümesinde mevcut modeli ve eşiği dondurarak ölçmek isterim.”

**Kanıt:** `docs/VERI_SOZLESMESI.md`, `models/advanced_v3/model_card.json`.

### 8. “İlk sıradaki sonraki deney ne olmalı?”

“Geliştirmede kullanılmamış, yeterli bağımsız kesim olayı içeren bir bölge/dönem değerlendirmesi. Araştırma sorusu eğitim bütçesiyse kısa Transformer, SSL, adım eşlenmiş Transformer ve CNN karşılaştırmasını yeni protokolle önceden belirlerim; ürünün taşınabilirliği için advanced_v3’ü ayrıca dondurulmuş ürün olarak ölçerim. Model skorları görülmeden bölge, etiketleme, örneklem ve ölçütler tanımlanmalı. Mevcut kullanılmamış DISFOR taramasındaki 111 adayın yalnız biri kesim olduğu için o havuzdan dış doğrulama skoru üretmedim.”

**Kanıt:** `experiments/paper_v4/unused_probe_audit.json`, `docs/ARASTIRMA_VE_URUN_RAPORU.md`.

## Sayıları karıştırmamak için küçük kart

| İfade | Doğru bağlam |
|---|---|
| 0,8690 ve 0,8322 | paper_v4, yüzde 20 etiket, SSL ve 40 epoch Transformer; üç seed ortalama macro-F1. |
| 0,8987 | paper_v4, yüzde 20 etiket, 320 epoch adım eşlenmiş denetimli Transformer. |
| 0,9299 | paper_v4, yüzde 100 etiket, CNN; ayrı katlardan birleştirilen tahminlerde üç seed ortalaması. |
| 0,9187 | advanced_v3 ürün birleşimi; daha önce incelenmiş 486 nokta. |
| 28 / 38 | advanced_v3 ürününün bulduğu kesim sayısı; 10 kesim kaçırıldı. |
| 180 | paper_v4 tamamlanmış koşu sayısı; 180 farklı veri kümesi veya 180 bağımsız doğrulama değil. |
| 0,0 tekrar üretim farkı | Aynı ortamda tek bir yeniden eğitilen SSL koşulunun olasılık farkı; bütün platformlarda birebir sonuç garantisi değil. |

**Katkı beyanı:** Kodlama, analiz denetimi ve rapor hazırlamada yapay zekâ yardımı kullanıldı. Araştırmacı, anlatacağı yöntem ve sonuçları kendisi incelemeli; yazarlık, kurum, fon ve bilimsel sorumluluk gerçek katkılara göre belirlenmelidir.
