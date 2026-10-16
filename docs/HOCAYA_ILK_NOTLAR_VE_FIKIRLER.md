# İlk notlar ve fikirler — Nida Hoca ile 18 Ekim 2026 görüşmesi için

Mehmet Oğuz Güneren · Hazırlık tarihi 16 Ekim 2026

Bu belge, 13 Eylül e-postasındaki araştırma başlıklarına verdiğim karşılıkları, okuduğum makalelerden çıkardığım notları, denediğim pilot çalışmayı ve sizinle birlikte karar vermek istediğim soruları tek yerde toplar. Amacım "bitmiş bir iş" sunmak değil; neyi anladığımı, neyi denediğimi ve nerede yönlendirmeye ihtiyacım olduğunu açıkça göstermek.

**Dürüstlük notu:** Bu süreçte kodlama, deney düzeni, analiz kontrolü ve belge hazırlamada yapay zekâ kodlama araçlarını (OpenAI Codex ve Claude) yoğun kullandım. Veri seçimi, araştırma sorusu, hangi kontrollerin gerekli olduğu ve sonuçların yorumu benim sorumluluğumda; ama tek başıma bu kadar kısa sürede bu hacmi üretemezdim. Bunu baştan söylemek istiyorum ki neyi gerçekten anladığımı ve neyi henüz öğrenmekte olduğumu birlikte doğru değerlendirebilelim.

## 1. Sizin verdiğiniz başlıklar ve öğrendiklerim

**CBS ve uzaktan algılama.** CBS, konumu olan veriyi saklama, üst üste getirme ve sorgulama sistemi; uzaktan algılama ise sensörden yeryüzü hakkında ölçüm üretme. Projede uydu ölçümü uzaktan algılama verisi, olay poligonu ve bozulma haritasını aynı koordinat sisteminde karşılaştırmak CBS işi.

**Raster ve vektör.** Raster hücre ızgarası (uydu bandı, sınıf kodu haritası); vektör nokta/çizgi/poligon (etiket noktası, olay alanı). İlk pratik dersim CRS oldu: GFD dosyaları EPSG:4326, yani derece cinsinden; piksel sayısını sabit 900 m² ile çarpıp alan çıkarmak yanlış, eş-alan projeksiyon veya jeodezik hesap gerekiyor.

**Optik ve SAR.** Sentinel-2 pasif optik (13 bant, 10/20/60 m, 2015'ten itibaren), bulut ve gölgeden etkileniyor, bitki örtüsü indeksleri (NDVI, NBR) için uygun. Sentinel-1 aktif C-band SAR, bulut ve gece fark etmiyor ama nem, geometri, speckle ve topoğrafya etkileri biyolojik değişimle karışabiliyor. Landsat 30 m'lik uzun arşiviyle 2000'li yıllar için tek seçenek. Sentinel Asia'nın Copernicus Sentinel uyduları olmadığını, JAXA öncülüğünde Asya-Pasifik afet bilgi paylaşım platformu olduğunu öğrendim.

**Veri nereden indirilir.** Sentinel-2'yi Element 84 Earth Search STAC kataloğundan COG içinden küçük pencere okuyarak indirdim (Marmaris çevresi, Temmuz/Ağustos 2021, hesap gerektirmedi). Copernicus Browser ve USGS EarthExplorer'ı da inceledim. Ölçek/ofset kuralları ve SCL (scene classification) bulut maskesi kodlarını Copernicus ve Sentinel Hub belgelerinden okudum.

**QGIS.** GFD kesitlerini, kendi ürettiğim dNBR/NDVI rasterlarını ve DISFOR noktalarını açabilecek bir QGIS projesi ve adım adım rehber hazırladım (`docs/QGIS_REHBERI.md`, `qgis/`). Identify ile hücre kodlarını kontrol etme, stil yükleme, CRS ve NoData bilgisini okuma alıştırmalarını yaptım.

## 2. Paylaştığınız makaleler: problem, veri, yöntem, başarım

**Wang ve ark. 2026, Global high-resolution forest disturbance type dataset (ESSD).** Problem: 2000–2020 için küresel 30 m orman bozulma türü haritası. Veri: Landsat/CCDC zaman serisi, yardımcı değişkenler. Yöntem: CART. Başarım: 57.000 örnek, %99 genel doğruluk, 7:3 eğitim/doğrulama ayrımı. Figshare'dan iki örnek GeoTIFF (GFC22, GFC30) indirip inceledim. Bulduklarım: (a) 0 kodu makalede "undisturbed", Figshare açıklamasında "other disturbance"; (b) NoData tanımı yok; (c) olay tarihi yok, yalnız dönem boyunca baskın tür var; (d) Figshare v1 açıklaması 16.000 doğrulama örneği ve %95 doğruluk diyor, makale 57.000 ve %99. Bu yüzden bu ürünü otomatik etiket kaynağı olarak kullanmanın riskli olduğuna karar verdim; "ürünle uyum" olarak ayrıca kullanılabilir.

**Zhang ve ark. 2025, Self-supervised deep learning for forest disturbance types (IJDE).** Problem: subtropik ormanda kesim/hastalık gibi bozulma türlerini ayırma. Veri: Sentinel-1 + Sentinel-2 düzensiz zaman serileri. Yöntem: Transformer (IRMST), düzensiz zaman için konumsal kodlama, kontrastif tarzda öz-denetimli ön eğitim. Başarım: F1 ≈ 0,95; %20 etikette SSL'li model 0,95'e karşı 0,86. Tam metne yayıncı sayfasından erişemedim (403); özet ve indekslenmiş bölümleri okudum. Beni en çok "%20 etikette SSL kazanıyor" sonucu ilgilendirdi ve pilot deneyimin sorusu buradan çıktı: **bu kazanç daha güçlü bir denetimli karşılaştırıcıya karşı da sürer mi?**

**Maze ve ark. 2025 (Nil Deltası, ISPRS) ve Vyas ve ark. 2024/25 (Punjab, Earth Science Informatics).** İkisi de S1+S2 füzyonuyla tarım arazi örtüsü/değişim sınıflandırması; XGBoost/RF gibi güçlü basit modellerin %91–96 OA verdiğini gösteriyor. Çıkardığım iki ders: radar katkısını ayrı ölçmek gerekir, ve RF gibi basit referansı hiçbir zaman atlamamak gerekir. Pilotumda RF'yi bu yüzden tuttum.

## 3. Pilot çalışma: ne yaptım, ne buldum

Olay tarihi olan, kamuya açık, gerçek etiketli bir Sentinel-2 zaman serisi verisi aradım ve **DISFOR**'u (JR-DIGITAL, Joanneum Research, EUPL-1.2 lisanslı, Avrupa orman bozulma etiketleri) buldum. Sabit bir sürümü indirdim; 3.822 noktadan yüksek güvenli, iki tam takvim yılı penceresi kurulabilen 2.213 konum seçtim (1.937 bozulmamış orman, 276 kesim). Her örnek 24 ay × 10 Sentinel-2 bandı; bulutlu gözlemler SCL ile elenip aylık medyan alındı, eksik aylar maskeyle işaretlendi.

Araştırma sorusu: *Az etiketle (eğitim konumlarının %20'si) maskeleyip yeniden kurma tarzı öz-denetimli ön eğitim, aynı mimarinin sıfırdan eğitilmesine göre kesim sınıflandırmasını iyileştiriyor mu; iyileştiriyorsa aynı optimizasyon bütçesini alan denetimli model karşısında da sürüyor mu?*

Deney düzeni: 5 km yakınlık ve ortak olay bağlarıyla 874 mekânsal bileşen; 5 coğrafi kat; 3 rastgele başlangıç; RF, zamansal CNN, Transformer, SSL Transformer ve kontroller. Toplam 180 eğitim kaydı. Ölçüt macro-F1; belirsizlik mekânsal bileşen bootstrap'ıyla.

| Sonuç (%20 etiket, 3 seed ortalaması) | Macro-F1 |
|---|---:|
| Kısa (40 epoch) denetimli Transformer | 0,832 |
| SSL Transformer (60 ön eğitim + 40 epoch) | 0,869 |
| Zamansal CNN | 0,872 |
| Adım sayısı eşlenmiş uzun denetimli Transformer | 0,899 |

Yani Zhang'ın sonucuna benzer şekilde SSL kısa eğitilen modeli geçiyor; ama aynı sayıda optimizasyon adımı verilen denetimli model SSL'yi geçiyor. **Ana bulgum "SSL iyidir" değil, "karşılaştırıcının eğitim bütçesi sonucu değiştirir."** Tam etikette üç sinir ağı da 0,93 civarında ve birbirinden ayrılmıyor.

Bu hafta iki ek deney tamamladım:

- **Mekânsal yarıçap duyarlılığı (tek seed):** Gruplama yarıçapını 5 → 10 → 20 km yapınca sıralama değişiyor. 20 km'de SSL 0,844 ile en iyi, adım eşlenmiş denetimli 0,822, CNN 0,800. Yani eğitim ve test bölgeleri birbirinden daha uzak tutulunca ön eğitimli model daha az bozuluyor. Tek seed olduğu için bunu "ipucu" olarak sunuyorum, kanıt olarak değil.
- **Etiket bütçesi eğrisi (%5, %10, %50):** Aynı katlar ve seed'lerle etiket eğrisini tamamladım; sayılar `experiments/paper_v6_label_curve/analysis.json` ve makalenin Tablo 5'inde.

Sınırlarını kendim yazayım: tek veri kümesi, geriye dönük bir denetim (modeller aynı veride daha önce geliştirilmişti), Türkiye verisi yok, Sentinel-1 yok, bağımsız saha doğrulaması yok. Kullanılmamış DISFOR noktalarında yalnız 1 kesim kaldığı için dış doğrulama skoru üretmedim.

## 4. Yanında ne var

- Çalışan bir yerel inceleme uygulaması (eğitilmiş model, 486 örnek, ham gözlemden yeniden çıkarım, GeoJSON çıktısı).
- Türkçe sonuç raporu ve İngilizce makale taslağı (26 kaynak, 5 şekil, 6 tablo). Taslak "anonim, yazar kararları alınmamış" olarak hazırlandı; yazarlık, kurum ve hedef dergi kararlarını sizinle vermek istiyorum.
- Bütün deneylerin kayıtları, doğrulama scriptleri, 79 otomatik test ve tekrar üretim paketleri.

## 5. Size sormak istediklerim

1. Bu pilotu hangi yöne götürelim: (a) "etiket verimliliği değerlendirmesinde optimizasyon ve mekânsal kontrol" eksenli kısa bir yöntem makalesi, (b) Sentinel-1 ekleyip Zhang'a daha yakın tam bir makale, (c) Türkiye uygulaması?
2. TÜBİTAK/BİLGEM tarafında kesim ya da yangın için bağımsız etiket ve Türkiye Sentinel verisi tedarik etme imkânı var mı? Kör etiketleme için iş akışını hazırladım (`external_validation/`); iki yorumlayıcı ve bir hakem gerekiyor.
3. Zhang ve ark. makalesinin tam metnine kurum erişiminizle bakabilir miyiz? Ön eğitim hedefi ve veri bölme ayrıntılarını doğrulamam gerekiyor.
4. Hedef yayın türü ve seviyesi ne olmalı; sizin için uygun dergi/konferans hangisi (IEEE GRSL, Remote Sensing, IJDE, ISPRS, yerli bir konferans)?
5. Haftalık planlamayı nasıl kurmak istersiniz; her hafta kısa bir yazılı ilerleme notu + 20 dakikalık görüşme uygun olur mu?

## 6. Önerdiğim sonraki dört hafta

| Hafta | İş | Kararın size düştüğü yer |
|---|---|---|
| 1 | Yarıçap deneyini 3 seed'e çıkarmak; literatürü derinleştirmek; Zhang tam metni | Yayın ekseni (a/b/c) |
| 2 | Sentinel-1 VV/VH serilerini DISFOR konumları için indirip veri sözleşmesine eklemek | S1 işleme ve yörünge seçimi |
| 3 | S1+S2 ve yalnız S2 karşılaştırması, aynı protokolle | Hangi kontroller gerekli |
| 4 | Bağımsız değerlendirme verisi için protokolü dondurmak; makale taslağını birlikte gözden geçirmek | Yazarlık, dergi, veri tedariki |

Bu plan önerim; sizin öncelikleriniz farklıysa tamamen değiştirebiliriz.
