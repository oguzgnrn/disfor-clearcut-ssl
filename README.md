# Orman SSL

Gerçek Sentinel-2 zaman serileriyle orman kesimi sınıflandırması. Eğitilmiş yerel model, çalışan inceleme uygulaması, Türkçe sonuç raporu ve İngilizce araştırma makalesi.

## Önce bunları aç

1. **Ürün:** Mac'te `URUNU_AC.command`. Kayıtlı 486 örneği incele; ham gözlemlerden modeli yeniden çalıştır; JSON ve GeoJSON çıktısını indir.
2. **Türkçe rapor:** [Araştırma ve ürün sonuçları](output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf). Düzenlenebilir [Word dosyası](output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.docx) aynı dizinde.
3. **İngilizce makale:** [Manuscript PDF](output/pdf/Orman_SSL_Manuscript.pdf) ve [Word](output/paper/Orman_SSL_Manuscript.docx).
4. **Görüşme (18 Ekim 2026, Pazar 17:00):** önce [ilk notlar ve fikirler](docs/HOCAYA_ILK_NOTLAR_VE_FIKIRLER.md), sonra [toplantı akışı ve soru listesi](docs/PAZAR_TOPLANTI_AKISI.md). Eski uzun akış: [7 dakikalık akış ve zor sorular](docs/GORUSME_AKISI_VE_SORULAR.md).
5. **Çevrimdışı araştırma özeti:** [paper_v4.html](reports/paper_v4.html); sunucu kurmadan açılır.

Yerel ürün, model ve hazır veriler kuruluysa internet gerektirmez. Canlı uygulama için HTML dosyasını doğrudan açmak yerine başlatıcıyı kullan. Sunucu yalnız bu bilgisayarın `127.0.0.1` adresinde çalışır.

## Kurulum ve çalıştırma

Bu çalışma klasöründe Python ortamı hazırdır. Başka bir bilgisayarda tam proje paketini çıkar, Python 3.11 kur ve proje klasöründe:

```bash
bash scripts/setup.sh
.venv/bin/python scripts/serve_product.py --open
```

İlk kurulum sabitlenmiş paketleri indirir. Terminalde `Ctrl+C` sunucuyu kapatır. [Ürün kılavuzu](docs/URUN_KILAVUZU.md) arayüzü ve yeni veri akışını açıklar.

Arayüz olmadan gerçek ham veriden tahmin:

```bash
.venv/bin/python scripts/run_advanced.py
```

Kendi uyumlu gözlemlerin için:

```bash
.venv/bin/python scripts/run_advanced.py \
  --observations /tam/yol/observations.parquet \
  --windows /tam/yol/windows.json \
  --source 'Veri kaynağı ve DN işleme geçmişi' \
  --out output/my_prediction
```

Girdi iki tam takvim yılı, 10 Sentinel-2 bandı ve gözlem maskesi gerektirir; etiket gerektirmez. `target_year` ikinci yıldır. Ayrıntılar [veri sözleşmesinde](docs/VERI_SOZLESMESI.md). Aynı çıktı diziniyle yeniden çalıştırma önceki tahminleri yeniler.

## Tamamlanan çalışma ve iki ayrı değerlendirme

| Bileşen | Veri ve yöntem | Doğrulanmış sonuç |
|---|---|---|
| Bilimsel deney paper_v4 | 2.213 konum, 874 mekânsal bileşen, 5 kat, 3 seed, 180 koşu | %20 etikette SSL 0,8690; kısa Transformer 0,8322; adım eşlenmiş Transformer 0,8987 macro-F1 |
| Ürün modeli advanced_v3 | 5 CNN + 5 SSL Transformer; önceki 486 örneklik benchmark | Macro-F1 0,9187; 38 kesimin 28'i bulundu, 10'u kaçırıldı |
| Hata incelemesi | Sabit bilimsel deneyin ayrılmış tahminleri | 81 inceleme adayı; kaynak etiketleri değiştirilmedi |
| Tekrar üretim | Sabit ham veri, etiket ve kat kimlikleri, ortam kilidi | 2.213 örnek birebir yeniden kuruldu; paketten tek SSL eğitimi aynı olasılıkları verdi |

| Uzantı paper_v5 | 5/10/20 km gruplama yarıçapı, seed 7, %20 etiket, 75 koşu | 20 km'de SSL 0,8437 > adım eşlenmiş 0,8216 > CNN 0,7997; 5 km'de sıralama tersi. Tek seed, betimsel. [Rapor](docs/PAPER_V5_MEKANSAL_DUYARLILIK.md) |
| Uzantı paper_v6 | %5/%10/%50 etiket bütçesi, v4 katları ve 3 seed, 5 yöntem, 225 koşu | Etiket eğrisi; `experiments/paper_v6_label_curve/analysis.json` ve makalede Tablo 5 / Şekil 4 |

Bu iki sürüm aynı deney değildir. Ürün skorunu makalenin sonuçlarıyla tek liderlik tablosunda karşılaştırma. 79.668 kayıtlı tahmin değeri 2.213 konum üzerindeki tekrarları içerir; bağımsız örnek sayısı değildir.

**Araştırma sonucu:** SSL'nin kısa denetimli karşılaştırıcıya göre kazancı var; daha uzun ve adım bütçesi eşlenmiş denetimli model karşısında macro-F1 üstünlüğü sürmüyor. Bu, yeni mimari veya genel SSL üstünlüğü iddiası değildir.

Çalışma, aynı kaynakta önceki model geliştirmelerinden sonra yürütülen geriye dönük bir denetimdir. Bağımsız Türkiye saha doğrulaması, Sentinel-1 füzyonu, sürekli ülke haritası ve erken uyarı kapsamda değildir. Kullanılmamış konum taramasında yalnız 1 kesim / 111 örnek kaldığından bağımsız başarı skoru üretilmedi.

## Doğrulama ve tekrar üretim

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/verify_paper.py
.venv/bin/python scripts/verify_advanced.py
.venv/bin/python scripts/verify_final_delivery.py
```

Son teslimdeki test sayısı, gerçek ürün çalıştırması ve belge kontrolleri [final_delivery_verification.json](reports/final_delivery_verification.json) içinde; [teknik denetim](docs/NIHAI_TEKNIK_DENETIM.md) önceki 45 çekirdek testin ve taşınmış modelin ayrıntısını içerir. [Bilimsel denetim](docs/NIHAI_BILIMSEL_DENETIM.md) kaynakları ve bağımsız ölçüt hesaplarını açıklar.

180 eğitimin ve iki uzantının (paper_v5, paper_v6) tekrar üretimi için [yöntem eki](paper/SUPPLEMENT.md) kullanılır. Makale kaynakçası 26 doğrulanmış kaynaktır (`paper/references.json`). Tamamlanmış koşular, dondurulmuş imza eşleşiyorsa önbellekten alınır. Gerçekten sıfırdan tekrar için yeni bir klasöre çıkartılan kopyada koşu kayıtlarını koruyarak ayır; özgün sonuçları silme. Başka donanımda küçük sayısal farklılıklar olabilir.

Türkçe rapor kaynağı [build_final_report.py](scripts/build_final_report.py), İngilizce makale kaynağı [manuscript.md](paper/manuscript.md). Belge üretimi için `requirements-paper.txt` gerekir. Rapor düzeni değişirse PDF ve Word birlikte yeniden üretilip görsel olarak kontrol edilmelidir.

## Hangi paketi götürmeliyim

| Paket | Kullanım |
|---|---|
| output/Orman_SSL_Hocaya_Sunum.zip | Türkçe rapor, İngilizce makale, görüşme notları ve çevrimdışı sonuç ekranı. Canlı model içermez. |
| output/Orman_SSL_Proje_Paketi.zip | Ürünü başka bilgisayarda çalıştırmak için kod, ham veri, modeller, belgeler ve deney kayıtları. |
| output/Orman_SSL_Paper_Paketi.zip | Bilimsel deneyi işlenmiş veriden tekrar üretmek için kompakt kod ve kanıt. Ürün modeli içermez. |
| output/Orman_SSL_Nihai_Model.zip | Hazır NPZ üzerinde yalnız eğitilmiş modelden tahmin üretmek için küçük paket. |

Her arşiv kendi başlangıç yönergesini ve SHA-256 dosya manifestini taşır. Açmadan bütünlüğü denetle:

```bash
.venv/bin/python scripts/verify_package.py output/Orman_SSL_Proje_Paketi.zip
```

Paketleri üretmek için sırasıyla `scripts/package_paper.py`, `scripts/smoke_paper_archive.py` ve `scripts/package_project.py` çalıştırılır. Son arşiv kontrolü `scripts/verify_final_delivery.py --archives` ile yapılır. Model paketini yalnız içeriği değiştiğinde `scripts/package_advanced.py` ile yenile.

## Kaynak ve araştırmacı kararları

Kaynak [DISFOR](https://huggingface.co/datasets/JR-DIGITAL/DISFOR), sabit revision `2562332e35c94c2339aeb341ffaed2a99faae7d6`. Kaynağın EUPL-1.2 lisansı `data/disfor/LICENSE` içinde korunur. Diğer önceki veri ve font atıfları [geçmiş sürüm rehberinde](docs/README_ONCEKI_SURUMLER.md) bulunur.

Kodun yayın lisansı, gerçek yazarlar, katkılar, kurum ve fon beyanları, hedef dergi araştırmacılarla kesinleştirilmeli. [Yazar değerlendirme notu](paper/AUTHOR_CONFIRMATION.md) bu kararları listeler. Yapay zekâ kodlama, analiz denetimi ve yazımda kullanılmıştır. Hiçbir dosya gönderilmedi veya kamuya yayımlanmadı.

İlk MVP, sentetik başlangıç ve eski toplantı dosyaları karşılaştırma için korunur. Güncel açılış yolu bu README'deki ürün ve rapordur; [önceki sürümlerin kayıtları](docs/README_ONCEKI_SURUMLER.md) tarihseldir.
