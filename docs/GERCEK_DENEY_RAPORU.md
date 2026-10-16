# Orman-SSL: gerçek Sentinel-2 verisinde kesim sınıflandırması

## Tamamlanan araştırma MVP'si

Bu sürüm gerçek etiketli veriyle eğitilmiş modeller, kilitli coğrafi test, etiket verimliliği karşılaştırması, gözlem kaybı deneyi, hata atlası, coğrafi tahmin dosyası ve yeni girdide çalışan tahmin komutu içerir. Tamamlanmış bir saha ürünü veya kabul edilmiş makale iddiası değildir.

## Kısa araştırma özeti

DISFOR'un yüksek güvenli yorum etiketlerinden **2213 gerçek 24 aylık Sentinel-2 serisi** hazırlandı. Girdi 10 spektral DN bandının aylık medyanıdır. Görev, ikinci yılda kesim gerçekleşen orman ile iki yıl boyunca yorumlanmış bozulmasız ormanı ayırmaktır. Yakın noktalar ve aynı olay grupları birleştirilerek eğitim/validation/test coğrafyaları arasında en az 5 km mesafe bırakıldı. Testte 448 bozulmamış ve 38 kesim örneği bulunur; kesim örnekleri 20 bağımsız mekânsal gruba dağılır.

RF, sıfırdan Transformer ve maskeli ön eğitimli Transformer üç seed ve dört eğitim etiketi bütçesinde karşılaştırıldı. Tam eğitim etiketiyle Transformer ortalama macro-F1=0,877 elde etti. %20 etikette RF=0,811; supervised Transformer=0,490; SSL Transformer=0,484. Bu kurulumda az etiketli SSL üstünlüğü gözlenmedi. Sonuç, SSL yaklaşımının genel olarak işe yaramadığı anlamına gelmez; model/ön eğitim seçimi, sınıf dengesizliği ve örnek çeşitliliğiyle sınırlıdır.

## Veri ve örnekleme

Kaynak: [DISFOR, JR-DIGITAL](https://huggingface.co/datasets/JR-DIGITAL/DISFOR), sabit revision `2562332e35c94c2339aeb341ffaed2a99faae7d6`, EUPL-1.2. İndirilen tabloda 3.822 nokta vardır; kaynak kartındaki 3.823 sayısı yerine dosyadan ölçülen sayı kullanıldı. Kaynak zaman serileri ve yorumlanmış segmentler birlikte sağlanır; bu etiketler bizim topladığımız arazi ölçümleri değildir. Kaynağın yayınlanan split'i kullanılmadı; bu proje özel bir coğrafi protokoldür, resmi benchmark sonucu değildir.

Yüksek güvenli örnekler, 2018-2023 hedef yılları, her yıl en az altı açık gözlem ayı. Kesim penceresinde önceki takvim yılı bozulmamış orman olmalı; iki yılda yalnızca bir bozulma olayı bulunmalı. Negatif pencereyi 110 etiketi bütünüyle örtmeli. Bir noktadan tek pencere kullanıldı; pencereler olayın kesin günü etrafında merkezlenmedi. Etiket veya olay günü model girdisi değildir.

İlk üç sınıflı veri hazırlığında testte bir yangın örneği kaldığı görüldü. Skorlar okunmadan ana görev kesim/bozulmamış orman olarak sınırlandı; yangın performansı iddia edilmedi. Seçim kararları `docs/REAL_PROTOCOL.md` ve hazırlama kodunda kayıtlıdır.

## Yöntem

10 bant: B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12. Kaynak DN değerleri korunur; belgelenmemiş ofset uygulanmaz. Bulut temizliği için source clear AND SCL 4/5 kullanılır. Eksik aylar NaN ve gözlem maskesiyle saklanır. Standardizasyon yalnızca eğitim gözlemlerinden hesaplanır. Grup kuralı 5 km komşuluk bağlı bileşenleri ve aynı kaynak hasar poligonu/fırtınasıdır; örnekleme strata'sı olay kabul edilmez.

Transformer: bir encoder, 32 gizli boyut, dört attention head, dropout=0,1. Değer, maske ve göreli takvim bilgisi girişe verilir. SSL: gözlenen hücrelerin %30'unun rekonstrüksiyonu; yalnızca eğitim coğrafyası, 30 epoch. Fine-tune: 25 epoch; validation macro-F1 checkpoint seçimi. RF: 200 ağaç, min_samples_leaf=2, balanced ağırlık ve zaman özetleri. Fine-tune çapraz entropisi bu sabit ana deneyde sınıf ağırlıksızdır; bu, az etiket sonuçları yorumlanırken dikkate alınır.

Her bütçede yöntemler aynı eğitim etiketlerini kullanır. Eğitim oranları validation maliyetini içermez. Kümeler: 1.266 eğitim, 461 validation, 486 test. Tek coğrafi ayrım üzerinde seed 7/17/27 kullanıldı. Test verisi ön eğitim, standardizasyon veya checkpoint seçimine girmedi. SSL ek hesaplama kullanır; eşit toplam hesaplama karşılaştırması yapılmadı.

## Ölçülmüş sonuçlar

| Eğitim etiketi | Random Forest | Transformer | SSL Transformer |
|---|---:|---:|---:|
| %5 | 0.692 ± 0.031 | 0.503 ± 0.037 | 0.478 ± 0.003 |
| %10 | 0.738 ± 0.068 | 0.482 ± 0.008 | 0.479 ± 0.001 |
| %20 | 0.811 ± 0.020 | 0.490 ± 0.010 | 0.484 ± 0.011 |
| %100 | 0.846 ± 0.006 | 0.877 ± 0.019 | 0.819 ± 0.051 |

Değerler test macro-F1 ortalama ± seed standart sapmasıdır. Seed standart sapması güven aralığı değildir. %20 etikette SSL-supervised farkı -0.0057; 1.000 eşleştirilmiş test grubu bootstrap tekrarında %95 aralık [-0.0245, 0.0030]. Aralık sıfırı kapsar. Bu aralık tek veri hazırlama ve coğrafi ayrım koşuluna bağlıdır.

## Kullanıma ayrılan model

Yöntem, %100 eğitim etiketi koşulundaki ortalama validation macro-F1 ile seçildi; seed=7 önceden sabitlendi. Seçilen yöntem Transformer; model `models/model.pt`. Bu tek checkpoint'in test macro-F1 değeri **0.861**. Bu sayı, üç seed ortalaması 0,877 ile karıştırılmamalı.

Confusion matrix, satırlar gerçek / sütunlar tahmin; sıra bozulmamış-kesim:

```
442    6
 12   26
```

Kesim precision=26/32=0,8125; recall=26/38≈0,6842. Kaçırılan 12 kesim, sistemin sınırını gösterir. Olasılıklar kalibre edilmiş güven değildir. Yeni girdi aynı bant sırası, DN tanımı ve 24 aylık takvim sözleşmesini izlemeli. Uygun olmayan kaliteyi model çıktısındaki `quality_eligible` alanı işaretler.

## Eksik gözlem ve hata analizi

%20 etiket modelleri yeniden ayarlanmadan test aylarına %0/%20/%40/%60 ek kayıp uygulandı. Yöntemler aynı seed'e ait aynı maskeleri görür. Sonuçlar `figures/real_robustness.png` ve `reports/real_analysis.json` içinde. Bu kontrollü silme gerçek bulut oluşumunun mevsimsel dağılımını bütünüyle modellemez.

Hata atlası DN eğrilerini yanlış ve doğru örneklerle gösterir. `reports/real_experiment/test_predictions.geojson` yalnızca test noktalarının gerçek koordinat, etiket, tahmin ve skorlarını içerir. Bu noktalar arasında sürekli raster tahmin yapılmış değildir.

## Sonuç ve savunulabilir katkı

Tamamlanan çıktı, gerçek Sentinel-2 verisine dayalı tekrarlanabilir bir karşılaştırma ve çalışan çıkarım aracıdır. Basit RF'nin az etikette güçlü olduğu; uygulanan SSL ön eğitiminin mevcut protokolde üstünlük sağlamadığı görülmüştür. Bu olumsuz bulgu saklanmaz. Nokta örneklemesi, kampanya/coğrafya farkları, negatiflerin fazlalığı, yalnızca bir coğrafi ayrım ve kaynak DN işleme geçmişi genelleme sınırlarıdır.

Gerçek Sentinel-1 füzyonu, Türkiye'de bağımsız saha doğrulaması, yangın/hastalık türlerinin güvenilir değerlendirmesi ve yayın yeniliğinin kanıtı bu tamamlanmış S2 kesim MVP'sinin kapsamı dışındadır. Bunlar eldeki sonuçların var olmadığı anlamına gelmez; hangi problemi gerçekten çözdüğünü tanımlar.

## Tekrar çalıştırma

```bash
.venv/bin/python scripts/prepare_disfor.py
PYTHONPATH=src .venv/bin/python -m orman_ssl.experiment --data data/processed/real_series.npz --out reports/real_experiment
.venv/bin/python scripts/analyze_real.py
PYTHONPATH=src .venv/bin/python -m orman_ssl.predict --checkpoint models/model.pt --data data/processed/test_inference.npz --out reports/inference_cli.json
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_real_report.py
```

Ham veriyi yeniden indirme: `scripts/download_disfor.py`. Veri lisansı `data/disfor/LICENSE`, hash kayıtları `data/disfor/downloads.json`. Kaynak kod, ham/işlenmiş veri, modeller ve raporlar pakette mevcuttur.
