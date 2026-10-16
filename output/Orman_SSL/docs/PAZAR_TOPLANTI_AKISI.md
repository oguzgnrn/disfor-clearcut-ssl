# Pazar 18 Ekim 2026, 17:00 (Teams) — toplantı akışı ve soru listesi

Hocanın beklentisi (24 Eylül e-postası): "ilk notlarını ve fikirlerini dinlemek". Bu bir savunma değil, yön belirleme toplantısı. Ekrana bitmiş makaleyi değil, önce `docs/HOCAYA_ILK_NOTLAR_VE_FIKIRLER.md` belgesini aç; makale ve ürün yalnız istenirse gösterilir.

## Toplantıdan önce (Cumartesi)

- `output/egitim/Orman_SSL_15_Sayfada_Proje_Rehberi.pdf` baştan sona oku. Şu beş şeyi kendi cümlelerinle anlatabiliyor olmalısın: DISFOR nedir ve 2.213 konum nasıl seçildi; 5 km mekânsal kat ayrımı neden gerekli; maskeleyip yeniden kurma (SSL) fikri; macro-F1 ile accuracy farkı; "adım eşlenmiş kontrol" bulgusu.
- `URUNU_AC.command` ile ürünü bir kez aç, çalıştığını gör; `disfor-1733-2019` (doğru bulunan kesim) ve `disfor-1664-2018` (kaçırılan kesim) örneklerini önceden seç.
- Teams'te ekran paylaşımını dene; PDF'ler ve tarayıcı sekmesi açık olsun.

## 10 dakikalık akış

| Süre | Ne göster | Ne söyle |
|---|---|---|
| 0:00–1:00 | Hiçbir şey; kamera | "Hocam verdiğiniz başlıkları çalıştım, makaleleri okudum, bir de pilot deney kurdum. Önce kısaca öğrendiklerimi, sonra pilotu, sonra size sorularımı anlatayım. Kodlama ve analizde yapay zekâ araçlarını yoğun kullandığımı baştan söyleyeyim; anlattıklarımın arkasında durabildiğim kısmı ayırmaya çalışacağım." |
| 1:00–2:30 | İlk notlar belgesi, bölüm 1–2 | GFD'yi QGIS'te inceleme bulguları: 0 kodu çelişkisi, NoData yok, olay tarihi yok. Zhang makalesinden çıkan soru: %20 etikette SSL kazancı güçlü karşılaştırıcıya karşı sürer mi? |
| 2:30–3:30 | DISFOR seçimi | "Olay tarihi olan, gerçek etiketli, açık bir Avrupa veri seti buldum: DISFOR. 2.213 konum, 24 ay × 10 bant. Türkiye verisi bulamadığım için önce burada denedim; sizin 'farklı ülke verileriyle çalışıp sonra kendi ülkemizde test' yaklaşımınıza uyuyor." |
| 3:30–5:30 | Sonuç tablosu (ilk notlar bölüm 3) | 0,832 → 0,869 → 0,899. "SSL kısa eğitilmiş modeli geçiyor; ama aynı adım sayısını alan denetimli model SSL'yi geçiyor. Bulgum SSL'nin üstünlüğü değil, karşılaştırıcı bütçesinin sonucu değiştirmesi." |
| 5:30–6:30 | Yarıçap ve etiket eğrisi şekilleri (`paper/figures/05_radius.png`, `04_label_curve.png`) | "Eğitim-test bölgelerini 20 km ayırınca SSL öne geçiyor; tek seed, ipucu düzeyinde. Etiket eğrisinde %5–10'da bütün modeller çok az kesim örneğiyle eğitildiği için belirsizlik büyük." |
| 6:30–7:30 | Ürün ekranı (istenirse) | "Eğitilmiş modeli ham gözlemden yeniden çalıştıran yerel bir inceleme aracı da var; bu bir demo, saha ürünü değil." |
| 7:30–10:00 | Soru listesi (bölüm 5) | Yön (a/b/c), Türkiye verisi, Zhang tam metni, hedef yayın, haftalık düzen. |

**Kapanış cümlesi:** "Hocam ben buradan Sentinel-1 ekleme, Türkiye verisi ya da yöntem makalesi yollarından hangisine gideceğimizi sizinle kararlaştırmak istiyorum; hangisini seçersek haftalık plan çıkarıp size yazarım."

## Hocanın sorabileceği sorular ve dürüst cevaplar

**"Bunu sen mi yaptın?"** "Araştırma sorusunu, veri seçimini ve hangi kontrollerin gerektiğini ben belirledim; kodun büyük kısmını ve belge taslaklarını yapay zekâ araçlarıyla ürettim, çıktıları doğrulama scriptleriyle kontrol ettim. Her satırını tek başıma yazmış gibi sunmak istemiyorum; ama yöntemi ve sonuçları anlatabilecek kadar üzerinden geçtim."

**"Neden Türkiye değil?"** "Olay tarihli, bağımsız doğrulanmış açık Türkiye kesim etiketi bulamadım. Sizin önerdiğiniz gibi önce yabancı açık veriyle problemi tanıdım; Türkiye'yi ayrı dış test olarak saklıyorum. Veri tedarikinde yardımınıza ihtiyacım var."

**"Sentinel-1 nerede?"** "Henüz yok; pilotu tek sensörle sade tuttum. Paylaştığınız üç makalenin üçü de S1+S2 kullanıyor; bir sonraki adım olarak DISFOR konumları için S1 VV/VH indirip aynı protokolde füzyonu ölçmeyi öneriyorum."

**"SSL kazanmadıysa yayın değeri ne?"** "Zhang gibi çalışmaların %20 etiket sonuçlarının kısa eğitilmiş karşılaştırıcıya ne kadar bağlı olduğunu kontrollü biçimde göstermek başlı başına bir katkı olabilir; ayrıca mekânsal ayrım sıkılaşınca SSL'nin daha dayanıklı çıkması araştırmaya değer bir ipucu. Ama bunun hangi dergi için yeterli olduğunu siz daha iyi bilirsiniz."

**"2.213 örnek yeterli mi?"** "Kontrollü karşılaştırma için evet, genelleme iddiası için hayır. Kesim içeren yalnız 141 bağımsız mekânsal bileşen var; yakın noktaları bağımsız saymıyorum."

**"Veri sızıntısı?"** "Aynı mekânsal bileşen ve aynı kaynak olayı hiçbir zaman eğitim ve test arasında bölünmüyor; ölçekleme yalnız eğitimden öğreniliyor; test konumları ön eğitime de girmiyor. Ama modeller bu veride daha önce geliştirildiği için 'geriye dönük denetim' diyorum, bağımsız doğrulama değil."

**"Bana ne göndereceksin?"** "`output/Orman_SSL_Hocaya_Sunum.zip` içinde Türkçe rapor, İngilizce makale, bu notlar ve çevrimdışı sonuç sayfası var; isterseniz tam proje paketini de iletirim."

## Toplantı sonrası

Hocanın söylediklerini aynı gün yazıya dök (`docs/GORUSME_NOTU_2026-10-18.md`), ertesi gün e-posta zincirine kısa bir özet + haftalık plan gönder. Yazılı kararlar: yayın ekseni, veri tedariki, yazarlık/kurum, bir sonraki görüşme tarihi.
