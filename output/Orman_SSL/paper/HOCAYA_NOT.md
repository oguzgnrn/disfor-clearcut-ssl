# Nida Hocayla görüşme için güncel araştırma notu

16 Ekim 2026 — İlk Teams görüşmesi Pazar 18 Ekim 17:00. Deney, uzantılar ve makale dosyası tamamlandı; hiçbir şey gönderilmedi.

**Önce şunu aç:** [`docs/HOCAYA_ILK_NOTLAR_VE_FIKIRLER.md`](../docs/HOCAYA_ILK_NOTLAR_VE_FIKIRLER.md). Hoca "ilk notlarını ve fikirlerini dinlemek" istedi; o belge ödev başlıklarına karşılıkları, makale notlarını, pilot bulguları ve soruları hocanın beklediği ölçekte anlatır. Konuşma sırası [`docs/PAZAR_TOPLANTI_AKISI.md`](../docs/PAZAR_TOPLANTI_AKISI.md) içindedir. Makale ve ürün yalnız istenirse açılır.

## Çalışmayı iki dakikada anlat

DISFOR'un gerçek Sentinel-2 serilerinden 2.213 yüksek güvenli konum seçtim; her konum iki takvim yılı, 10 bant. Görev bozulmamış orman ile kesimi ayırmak. Yakın konumları ve ortak olayları aynı grupta tutarak beş coğrafi katta, üç seed ile 180 eğitim yaptım.

%20 etikette SSL Transformer 0,8690; kısa denetimli Transformer 0,8322; yaklaşık aynı optimizasyon adımını alan uzun denetimli Transformer 0,8987. Ana bulgu "SSL üstündür" değil, karşılaştırıcının eğitim bütçesinin yorumu değiştirmesi. Tam etikette CNN 0,9299.

**Bu hafta eklenenler.** (1) Mekânsal yarıçap duyarlılığı (tek seed, 75 koşu): 5 km'de uzun denetimli model önde (0,9017 / SSL 0,8726), 20 km'de SSL önde (0,8437 / 0,8216 / CNN 0,7997). Eğitim-test ayrımı sertleşince ön eğitimli temsil daha az bozuluyor; tek seed olduğu için ipucu. (2) Etiket bütçesi eğrisi (%5/%10/%50, aynı katlar ve seed'ler, 225 koşu): sayılar `experiments/paper_v6_label_curve/analysis.json`, makalede Tablo 5 / Şekil 4. (3) Kaynakça 8 → 26 doğrulanmış kaynak; ilgili çalışmalar paragrafı; hocanın paylaştığı dört makale de kaynakçada.

## Somut olarak ne hazır

- İngilizce makale (`output/pdf/Orman_SSL_Manuscript.pdf`, `output/paper/Orman_SSL_Manuscript.docx`): yöntem, sonuçlar, iki uzantı bölümü, tartışma, 26 kaynak, 5 şekil, 6 tablo.
- Türkçe araştırma ve ürün raporu (`output/final/`), uzantı sayfasıyla güncellendi.
- Dondurulmuş protokoller ve koşu kayıtları: paper_v4 (180), paper_v5 (75), paper_v6 (225); doğrulama scriptleri; testler.
- Çalışan yerel ürün (`URUNU_AC.command`), 486 örnek, ham gözlemden yeniden çıkarım.
- Kör etiketleme iş akışı (`external_validation/`), gerçek dış veri geldiğinde kullanılmak üzere.

## İddiamın sınırı

Modeller aynı veride daha önce geliştirildi; yeni katlar çakışmayı önlüyor ama bu bağımsız dış doğrulama değil. Kullanılmamış konum taramasında yalnız bir kesim kaldı; skor üretmedim. Sentinel-1 yok, Türkiye verisi yok, yangın/hastalık yok, yeni mimari iddiası yok. Yarıçap sonucu tek seed; etiket eğrisinin %5–10 kısmı çok az kesim örneğiyle eğitildiği için geniş aralıklı. Presto ile dondurulmuş lineer probe 0,71 verdi; fine-tune edilmediği ve S1/iklim/yükseklik girdileri olmadığı için bunu karşılaştırma saymıyorum.

**Yapay zekâ kullanımı:** kodlama, deney düzeni, analiz kontrolü ve yazımda yoğun kullanıldı; hocaya ilk cümlede söylenecek. Yazarlık, kurum, fon ve dergi kararları `AUTHOR_CONFIRMATION.md` gereği insan araştırmacılara ait.

## Görüşmede birlikte kesinleştirilecek kararlar

1. Yayın ekseni: (a) kısa yöntem/değerlendirme makalesi, (b) Sentinel-1 eklenmiş tam makale, (c) Türkiye uygulaması.
2. Bağımsız değerlendirme verisi: BİLGEM/TÜBİTAK üzerinden Türkiye kesim veya yangın etiketi tedarik edilebilir mi?
3. Zhang ve ark. 2025 tam metnine erişim.
4. Hedef dergi/konferans ve yazar rolleri.
5. Haftalık çalışma düzeni.
