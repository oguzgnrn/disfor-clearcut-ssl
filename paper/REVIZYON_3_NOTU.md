# Revizyon 3 notu (9 Kasım 2026)

Nida Hoca'nın `Orman_SSL_Makale_v2.docx` üzerindeki kırmızı notlarına karşılık yapılan değişiklikler. Metnin tamamı `scripts/compose_paper.py` içinden üretilir; sayılar `experiments/*/analysis.json` dosyalarından okunur, elle yazılmaz.

| # | Hocanın notu | Yapılan |
|---|---|---|
| 1 | Başlık önerisi | Başlık hocanın önerisi oldu: *Self-Supervised Forest Clear-Cut Detection Using Sentinel-2 Time Series*. |
| 2 | Yeni özet | Hocanın özeti kelimesi kelimesine kullanıldı; içindeki sayılar analiz dosyalarından okunur (0,8690, 0,8636, 0,0368, 0,8721, 0,8987, 0,0193, 0,8437 doğrulandı). |
| 3 | Giriş sonunda motivasyon ve katkılar | Giriş yeniden yazıldı: orman izleme bağlamı, literatür, iki metodolojik kaygı (optimizasyon bütçesi, mekânsal bağımlılık), amaç ve katkılar paragrafı, makale organizasyonu paragrafı. |
| 4 | II. Material and Methods + giriş paragrafı | Bölüm II adı değişti; alt başlıkları sayan giriş paragrafı eklendi. |
| 4 | Dataset and study sample (DISFOR makalesinden, görsellerle) | Hocanın yazdırdığı üç paragraf kelimesi kelimesine II.A'nın başında ("Viehweger et al., 2026" → [1]); ardından DISFOR makalesinden doğrulanmış ayrıntılar (kampanyalar, etiket hiyerarşisi, bantlar, SCL, lisans), zaman serisinin nasıl göründüğünü anlatan paragraf, Şekil 1 (konumlar) ve Şekil 2 (kesim öncesi/sonrası gerçek Sentinel-2 görüntüsü). |
| 5 | Study Design and Dataset Construction; Classification Models | Hocanın iki paragrafı kelimesi kelimesine II.B'nin başında (tek düzeltme: "three random," → "three random seeds"); II.C Classification Models, II.D Training protocol ayrıldı. |
| 6 | Evaluation Metrics and Uncertainty Analysis: formüller + gerekçe + referans | P, R, F1, macro-F1, AP, ROC-AUC, Brier formülleri yazıldı; seçim gerekçeleri için Sokolova & Lapalme 2009, Saito & Rehmsmeier 2015, Davis & Goadrich 2006, Fawcett 2006, Brier 1950, Efron 1979 eklendi (hepsi Crossref ile doğrulandı). |
| 7 | V. Experimental Results giriş paragrafı + örnek görsel | III. Experimental results giriş paragrafı; Şekil 2: dört örnek pencere (NDVI/NBR, gerçek etiket, dört modelin held-out olasılıkları). |
| 8 | Koda işaret eden ifadeleri çıkar | paper_v4/v5/v6, scripts/…, experiments/…, advanced_v3, sklearn fonksiyon adları metinden, tablo ve şekil altyazılarından çıkarıldı; compose_paper.py bunların geri gelmesini engelleyen bir kontrol içeriyor. |
| 9 | Discussion: kendimizle ve literatürle karşılaştırma, tablo, limitasyonlar | IV.A deneyler arası karşılaştırma; IV.B literatür: Kasım 2026 taramasında DISFOR ile yayımlanmış başka sınıflandırma sonucu bulunamadı (veri seti makalesi de baseline vermiyor), bu yüzden Tablo 8 benzer görevlerdeki çalışmaları (Schiller 2024, Zhang 2025, Kuzu 2024, Viana-Soto 2026, Giambelluca 2025) yan yana koyuyor ve üç gözlem çıkarıyor; IV.C Limitations. |
| 10 | Conclusion: genelden giriş, bulgular, ders, gelecek çalışmalar | Üç paragraf: bağlam, bulgular ve ders, gelecek çalışmalar (Türkiye sıfır atış testi, DISFOR ajan hiyerarşisi, Sentinel-1 füzyonu, Presto/SatMAE/Prithvi, büyük veri setleri, operasyonel gereksinimler). |
| 11 | Data availability: "source code is available at xxx [y]" | Cümle yazıldı; **depo adresi bekleniyor** ("[repository address to be added]"). GitHub deposu açıldığında tek satır değişecek. |
| 12 | Author contributions | "reviewed the interpretation and final text"; geçici yazarlık ve sorumluluk cümleleri silindi. |

Ek: referans listesi 26 → 36 (yeni 10 kaynağın tamamı Crossref ile doğrulandı). Tire kuralı: hocanın yazımına uyularak bileşik terimlerde tire korundu (Self-Supervised, Clear-Cut, Sentinel-2); `ORMAN_NO_HYPHENS=1` ile eski tiresiz sürüm yine üretilebilir.

Açık işler: GitHub depo adresi; Türkiye sıfır atış testinin çalıştırılması (Earth Search erişimi düzelince).
