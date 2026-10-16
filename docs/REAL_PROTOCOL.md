# Gerçek veri deneyi: önceden sabitlenen protokol

DISFOR revision: `2562332e35c94c2339aeb341ffaed2a99faae7d6`.

Birincil görev: 24 aylık Sentinel-2 serisinden yorumlanmış bozulmamış orman / kesim ayrımı. Erken uyarı veya bozulma tarihini bulma deneyi değildir. Kaynak etiketleri uzman görüntü yorumu ve yardımcı olay kaynaklarına dayanır; arazi ölçümünü bizim yaptığımız iddia edilmez.

Sadece high-confidence örnekler, 2018-2023 hedef yılları. Pozitiflerde önceki takvim yılı tamamen orman olmalı; iki yıllık pencerede yalnızca bir bozulma olayı bulunmalı, kesim ikinci yılda olmalı. Negatifler iki yıl boyunca 110 etiketiyle örtülmeli. Bir kaynak noktadan yalnızca bir pencere kullanılır. Model girdisine olay günü veya etiket kodu girmez. Aylık medyan 10 DN bandı; source clear ve SCL 4/5; her yılda en az 6 gözlenen ay. Eksik aylar doldurulmaz.

Veride 5 km komşuluk bağlı bileşenleri ve aynı kaynak hasar poligonu/fırtına kimliği birleştirilir. Örnekleme strata'ları olay kabul edilmez. Sabit 1729/1730 grup ayrımı; gerçek en yakın kümeler arası mesafeler ayrıca hesaplanır. Kaynağın resmi split'i yerine bu projeye özgü daha açık mesafe kuralı kullanılmıştır; sonuçlar resmi benchmark skoru olarak sunulmaz.

İlk üç sınıflı hazırlıkta testte yalnızca bir wildfire örneği bulundu. Model skorları incelenmeden birincil görevden wildfire çıkarıldı. Bu karar veri desteğine dayanır. İlk üç sınıflı koşu denetim arşivinde tutulur; ana raporun kanıtı değildir.

Sabit 30 ön eğitim, 25 fine-tune epoch; 3 seed, 4 etiket oranı, 3 yöntem. Sınıf dengesizliği, veri toplama kampanyaları ve coğrafya olası karıştırıcılardır. Etiket oranları yalnızca eğitim bölümüne uygulanır; validation maliyeti ayrıca raporlanır. Test verisi hiçbir ön eğitim veya ölçekleme işlemine girmez. RF ve Transformer sonuçları birlikte sunulur; SSL'nin üstün çıkması başarı koşulu değildir.

Dağıtılacak checkpoint seçimi, %100 eğitim etiketi koşulundaki ortalama validation macro-F1 ile yöntem seçimi ve sabit seed=7 olarak belirlenir. Testte en iyi seed/yöntemi seçmek yoktur. Tüm eğitilmiş modeller korunur. Ek gözlem silme deneyi yalnızca test girdisine sabit maske uygular; yeniden ayar yapılmaz.

Belirsizlik: 1.000 test grubu bootstrap tekrarıyla yöntem farkları, seed'ler üzerinde ortalanarak. Bu tek coğrafi ayrımın örnekleme belirsizliğidir; başka ülkeye veya tüm dünyaya genelleme garantisi değildir. Ek dış ülke ve gerçek Sentinel-1 verisi bu veri setinden üretilemez; mevcut görevin sınırı açıkça Sentinel-2 kesim sınıflandırmasıdır.
