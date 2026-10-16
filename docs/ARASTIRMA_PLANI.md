# Tamamlanan deney ve araştırmanın devamı

Güncel sonuç: `GERCEK_DENEY_RAPORU.md`. İlk sürüm planı `archive_v1/ARASTIRMA_PLANI.md` altında saklanır.

## Bu sürümde tamamlananlar

Gerçek DISFOR verisinin temini; etiket ve zaman eşleştirme; 24 aylık seriler; 5 km/olay ayrımı; 36 gerçek eğitim koşulu; model seçimi; 1.000 bootstrap tekrar; eksik gözlem deneyi; hata atlası; GeoJSON tahminleri; etiketsiz yeni girdide çıkarım; 18 test; çevrimdışı demo ve güncellenmiş PDF.

## Araştırma sonucu

Mevcut protokolde SSL, az etiketli supervised Transformer'a üstünlük sağlamadı. RF az etiket koşullarında güçlü. Tam etikette supervised Transformer en yüksek ortalama test macro-F1'e ulaştı. Bu bulgu model geliştirmeye nereden başlanacağını gösterir; sonuçları değiştirmek için test üzerinde hiperparametre aramak yapılmadı.

## Yeni bir çalışma olarak değerlendirilecek uzantılar

- Eğitim tarafında sınıf ağırlığı, maskeleme hedefi ve ön eğitim çeşitliliğini validation üzerinden araştırmak; yeni nihai dış test ayırmak.
- Birden çok mekânsal fold ve ülke/campaign dışı test ile coğrafi genellemeyi ölçmek.
- İzinli ve doğrulanmış Sentinel-1 zaman serileri temin edilirse radar katkısını ayrı çalışmak.
- Türkiye uygulaması için bağımsız olay etiketi toplamak ve alan uyumunu denetlemek.

Bunlar tamamlanmış MVP'nin gizli eksikleri olarak sunulmaz; şu anki modelin çözdüğü S2 kesim görevinin ötesindeki araştırma kapsamıdır. Yayın yeniliği bu genişletmeler ve daha kapsamlı literatür değerlendirmesiyle kararlaştırılır.
