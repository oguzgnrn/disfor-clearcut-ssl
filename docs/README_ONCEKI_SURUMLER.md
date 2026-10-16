# Orman-SSL — bilimsel deney ve makale paketi

## Güncel araştırma sürümü — paper_v4

27 Eylül son denetimi: ham veriden tüm örnekler birebir yeniden üretildi; 215 olay grubu ve yinelenen gözlem dizileri kontrol edildi. 81 hata inceleme adayı QGIS ve tarayıcıya eklendi. Yıl/kampanya kırılımları `paper/ERROR_AUDIT.md` içindedir. Eski adı korunan `Orman_SSL_Hocaya_Sunum.zip` artık güncel makaleyi taşır.

**180 gerçek eğitim tamamlandı; 5 coğrafi kat, 3 seed, 2 etiket bütçesi ve 4 kontrol deneyi.** 2.213 konum ve 874 mekânsal bileşen kullanıldı. Tüm sonuçlar ve olumsuz bulgular korunuyor; 45 test ve bağımsız kayıt/ölçüt doğrulaması geçti.

- Makale: `output/paper/Orman_SSL_Manuscript.docx` ve `output/pdf/Orman_SSL_Manuscript.pdf` (İngilizce, 11 sayfa).
- İnceleme paketi: `output/Orman_SSL_Paper_Paketi.zip`; ham veri ve eski modeller dahil tam proje: `output/Orman_SSL_Proje_Paketi.zip`.
- Güncel Türkçe araştırma özeti: `reports/paper_v4.html`; Mac kısayolu: `PAPER_RAPORUNU_AC.command`.
- Makale kaynağı, 3 şekil, 4 tablo, kaynakça ve ek yöntemler: `paper/`.
- Tekrar üretim: `paper/SUPPLEMENT.md`; iddia–kanıt eşleştirmesi: `paper/CLAIM_LEDGER.md`.

**Ana bulgu:** %20 etiketle SSL macro-F1 0,8690; kısa denetimli Transformer 0,8322. Fakat yaklaşık eşit optimizasyon adımı alan denetimli model 0,8987 ile daha iyi. Tam etiketli CNN ortalaması 0,9299. Bunlar sabit coğrafi katlarda toplanan tahminlerden hesaplandı; bağımsız dış saha sonuçları değildir. Yeni mimari veya SOTA iddiası yok.

Çalışma, aynı veride önceki geliştirmelerin ardından yapılan geriye dönük bir denetimdir. Kullanılmamış konum taramasında yalnızca 1 pozitif / 111 örnek bulunduğundan dış doğrulama skoru üretilmedi. Yazar, kurum, katkı, fon ve dergi kararları gerçek araştırmacılarla kesinleştirilmeli; ayrıntı `paper/AUTHOR_CONFIRMATION.md`. Hiçbir dosya yayımlanmadı veya gönderilmedi.

Aşağıdaki advanced_v3, çalışan çıkarım modeli ve önceki geliştirme kaydıdır. paper_v4'teki tekil modellerin çapraz doğrulama sonuçlarıyla aynı deney değildir.


**Gerçek Sentinel-2 verisinde eğitilmiş model, coğrafi test, deney raporu ve çalışan tahmin aracı.** Görev: 24 aylık seriden bozulmamış orman / kesim ayrımı. Bu sürüm yalnızca sentetik başlangıç değildir.

## Nihai model — advanced_v3

**Eğitim tamamlandı:** 24 coğrafi CV koşulu + 10 nihai üye + 18 düşük etiket koşulu = 52 eğitim koşulu. Bu sürüm tamamlandığında 37 otomatik test geçmişti; güncel proje toplamı 45 testtir. Nihai model, geliştirilmiş SSL Transformer ve CNN64'ün beşer eğitiminden oluşur.

Aynı geçmiş 486 örneklik testte macro-F1 **0,9187** (önceki model: 0,8615); 38 kesimin 28'i bulundu, 10'u kaçırıldı; bozulmamış 448 noktada 0 yanlış kesim alarmı. PR-AUC 0,9359. Test daha önce incelendiğinden dış doğrulama değildir. Grup bootstrap sonuçları ve kalibrasyon karşılaştırması makine kayıtlarında korunur.

Taşınabilir çıkarım paketi `output/Orman_SSL_Nihai_Model.zip`; tam eğitim/veri paketi `output/Orman_SSL_Proje_Paketi.zip`. Eski toplantı PDF'si ve demo önceki MVP sürümünü anlatır. Güncel makale ve deneyler yukarıdaki paper_v4 paketindedir.

Yeni çalışma önceki MVP'den ayrı sürümlenmiştir. `models/advanced_v3/bundle.json` model üyelerini, kalibrasyonu, karar eşiğini ve dosya hash'lerini tanımlar. Tam model seçimi eğitim verisindeki dört coğrafi katta yapılır; en iyi iki ayar beşer seed ile eğitilip birleştirilir. Eski model `models/model.pt` karşılaştırma amacıyla korunur.

Mac'te `MODELI_CALISTIR.command` dosyasını çalıştır. Terminalden:

```bash
.venv/bin/python scripts/run_advanced.py
```

Ham veriden üretilen yeni model çıktıları `output/advanced_prediction/` içindedir. Kendi uyumlu gözlem Parquet'in için `--observations`, `--windows`, `--source`, `--out` seçenekleri aşağıda açıklanan veri sözleşmesini kullanır.

Hazır etiketsiz NPZ için:

```bash
PYTHONPATH=src .venv/bin/python -m orman_ssl.predict_advanced \
  --bundle models/advanced_v3/bundle.json \
  --data data/processed/test_inference.npz \
  --out output/advanced_prediction/npz_predictions.json
```

Eğitimi tekrarlamak için `bash scripts/train_advanced.sh`. Tamamlanmış koşular kayıtlarından devam edilir; eğitim kodu/veri/protokol değişirse eski kayıtlarla karışması engellenir. Yeni bir deney tasarımı için ayrı sürüm gerekir. Model bileşenleri `src/orman_ssl/advanced.py` içinde; kapsam ve önceden belirlenen seçim kuralları `experiments/advanced_v3/protocol.json` içindedir.

Makinece okunabilir nihai değerlendirme `experiments/advanced_v3/evaluation.json`, kabul kontrolleri `experiments/advanced_v3/acceptance.json`, model kartı `models/advanced_v3/model_card.json` içindedir. Güncel test kayıtları `experiments/advanced_v3/tests.log` altındadır. Güncel bilimsel rapor paper_v4 altında hazırlanmıştır; aşağıdaki önceki sürüm sonuçları tarihsel karşılaştırma içindir. Yeni test de daha önce incelenmiş aynı 486 örneği kullanır; dış saha doğrulaması değildir.

## Önceki sürüm dosyaları

1. `output/pdf/Orman_SSL_Toplanti_Dosyasi.pdf` — önceki sürüm toplantı dosyası.
2. `reports/demo.html` — çevrimdışı rapor; gerçek test örnekleri, tahminler, hata filtresi ve eğriler. Mac'te `DEMOYU_AC.command` da açar.
3. `docs/GERCEK_DENEY_RAPORU.md` — yöntem, gerçek sonuçlar ve sınırlılıklar.
4. `docs/TOPLANTI_REHBERI.md` — bu tamamlanmış deneyi anlatma akışı.

## Önceki MVP sürümünde ne tamamlandı?

| Teslim | Durum |
|---|---|
| Gerçek etiketli veri | DISFOR sabit revision; 2.213 yüksek güvenli, uygun 24 aylık seri |
| Coğrafi ayrım | 1.266 eğitim / 461 validation / 486 test; kümeler arası minimum 5 km |
| Modeller | RF, supervised Transformer, SSL Transformer; 4 bütçe × 3 seed = 36 gerçek koşul |
| Seçilen model | Validation ile yöntem seçimi, sabit seed 7; `models/model.pt` |
| Yeni girdide tahmin | `orman_ssl.predict`; etiket gerektirmez; gerçek test girdisinde doğrulandı |
| Belirsizlik ve dayanıklılık | 1.000 grup bootstrap; %0/%20/%40/%60 ek ay kaybı |
| İnceleme | Hata atlası, gerçek test nokta tahminleri GeoJSON, etkileşimli örnek raporu |
| Doğrulama | O sürümde 33 test geçti; kaynak hash'leri ve raster kontrolleri ayrıca mevcut |

**Sonuç:** Tam etiketli Transformer'ın üç seed ortalama test macro-F1'i 0,877. Dağıtılan sabit checkpoint 0,861. %20 etikette RF 0,811; bu SSL uygulaması üstünlük göstermedi. Kesim sınıfında seçilen model 38 örneğin 26'sını buldu, 12'sini kaçırdı. Yüzde doğruluk ile macro-F1 aynı metrik değildir.

## Tek komutla ham veriden tahmine

Mac'te `MVP_CALISTIR.command` dosyasını çalıştır; terminal alternatifi:

```bash
.venv/bin/python scripts/run_mvp.py
```

Bu komut ham DISFOR gözlemlerini okur, etiket sütunlarını dışlar, kaynak kalite maskesini uygular, 24 aylık serileri oluşturur ve kayıtlı modeli çalıştırır. 486 örneğin çıktıları `output/prediction/` altındadır: `input.npz`, `predictions.json`, `predictions.geojson`, `manifest.json`. Önceden ölçülen test örneklerinin tekrar işlenmesidir; yeni bağımsız değerlendirme sayılmaz. Model yeniden eğitilmez.

Kendi uyumlu gözlemlerinde:

```bash
.venv/bin/python scripts/run_mvp.py \
  --observations /tam/yol/observations.parquet \
  --windows /tam/yol/windows.json \
  --source 'Veri kaynağı ve DN işleme geçmişi' \
  --out output/my_prediction
```

Gözlem tablosunda `sample_id`, `timestamps`, `clear`, `SCL` ve 10 bant gerekir; `label` gerekmez. Pencere JSON'u `data/examples/inference_windows.json` biçimindedir: her örnek için tekil `id`, `sample_id`, `target_year`; harita çıktısı için isteğe bağlı WGS84 `lon`/`lat`. `target_year` iki yıllık pencerenin ikinci yılıdır. Kaynak ve DN işleme uyumu kullanıcı tarafından sağlanmalıdır; araç beyana bakarak fiziksel uyumu kanıtlayamaz. Aynı çıktı klasöründe tekrar çalıştırmak önceki tahmin dosyalarını yeniler.

Yeni çalışma için `bash scripts/setup.sh` Python 3.11 ortamını ve ana bağımlılıkları kurar. `bash scripts/check.sh` modeli eğitmeden ortamı, testleri ve ham veri çıkarımını kontrol eder. Bu komutlar PDF veya araştırma raporu üretmez.

## Hemen tahmin üret

Bu makinedeki `.venv` hazırdır. Komutları proje kökünden çalıştır:

```bash
PYTHONPATH=src .venv/bin/python -m orman_ssl.predict \
  --checkpoint models/model.pt \
  --data data/processed/test_inference.npz \
  --out reports/my_predictions.json
```

Girdi 486 gerçek test örneğinin **etiketsiz** sürümüdür. Çıktı ID, tahmin, sınıf skorları ve kalite uygunluğudur. Kendi verin için `docs/VERI_SOZLESMESI.md` kullan. Model Türkiye'deki rastgele tek görüntüye veya mevcut iki tarihli dNBR kesitine doğrudan uygulanamaz.

## Kurulum ve tüm deneyi yeniden üret

Python 3.11 ile:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
```

Yerel veriyle internet gerekmez:

```bash
python scripts/prepare_disfor.py
PYTHONPATH=src python -m orman_ssl.experiment --data data/processed/real_series.npz --out reports/real_experiment
python scripts/analyze_real.py
python -m unittest discover -s tests -v
python scripts/build_real_report.py
```

`bash scripts/reproduce.sh` veri hazırlama, eğitim, analiz, test ve ham girdiden çıkarım zincirini çalıştırır; mevcut HTML/PDF belgelerini değiştirmez. Belge üretimi gerektiğinde `bash scripts/reproduce.sh --with-reports` kullan. PDF bağımlılıklarını önce `python -m pip install -r requirements-report.txt` ile kur. Ana deney sabit 30 ön eğitim + 25 fine-tune epoch; hesaplama süresi `results.json` içinde. Model sonuçları donanım/kitaplık farklarıyla küçük değişiklik gösterebilir.

Ham veriyi yeniden almak için `python scripts/download_disfor.py`. Yalnızca yaklaşık 66 MB tablolar alınır; 34 GB görüntü arşivi indirilmez. Veri sürümü ve SHA-256 kayıtları saklanır.

## Dosya haritası

- `src/orman_ssl/experiment.py`: train-only ön işleme, SSL, supervised ve RF.
- `src/orman_ssl/predict.py`: yeni veri çıkarımı, bant sırası/kalite kontrolleri.
- `scripts/prepare_disfor.py`: etiket-zaman eşleştirme, aylık seri, mekânsal gruplar.
- `scripts/analyze_real.py`: validation model seçimi, bootstrap, robustness, GeoJSON.
- `models/model_card.json` ve `docs/MODEL_CARD.md`: model seçimi ve kullanım sınırı.
- `data/disfor/sample_manifest.json`: örnek kökeni, konumu, yılı ve split.
- `reports/real_experiment/`: bütün gerçek deneyler, checkpoint'ler ve tahminler.
- `reports/exploratory_three_class/`: destek yetersizliği nedeniyle ana değerlendirmeye alınmayan ilk üç sınıflı koşu; bilimsel başarı iddiası için kullanılmaz.
- `reports/demo_v1.html`, `reports/experiment/`, `docs/archive_v1/`: ilk sürüm; sentetik sonuçlar güncel gerçek deneyden ayrılmıştır.
- `docs/QGIS_REHBERI.md`: önceki gerçek GFD/Sentinel veri incelemesi.

## Kapsam ve kaynak

Bu tamamlanmış MVP gerçek, geriye dönük **Sentinel-2 kesim sınıflandırmasıdır**. Gerçek Sentinel-1 füzyonu, sürekli ülke haritası, yangın erken uyarısı veya bağımsız Türkiye saha doğrulaması içermez. Yayın yeniliği ve kabulü henüz iddia edilmiyor.

[DISFOR](https://huggingface.co/datasets/JR-DIGITAL/DISFOR): EUPL-1.2; lisans metni `data/disfor/LICENSE`, revision ve kaynak bilgisi manifestlerde. Etiketler kaynağın görüntü yorumları ve yardımcı kayıtlarına dayanır; yeni arazi gerçeği topladığımız iddia edilmez. Kaynak split'i yerine kendi coğrafi protokolümüz kullanılmıştır.

Önceki GFD örnekleri: Liu ve ark., [Figshare 28465178 v1](https://doi.org/10.6084/m9.figshare.28465178), CC BY 4.0. Sentinel ön inceleme çıktıları: Contains modified Copernicus Sentinel data (2021), Earth Search / Element 84. Kaynakların lisansları korunmuştur. DejaVu font lisansı `assets/fonts/` içinde. Yeni proje kodu için yayımlama öncesi proje sahipleri lisans seçmelidir.

Yapay zekâ yardımıyla hazırlanmıştır. E-posta gönderilmedi, proje internette yayımlanmadı. İşlenmiş veri ve modeller yalnızca yerel proje içinde bulunur.

## Teslim paketleri

`output/Orman_SSL_Proje_Paketi.zip` kod, ham ve işlenmiş veri, bütün ağırlıklar, raporlar ve manifestleri içerir. `output/Orman_SSL_Hocaya_Sunum.zip` güncel paper_v4 makalesi (PDF ve Word), çevrimdışı araştırma özeti ve görüşme notlarını içerir. Paketleri `python scripts/package_project.py` ile yeniden oluştur; her arşiv için CRC kontrolü ve SHA-256 kaydı üretilir.

`requirements-lock.txt` temiz Python 3.11 ortamında kurulup doğrulanan ana ve dolaylı bağımlılıkları sabitler. `reports/isolated_check.log` ilk temiz ortam kontrolünü, `reports/release_reproduction.log` ise arşivden çıkarılan kopyanın 33 testlik tam yeniden üretim kontrolünü kaydeder. Önceki PDF ve deney raporu bu mühendislik güncellemesinde yeniden yazılmadı; oradaki 18 test sayısı önceki sürüme aittir. Bu kayıt önceki sürümün 33 testini kapsar; güncel proje kontrolünde 45 test geçmektedir.

Teslim ZIP dosyasını açmadan önce `python scripts/verify_package.py output/Orman_SSL_Proje_Paketi.zip` ile bütün dosya hash'lerini ve arşiv yollarını doğrulayabilirsin. Tam paket, boşluk içeren farklı bir klasöre çıkarılarak kurulu temiz Python ortamıyla ayrıca çalıştırılmıştır; doğrulama kaydı `output/release_verification.json` dosyasındadır.
