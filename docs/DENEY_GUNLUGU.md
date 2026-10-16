# Sürüm 2 deney günlüğü

Önceki GFD/Sentinel/sentetik çalışma kaydı `archive_v1/DENEY_GUNLUGU.md` içinde korunur.

1. Açık DISFOR veri seti bulundu; sabit revision ve dosya hash'leri kaydedildi. Yaklaşık 66 MB tablolar indirildi.
2. Kaynak kartı 3.823 dese de indirilen samples tablosunda 3.822 nokta ölçüldü; raporda dosya sayısı kullanıldı.
3. Yüksek güvenli, zaman aralığı ve kalite koşullarını sağlayan 2.502 üç sınıflı örnek hazırlandı. İlk splitte test yangın sayısı 1 bulundu. Skorlar okunmadan ana görev kesim/bozulmamış ormana daraltıldı. İlk in-flight model koşusu yalnız denetim arşivinde tutuldu.
4. Ana veri: 2.213 örnek, 1.937 bozulmamış ve 276 kesim. Eğitim/validation/test 1.266/461/486. Coğrafi mesafe kontrolleri geçti.
5. Sabit ana hiperparametrelerle 36 gerçek model koşulu tamamlandı. Sonuçtan sonra hiperparametre araması yapılmadı. Kaydedilen süre yaklaşık 28 saniye; veri hazırlama ve analiz süreleri bundan ayrıdır.
6. Validation ortalamasıyla yöntem, sabit seed=7 ile checkpoint seçildi. Testten model/seed seçimi yapılmadı.
7. 1.000 mekânsal grup bootstrap ve 36 ek gözlem kaybı değerlendirmesi yapıldı. Bunlar yeni model eğitimleri değildir.
8. Model çıkarımı etiketsiz 486 örnek girdisinde çalıştırıldı; kayıtlı sonuçlar ve CLI çıktı tutarlılığı kontrol edildi.
9. 18 otomatik test geçti. PDF, çevrimdışı rapor ve örnek filtreleri son teslimde kontrol edildi.

Sonuçlar: tümü `reports/real_experiment/results.json`; ayrım/örnek manifestleri `data/disfor/`; kullanılan model seçimi `models/model_card.json`. Sınıf desteğine dayalı kapsam değişikliği saklanmadı. Kaynak etiketleri saha gerçeği topladığımız anlamına gelmez.

# Sürüm 3 ve uzantılar (16 Ekim 2026 güncellemesi)

10. `paper_v4` ana denetimi (180 koşu) 26 Eylül'de donduruldu; ayrıntı `paper/SUPPLEMENT.md`.
11. `paper_v5_exploratory`: 5/10/20 km gruplama yarıçapı, seed 7, %20 etiket, 75 koşu 1 Ekim'de eğitildi; 16 Ekim'de `analyze`, `verify_spatial_v5.py` (75 checkpoint yeniden yüklendi, en büyük olasılık farkı 2,2e-6, farklı platform) ve `report_spatial_v5.py` çalıştırılarak tamamlandı. 20 km'de SSL 0,844 > adım eşlenmiş 0,822 > CNN 0,800; 5 km'de sıralama tersi.
12. `paper_v6_label_curve`: %5/%10/%50 etiket bütçeleri, v4 katları ve seed'leri, 5 yöntem, 225 koşu; protokol ve etiket tahsisi eğitimden önce `label_allocation.json` ile ilan edildi; Linux konteynerde (Python 3.13, torch 2.14 CPU) eğitildi.
13. Makale kaynakçası 8'den 26'ya çıkarıldı (hepsi Crossref/yayıncı sayfasıyla doğrulandı); ilgili çalışmalar paragrafı, Bölüm 5.1–5.2, Şekil 4–5, Tablo 5–6 eklendi; `compose_paper.py` uzantı sonuçlarını analiz dosyalarından okur.
14. Hoca toplantısı için `docs/HOCAYA_ILK_NOTLAR_VE_FIKIRLER.md` ve `docs/PAZAR_TOPLANTI_AKISI.md` yazıldı; `paper/HOCAYA_NOT.md` güncellendi.
