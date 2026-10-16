# Orman-SSL — projenin tam haritası ve dosya rehberi

**Son envanter:** 16 Ekim 2026 (akşam güncellemesi: v5 tamamlandı, v6 eklendi, kaynakça 26)  
**Proje klasörü:** `/Users/gnrnoguz/Desktop/PaperNidaHoca`  
**Bütün dosyaların tek tek konumu:** [TUM_DOSYALAR_ENVANTERI.md](TUM_DOSYALAR_ENVANTERI.md)

Bu belge “Bu proje tam olarak ne yapıyor, neden yapıldı, nasıl çalışıyor, hangi dosyası ne işe yarıyor?” sorularını yanıtlar. Buradaki yollar **proje klasörüne göre** yazılmıştır. Örneğin `models/advanced_v3/bundle.json` dosyasının tam konumu `/Users/gnrnoguz/Desktop/PaperNidaHoca/models/advanced_v3/bundle.json` olur. Her dosyayı tek tek, tıklanabilir tam yolu ve boyutuyla görmek için yukarıdaki envanteri aç.

## Önce hangi dosyayı açmalısın?

| Ne yapmak istiyorsun? | Açılacak dosya veya klasör | Ne göreceksin? |
|---|---|---|
| Projeyi sıfırdan öğrenmek | [15 sayfalık Türkçe rehber](../output/egitim/Orman_SSL_15_Sayfada_Proje_Rehberi.pdf) | Kavramlar, yöntem, sonuçlar, demo, sınav ve hocaya anlatım |
| Son bilimsel ve ürün sonucunu okumak | [Türkçe sonuç raporu PDF](../output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf) | Araştırma bulguları, çalışan ürün ve sınırlar |
| Raporu düzenlemek | [Türkçe sonuç raporu Word](../output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.docx) | Düzenlenebilir rapor |
| Makaleyi okumak | [İngilizce makale PDF](../output/pdf/Orman_SSL_Manuscript.pdf) | Bilimsel makale taslağı |
| Makaleyi düzenlemek | [İngilizce makale Word](../output/paper/Orman_SSL_Manuscript.docx) | Düzenlenebilir makale |
| Canlı ürünü göstermek | [URUNU_AC.command](../URUNU_AC.command) | Yerel tarayıcı arayüzü ve kayıtlı modelin gerçek çıkarımı |
| Araştırma sonuçlarını çevrimdışı göstermek | [paper_v4.html](../reports/paper_v4.html) | 180 koşuluk ana araştırmanın etkileşimli özeti |
| 18 Ekim görüşmesine hazırlanmak | [HOCAYA_ILK_NOTLAR_VE_FIKIRLER.md](HOCAYA_ILK_NOTLAR_VE_FIKIRLER.md) ve [PAZAR_TOPLANTI_AKISI.md](PAZAR_TOPLANTI_AKISI.md) | Hocanın ödev başlıklarına karşılıklar, pilot bulgular, sorular, 10 dakikalık akış |
| Hocayla konuşma sırasını görmek (eski uzun sürüm) | [GORUSME_AKISI_VE_SORULAR.md](GORUSME_AKISI_VE_SORULAR.md) | Yedi dakikalık akış ve zor sorular |
| Her dosyanın tam konumunu bulmak | [TUM_DOSYALAR_ENVANTERI.md](TUM_DOSYALAR_ENVANTERI.md) | Kalıcı proje dosyalarının eksiksiz listesi |

**Önemli sürüm ayrımı:** Güncel bilimsel ana sonuç `paper_v4`, ürünün çalıştırdığı eğitilmiş model `advanced_v3`, ürün arayüzü `1.1` sürümüdür. `paper_v5_exploratory` ve `presto_v1_exploratory` daha sonraki **keşif çalışmalarıdır**; ana makalenin sabit `paper_v4` sonucunun yerine geçmez. İlk MVP ve sentetik deneme dosyaları da klasörde tarihçe için durur.

## 1. Proje nedir ve niçin yapıldı?

Orman-SSL, **gerçek Sentinel-2 uydu gözlemlerinden orman kesimini geriye dönük sınıflandırma** projesidir. Her örnekte aynı konumun iki tam takvim yılı boyunca aylık ölçümleri bulunur. Amaç, **ikinci yılda kesim olup olmadığını** ayırt etmektir. Çıktı iki sınıftan biridir: `undisturbed_forest` (bozulmamış orman) veya `clear_cut` (kesim). Model ayrıca kesim skoru üretir.

Bu problemde güvenilir etiket toplamak zahmetlidir. Bu yüzden bilimsel soru şudur: **Az sayıda etiket varken, etiketsiz gözlemleri maskeleyip yeniden kurarak yapılan özdenetimli ön eğitim (SSL) yarar sağlıyor mu; sağlıyorsa bu yarar daha uzun eğitilmiş güçlü bir denetimli karşılaştırıcı karşısında sürüyor mu?** Proje bu soruyu aynı konumlar, aynı etiket alt kümeleri ve coğrafi ayrımlar üzerinde karşılaştırır. İkinci amaç, eğitilmiş modeli incelenebilir bir yerel ürüne dönüştürmektir.

Buradaki model bir yangın alarmı veya bütün Türkiye'nin kesintisiz orman haritası değildir. İki yıllık pencere tamamlandıktan sonra sınıflandırma yapar. Kaynak etiketler DISFOR veri üreticilerinin yorumlarından gelir; bu proje için yeni saha ziyareti yapılmadı. Türkiye'de bağımsız saha başarımı henüz ölçülmedi.

## 2. Veri nereden geliyor ve neye dönüşüyor?

Ana kaynak, sabit DISFOR sürümüdür. Kaynak kümede 3.822 konum vardır. Güven, iki yıllık pencere, açık ay sayısı ve ikili göreve uygunluk seçiminden sonra **2.213 konum** kalır: **1.937 orman, 276 kesim**. Veri lisansı ve kaynak kayıtları `data/disfor/LICENSE`, `data/disfor/repository.json`, `data/disfor/downloads.json` ve `data/disfor/sample_manifest.json` içindedir. Asıl tablolar `data/disfor/samples.parquet`, `pixel_data.parquet`, `labels.parquet` dosyalarıdır.

Bir model girdisi **24 ay × 10 Sentinel-2 bandı** biçimindedir. `scripts/prepare_disfor.py` kaynak gözlemleri örneğe bağlar; kaynak `clear` koşulu **ve** SCL 4/5 kalite koşulundan geçen ölçümlerin aylık medyanını hesaplar. Eksik ay sıfırla doldurulmuş gerçek ölçüm gibi kullanılmaz; `observed` maskesiyle belirtilir. Her yılda en az altı gözlenen ay koşulu uygulanır. Kaynak DN ölçeği korunur. Ölçekleme yalnız eğitim verisinden öğrenilir. Referans etiket ve olay tarihi model girdisine sokulmaz.

| Veri konumu | Görevi |
|---|---|
| `data/disfor/` | Sabit kaynak tabloları, lisans, sınıf ve köken kayıtları |
| `data/processed/real_series.npz` | Bilimsel deneyin hazırlanmış zaman serileri |
| `data/processed/test_inference.npz` | Etiketsiz çıkarım örnek girdisi |
| `data/examples/inference_windows.json` | Yeni girdinin kimlik ve iki yıllık pencere örneği |
| `data/metadata/` ve `data/raw/` | Kaynak/uydu ön inceleme kayıtları ve eski raster incelemeleri |
| `docs/VERI_SOZLESMESI.md` | Kendi verinin biçim, bant sırası, birim ve kalite kuralları |

Eğitim ve testte yakın noktaların veya aynı olayın iki tarafa da düşmesi yanlış iyimser başarı verebilir. Bu nedenle `paper_v4`, 5 km yakınlık ve bilinen ortak olay bağlarıyla **874 mekânsal bileşen** kurup bunları beş coğrafi kata ayırır. Denetlenen eğitim–test en yakın uzaklığı yaklaşık **5,0011 km**'dir. Bu kural bütün olası bağımlılıkları yok ettiğini kanıtlamaz; belirlenen yakınlık ve olay sızıntısı riskini sınırlar.

## 3. Bilimsel deney (`paper_v4`) nasıl yapıldı?

**Bilimsel deneydeki ölçüm**, ürün ekranındaki 486 örneklik geçmiş ölçümden ayrıdır. `paper_v4` 2.213 konumda, beş coğrafi kat ve üç rastgele başlangıç (`seed`: 7, 17, 27) kullanır. Yüzde 20 ve yüzde 100 etiket bütçelerinde Random Forest, zamansal CNN, kısa denetimli Transformer ve SSL Transformer karşılaştırılır. Ek kontroller arasında adım bütçesi eşlenmiş uzun denetimli Transformer, bağımsız hücre maskelemesi ve yalnız yan bilgi kontrolleri vardır. Toplam **180 gerçek eğitim koşusu** kaydedilmiştir.

SSL'de model önce mevcut gözlemlerin bir bölümünü **bilinçli olarak gizleyip** onları tahmin etmeyi öğrenir. Doğal olarak ölçülmemiş hücreler bu eğitim hedefi yapılmaz. Ardından etiketli örneklerle kesim/orman sınıflandırması için eğitilir. Bu, etiketsiz veriden öğrenilen temsilin az etiketli görevde işe yarayıp yaramadığını sınar. Denetimli karşılaştırıcı ise sınıf etiketleriyle doğrudan öğrenir.

Her yöntem aynı dış katın test noktalarını eğitimden uzak tutar; aynı kat/seed/etiket bütçesinde etiketli konumlar birebir eşleşir. Dış kat tahminleri birleştirilir; her seed için 2.213 noktanın **macro-F1** ve diğer ölçütleri hesaplanır. Macro-F1 iki sınıfın F1'ini eşit ağırlıkla ortalar; “tüm örneklerin yüzde kaçı doğru” anlamındaki accuracy ile aynı şey değildir. Kesim azınlık sınıfı olduğundan yalnız accuracy yanıltıcı olabilir. AP ise skor sıralamasını özetler. Belirsizlik aralıkları mekânsal bileşenlerden 2.000 eşlenmiş bootstrap çekilişiyle hesaplanır; yeni bir ülkedeki başarım aralığı değildir.

| Yüzde 20 etiketli ana karşılaştırma | Macro-F1 ortalaması |
|---|---:|
| Kısa denetimli Transformer | 0,8322 |
| SSL Transformer | 0,8690 |
| Zamansal CNN | 0,8721 |
| Yaklaşık aynı optimizer adımını alan uzun denetimli Transformer | 0,8987 |

**Doğru bilimsel sonuç:** SSL, kısa denetimli Transformer'dan daha iyi görünür; fakat uzun denetimli kontrol macro-F1'de SSL'yi geçer. Bu yüzden “SSL her durumda daha iyi” veya “yeni mimari bulduk” denmez. Uzun kontrol optimizer adımlarını yaklaşık eşler; süreyi, FLOP'u ve aynı etiketleri kaç kez gördüğünü eşitlemez. Yapılandırılmış maskelemenin bağımsız hücre maskelemesine kesin üstünlüğü de gösterilmemiştir. Tam etiketli CNN ortalaması **0,9299**'dur; bu, başka ülkeye aktarım sonucu değildir.

**Kanıt zinciri:** `experiments/paper_v4/protocol.json` (önceden sabitlenen kural) → `folds.json` ve `jobs.json` (hangi ayrım/koşu) → `runs/` altındaki 180 JSON kayıt (eğitim ve tahmin) → `oof_predictions.npz` (dış katta üretilmiş tahminler) → `analysis.json` (tablolar/aralıklar) → `paper/manuscript.md` ve `reports/paper_v4.html` (anlatım). `experiments/paper_v4/verification.json`, `reports/final_science_review.json`, `paper/CLAIM_LEDGER.md` ve `paper/SUPPLEMENT.md` iddia, yeniden hesap ve tekrar üretim için açılır. `scripts/train_paper.py`, `scripts/analyze_paper.py`, `scripts/verify_paper.py` işlem kodudur. Tekrarlanmış tahminleri sayan 79.668 değer **79.668 bağımsız konum** demek değildir.

## 4. Çalışan ürün modeli (`advanced_v3`) nedir?

Ürünün kaydedilmiş modeli **beş SSL Transformer ve beş CNN** üyesinin birleşimidir. Toplam on gerçek ağırlık dosyası `models/advanced_v3/` içindedir; `bundle.json` bunların dosya kimliklerini, SHA-256 bütünlüklerini, kalibrasyon ve karar eşiğini tanımlar; `model_card.json` görevi ve sınırları açıklar. Eğitimin seçim ve değerlendirme kayıtları `experiments/advanced_v3/` altındadır. Model uygulaması `src/orman_ssl/advanced.py`, yeni veriye tahmin `src/orman_ssl/predict_advanced.py`, komut satırı girişi `scripts/run_advanced.py` içindedir.

Bu sürümde eğitim 1.266 noktada, kalibrasyon 461 noktada, geçmiş benchmark 486 noktada tutuldu. **Daha önce incelenmiş 486 örnekte** macro-F1 **0,9187**; 38 referans kesimin **28'i bulundu, 10'u kaçırıldı**. 448 referans orman örneğinde yanlış kesim alarmı sıfırdı. Bu sayılar `models/advanced_v3/model_card.json` ve `experiments/advanced_v3/evaluation.json` dosyalarında kayıtlıdır. Bu 486 örnek yeni, bağımsız dış saha verisi değildir. Ürün skoru ile `paper_v4`'ün coğrafi çapraz doğrulama ortalamaları tek bir yarış tablosu yapılmaz; eğitim ve değerlendirme düzenleri ayrıdır.

Modelin verdiği kalibre kesim skoru geliştirme verisindeki kalibrasyona dayanır. Yeni coğrafyada “%99 kesinlik” sözü değildir. Üyeler arası standart sapma da istatistiksel güven aralığı değildir. `quality_eligible` aylık gözlem koşulunu anlatır, tahminin doğru olduğunu değil.

### Eğitilmiş ağırlıkların tam konumları

`models/advanced_v3/` altında CNN ağırlıkları: `cnn64_7.pt`, `cnn64_17.pt`, `cnn64_27.pt`, `cnn64_37.pt`, `cnn64_47.pt`. SSL Transformer ağırlıkları: `ssl_transformer48_7.pt`, `ssl_transformer48_17.pt`, `ssl_transformer48_27.pt`, `ssl_transformer48_37.pt`, `ssl_transformer48_47.pt`. Her birinin tıklanabilir tam yolu [tam envanterde](TUM_DOSYALAR_ENVANTERI.md) bulunur. `models/model.pt` önceki MVP'nin modelidir; güncel ürün onu yüklemez.

## 5. Ürün nerede ve ne yapar?

Mac'te proje kökündeki `URUNU_AC.command` dosyasına çift tıklayın. Terminal ve yerel tarayıcı açılır; adres varsayılan `http://127.0.0.1:8765` olur. Terminal açık kalmalıdır. Arayüz kodu `reports/product.html`, yerel sunucu `scripts/serve_product.py`, kullanım açıklaması `docs/URUN_KILAVUZU.md` içindedir. Tarayıcıda 486 kayıtlı örneğin konumunu, 24 aylık spektral izini, tahminini, gözlem kalitesini, doğru ve kaçırılmış kesim örneklerini görebilirsiniz.

**“Örnek veride analizi çalıştır”** düğmesi ham DISFOR Parquet verisini yeniden okuyup aynı on kayıtlı modelle gerçek çıkarım yapar; eğitim başlatmaz. Çıktı `output/product_demo/` klasöründe `input.npz`, `predictions.json`, `predictions.geojson`, `manifest.json`, `inference.log` olur. Başlangıçta gösterilen dondurulmuş sonuç `output/advanced_prediction/` içindedir. Kendi sözleşmeye uygun etiketsiz NPZ girdin için arayüzde yükleme vardır; başarılı yüklemeler `output/product_uploads/run-…/` altında ayrı tutulur. `scripts/run_advanced.py` kendi ham gözlem Parquet'in ve iki yıllık pencere JSON'unla komut satırından çalışır. Yalnız model arşiviyle hazır NPZ üzerinde çıkarım için `output/Orman_SSL_Nihai_Model.zip` vardır.

Yeni veri için sayıların biçimce uygun olması fiziksel olarak aynı sensör işleme geçmişinden geldiğini tek başına kanıtlamaz. Birim, bant sırası, aylık kalite filtresi ve kaynak DN işleme geçmişini `docs/VERI_SOZLESMESI.md` ile kontrol edin. Ürün rastgele tek Sentinel görüntüsünde veya SAR/Sentinel-1 girdisinde doğrulanmış değildir.

## 6. Raporlar, makale, eğitim metinleri ve bütün MD dosyaları

**Ana Türkçe sonuç raporu:** `output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf` ve aynı adlı `.docx`. Metin kaynağı `docs/ARASTIRMA_VE_URUN_RAPORU.md`; üretim kodu `scripts/build_final_report.py`. Makinece belge kontrolü `reports/final_report_document_qa.json` ve `reports/final_delivery_verification.json` içindedir.

**İngilizce makale:** `output/pdf/Orman_SSL_Manuscript.pdf`, `output/paper/Orman_SSL_Manuscript.docx`. Metin `paper/manuscript.md`, yapılandırılmış içerik `paper/manuscript_content.json`, şekiller `paper/figures/`, kaynakça `paper/references.json` ve `paper/references.bib`. `paper/SUPPLEMENT.md` yöntem ayrıntıları ve tekrar üretim; `CLAIM_LEDGER.md` sayıların dayanağı; `ERROR_AUDIT.md` hata örnekleri; `LITERATURE_POSITION.md` literatürde yeri; `HOCAYA_NOT.md` sunum notu; `AUTHOR_CONFIRMATION.md` insan araştırmacıların netleştirmesi gereken yazar/kurum/katkı kararlarıdır. Belge üretim kodları `scripts/compose_paper.py`, `scripts/build_paper_docx.py`, `scripts/build_pdf.py`, `scripts/plot_paper.py` içindedir.

**Okuma ve hocaya hazırlık:** Güncel kısa rehber `output/egitim/Orman_SSL_15_Sayfada_Proje_Rehberi.pdf`, `.docx`, `.md`; 40 sayfalık geniş sürüm aynı klasörde `Orman_SSL_Sifirdan_Proje_Hakimiyet_Rehberi.*`. Kısa rehberin düzenlenebilir bölüm kaynakları `docs/egitim/kisa/01_temeller.json` … `05_basvuru.json`, oluşturucusu `scripts/build_compact_learning_guide.py`, kapsam ve görsel kontrolleri `reports/compact_learning_guide_coverage.json` ile `reports/compact_learning_guide_document_qa.json` içindedir. **15 sayfa; 38 ders, 259 içerik bloğu, 52 dosya dayanağı** korunmuştur. Uzun rehberin kaynakları `docs/egitim/` kökünde, üretim kodu `scripts/build_learning_guide.py` içindedir.

**Diğer güncel MD belgeleri:** `README.md` başlangıç; `docs/URUN_KILAVUZU.md` ürün kullanımı; `docs/VERI_SOZLESMESI.md` girdi biçimi; `docs/GORUSME_AKISI_VE_SORULAR.md` sözlü anlatım; `docs/NIHAI_BILIMSEL_DENETIM.md` bilimsel denetim; `docs/NIHAI_TEKNIK_DENETIM.md` mühendislik denetimi; `docs/TESLIM_KONTROLU.md` teslim kontrolü; `docs/ARASTIRMA_PLANI.md` araştırma planı; `docs/DENEY_GUNLUGU.md` kayıtlar; `docs/KAYNAK_NOTLARI.md` literatür notları; `docs/MODEL_CARD.md` model sınırları. `external_validation/README_TR.md` ileride gerçek bağımsız veri için hazır fakat henüz uygulanmamış iş akışıdır.

**Tarihsel/yardımcı MD belgeleri:** `docs/README_ONCEKI_SURUMLER.md` eski MVP ayrımı; `docs/GERCEK_DENEY_RAPORU.md`, `docs/TOPLANTI_REHBERI.md`, `docs/REAL_PROTOCOL.md`, `docs/QGIS_REHBERI.md`; `docs/archive_v1/` ilk sürüm belgeleri; `data/disfor/README.md` kaynak veri; `reports/exploratory_three_class/STATUS.md` üç sınıflı keşfin neden ana sonuç yapılmadığı; `third_party/natural_earth/LICENSE.md` üçüncü taraf lisansı. **Bütün MD dosyalarının tek tek tam adresi** envanterde bulunur; `output/Orman_SSL/` altındaki kopyalar da ayrı gösterilir.

## 7. Teslim paketleri ve hangisi ne için?

| Paket | Tam proje klasöründeki konum | Kapsam |
|---|---|---|
| Hocaya sunum | `output/Orman_SSL_Hocaya_Sunum.zip` | Rapor, makale, görüşme metinleri ve çevrimdışı araştırma sayfası; canlı model içermez |
| Tam proje | `output/Orman_SSL_Proje_Paketi.zip` | Kod, ham/işlenmiş veri, model, deney kayıtları ve belgeler; başka bilgisayara taşımak için |
| Bilimsel deney | `output/Orman_SSL_Paper_Paketi.zip` | `paper_v4` karşılaştırmasını işlenmiş veriden tekrar üretmeye yönelik paket; ürün ağırlıkları yok |
| Nihai model | `output/Orman_SSL_Nihai_Model.zip` | Hazır etiketsiz NPZ üzerinde eğitilmiş modelden tahmin için küçük paket |

Paketlerin ayrı README/manifestleri vardır. `output/package_manifest.json`, `output/paper_package_verification.json`, `output/advanced_package_verification.json`, `output/final_release_verification.json` ve `reports/final_delivery_verification.json` ilgili kayıtlar arasındadır. `output/Orman_SSL/` hocaya sunum ZIP'inin açılmış/kopyalanmış içerik ağacıdır; proje kökündeki `paper/` ve `reports/` ile benzer dosyalar bulundurması yeni bir araştırma sürümü olduğu anlamına gelmez. Sonradan değişen tekil belgeler **eski ZIP'in içinde kendiliğinden güncellenmez**. 15 sayfalık rehberi paketle birlikte vereceksen PDF'yi ayrıca ekle veya paket içeriğini yeniden üretip doğrula.

## 8. Sonradan yapılmış keşifler ve geliştirme araçları

`experiments/presto_v1_exploratory/` sabit geçmiş kohortta Presto temsilinden çizgisel probeleri araştırır: 90 fit ve kayıtlı analiz vardır. `reports/presto_probe_verification.json` hesapları denetler. Bu, Presto ile ana makalede doğrudan eşlenmiş bir üstünlük yarışması veya dış doğrulama değildir. `scripts/train_presto_probe.py` ve `scripts/verify_presto_probe.py` kodlarıdır; kullanılan üçüncü taraf içerik `third_party/` altındadır.

`experiments/paper_v5_exploratory/` 5/10/20 km mekânsal yarıçap duyarlılığı **uzantısıdır**; 16 Ekim 2026'da analizi, checkpoint doğrulaması ve raporu (`docs/PAPER_V5_MEKANSAL_DUYARLILIK.md`, `radius_sensitivity.png`) tamamlandı. Tek seed ve betimseldir; 20 km'de SSL en iyi, 5 km'de adım eşlenmiş denetimli en iyi çıkar. Makalede Bölüm 5.2, Tablo 6 ve Şekil 5 olarak yer alır. Betikler `scripts/scientific_v5.py`, `scripts/report_spatial_v5.py`, `scripts/verify_spatial_v5.py`.

`experiments/paper_v6_label_curve/` 16 Ekim 2026'da ilan edilip koşulan **etiket bütçesi eğrisi uzantısıdır**: %5/%10/%50 etiket, v4'ün aynı katları, seed'leri ve tarifleri, 5 yöntem, 225 koşu. Etiket tahsisi eğitimden önce `label_allocation.json` ile ilan edilir; `analysis.json`, `combined_curve.csv` ve `oof_predictions.npz` üretir. Makalede Bölüm 5.1, Tablo 5 ve Şekil 4. Betik `scripts/label_curve_v6.py`, şekiller `scripts/plot_extensions.py`, testler `tests/test_label_curve_v6.py`. Linux konteynerde eğitildiği `execution.json` içinde kayıtlıdır.

`external_validation/` gerçek, yeni ve kör etiketlenmiş veri için plan, aday denetimi, dondurma ve yorumlayıcı uzlaşması şablonlarını sağlar. **Burada henüz dış saha verisi, insan etiketleme sonucu veya yeni Türkiye F1 skoru yoktur.** `external_validation/README_TR.md` koşulları anlatır; `workflow.py` araçtır. `reports/exploratory_three_class/` önceki üç sınıflı keşiftir; ayrılmış testte yalnız bir yangın gözlemi bulunduğu için ana bilimsel değerlendirme yapılmadı.

## 9. Kaynak kodu ve testlerin yerleri

| Klasör veya dosya | Rolü |
|---|---|
| `src/orman_ssl/inputs.py` | Model girdisi ve veri sözleşmesi denetimi |
| `src/orman_ssl/advanced.py` | Güncel ensemble bileşenleri ve eğitim/çıkarım mantığı |
| `src/orman_ssl/predict_advanced.py` | Güncel modelin etiketsiz girdi çıkarımı |
| `src/orman_ssl/experiment.py` | Önceki bilimsel/MVP deney yordamları |
| `src/orman_ssl/predict.py` | Önceki MVP çıkarımı |
| `scripts/prepare_disfor.py` | Kaynaktan 24 aylık örnek ve mekânsal grup oluşturma |
| `scripts/train_paper.py`, `analyze_paper.py`, `verify_paper.py` | `paper_v4` eğitimi, analizi ve kaydı doğrulama |
| `scripts/train_advanced.sh`, `evaluate_advanced.py`, `verify_advanced.py` | Ürün modeli eğitimi, değerlendirmesi ve doğrulaması |
| `scripts/run_advanced.py`, `serve_product.py`, `product_data.py` | Ham veriden güncel çıkarım ve yerel ürün |
| `scripts/package_project.py`, `package_paper.py`, `package_advanced.py`, `verify_package.py` | Paketleme ve ZIP bütünlüğü |
| `scripts/verify_final_delivery.py` | Teslimin birleşik yerel kontrolü |
| `tests/` | Ana ürün, girdi, deney ve paket testleri |
| `external_validation/tests/` | Gelecekteki dış değerlendirme iş akışının yapay testleri |

Yerel son teslim denetimi `reports/final_delivery_verification.json` içinde **58 test geçti**, 180 mevcut bilimsel eğitim kaydı ve 10 ürün model üyesi doğrulandı diye kaydediyor. Bu denetim 30 Eylül 2026 tarihli durumun kanıtıdır. Kaydı anlamak için `reports/final_delivery_tests.log`, `reports/final_science_review.json` ve `reports/final_engineering_review.json` aç. 15 sayfalık rehberin ayrıca 16 Ekim'de PDF/DOCX içeriği ve 15 sayfalık görsel düzeni denetlenmiştir. **58 testin geçmesi Türkiye saha başarımı veya yeni eğitim yapıldığı anlamına gelmez.**

## 10. Hocaya açacağın sıra ve dürüst anlatım

1. `output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf` ile **amaç ve iki sürümü** göster: bilimsel karşılaştırma `paper_v4`, çalışan ürün `advanced_v3`.
2. `reports/paper_v4.html` veya makaledeki sonuç şeklinde **0,8322 → 0,8690 → 0,8987** karşılaştırmasını anlat: kısa denetimli model, SSL, daha uzun denetimli kontrol. Ana mesaj karşılaştırıcı seçiminin yorumu değiştirmesidir.
3. `URUNU_AC.command` ile arayüzü aç; bir doğru bulunan kesim (`disfor-1733-2019`, skor 0,9981) ve bir kaçırılan kesim (`disfor-1664-2018`, skor 0,0176) göster. İkisi de geçmiş değerlendirme örneğidir; skor etiketi değiştirmez.
4. “Örnek veride analizi çalıştır” ile **kaydedilmiş modelin ham veriden yeniden çıkarımını** göster; bunun yeniden eğitim olmadığını söyle. Çıktıların `output/product_demo/` klasörüne yazıldığını göster.
5. Bir sayı sorulursa `paper/CLAIM_LEDGER.md`, `experiments/paper_v4/analysis.json` veya `models/advanced_v3/model_card.json` ile kaynağı aç. Bilmediğin ayrıntı için kesin konuşmadan dosyayı kontrol et.
6. Gelecek kararı olarak yeni coğrafyadan, yeterli kesim/orman desteği olan **gerçek bağımsız değerlendirme** ve yayın katkılarının insan araştırmacılarla netleştirilmesini öner.

Kısa açıklama cümlesi: “Gerçek Sentinel-2 zaman serilerinden ikinci yıldaki orman kesimini geriye dönük sınıflandıran çalışan bir ürün yaptık. Araştırmada az etiketli SSL'yi beş coğrafi kat ve üç seed ile sınadık. SSL kısa denetimli Transformer'dan iyi; daha uzun denetimli karşılaştırıcı macro-F1'de daha iyi. Ürün modelinin daha önce incelenmiş 486 örnekteki sonucu ayrı; Türkiye'ye bağımsız genelleme henüz ölçülmedi.”

## 11. Herhangi bir dosyayı nasıl bulursun?

- Dosya adını biliyorsan [tam envanterde](TUM_DOSYALAR_ENVANTERI.md) ara; **her satır tıklanabilir tam dosya konumunu** verir.
- Klasörleri zihninde şöyle tut: `data` **girdi**, `experiments` **öğrenme kayıtları**, `models` **eğitilmiş ağırlıklar**, `src`/`scripts` **kod**, `paper` **makalenin aslı**, `docs` **Türkçe açıklamalar**, `reports` **denetim/HTML**, `output` **sunulacak sonuç ve paketler**.
- Aynı isimli birden çok dosya varsa **önce bu belgedeki sürüm ayrımını** kontrol et. `docs/archive_v1`, `reports/demo_v1.html`, `models/model.pt`, `output/pdf/Orman_SSL_Toplanti_Dosyasi.pdf` ilk dönem kayıtlarıdır. `output/Orman_SSL/` kopya teslim ağacıdır.
- Dosyaları değiştirdikten sonra eski ZIP, PDF veya hash raporunun otomatik güncellendiğini varsayma. Değişikliğin ilgili belge/ürün/paket doğrulamasını yeniden çalıştır.

**İleriye dönük açık kararlar:** Makalenin gerçek yazarları, kurum/katkı/fon beyanları ve hedef dergi `paper/AUTHOR_CONFIRMATION.md` doğrultusunda insan araştırmacılarla netleşmeli. Bağımsız saha veri desteği kurulmadan yeni ülke başarımı söylenmemeli. `paper_v5_exploratory` ve Presto keşiflerinin sonuçları ancak kendi analiz ve kapsam sınırlarıyla ayrı sunulmalı. Hiçbir dosyanın akademik dergiye gönderildiği veya internet üzerinde yayımlandığı iddia edilmez.
