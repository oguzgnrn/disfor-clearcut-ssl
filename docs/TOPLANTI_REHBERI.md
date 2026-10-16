# Güncel toplantı rehberi — gerçek deney

## Söyleyeceğin ana cümle

“Hocam, gerçek etiketli Sentinel-2 zaman serileriyle uçtan uca bir deneyi tamamladım. Aynı coğrafi ayrımda Random Forest, Transformer ve self-supervised ön eğitimli Transformer'ı karşılaştırdım. Bu ilk kurulumda SSL üstünlük sağlamadı; az etikette Random Forest güçlü, tam etikette Transformer daha iyi çıktı.”

## 8 dakika

1. **1 dk:** Araştırma sorusu ve kesim/bozulmamış orman kapsamı.
2. **1,5 dk:** 2.213 gerçek seri; 1.266/461/486 ayrımı; 5 km coğrafi koruma; etiket kökeni.
3. **2 dk:** Gerçek deney tablosu. Ortalama 0,877 ile seçilen checkpoint 0,861 arasındaki farkı açıkla.
4. **1,5 dk:** Demo filtrelerinden bir doğru kesim ve bir kaçırılan kesim aç; eğrileri yorumla.
5. **1 dk:** 12 kaçırılan kesim, kaynak kampanyaları ve dengesizliğin sınırları.
6. **1 dk:** Bulguyu hangi bilimsel uzantıyla güçlendireceğinizi konuş.

## Kritik sorular

**“Neden SSL kazanmadı?”** Bu deney sınıf dengesizliğine ve kullanılan ön eğitim hedefine duyarlı olabilir. Bunlar hipotez; kanıtlanmış neden gibi anlatmam. RF sonucunu saklamadım. Testte ayar aramadan sonraki validation deneyini tasarlamak gerekir.

**“Gerçek veri mi?”** Evet. DISFOR'un yorumlanmış gerçek S2 serileri. Yeni arazi doğrulaması yaptığımı söylemiyorum. Önceki sentetik çalışma ayrı arşivde.

**“Yangın da var mı?”** Ana modelin görevi kesim. İlk üç sınıflı ayrımda yangın test desteği yetersizdi; model skorlarını okumadan kapsamı daralttım.

**“Model çalışıyor mu?”** Evet; `models/model.pt` ve etiket gerektirmeyen tahmin komutu var. 486 test girdisinde kayıtlı sonuçlarla eşleşmesi test edildi.

**“Yayın hazır mı?”** Gerçek deney ve rapor hazır; yenilik, dış doğrulama ve yayın kapsamını birlikte değerlendirmek gerekir. Başarım sayısı tek başına yayın katkısı değildir.

## Güncel e-posta taslağı — gönderilmedi

Nida Hocam merhaba,

Yönlendirmeniz doğrultusunda ilk veri incelemelerinin ardından, gerçek etiketli Sentinel-2 zaman serileriyle bir sınıflandırma deneyi tamamladım. DISFOR verisinden 2.213 uygun seri hazırlayıp coğrafi ayrımı koruyarak Random Forest, Transformer ve self-supervised ön eğitimli Transformer'ı farklı etiket bütçelerinde karşılaştırdım.

İlk sonuçlarda az etikette Random Forest'ın güçlü kaldığını, kullandığım SSL ön eğitiminin ise üstünlük sağlamadığını gördüm. Tam etiketli Transformer için ortalama test macro-F1 yaklaşık 0,877. Sonuçları, hata örneklerini ve yöntemin sınırlarını kısa bir dosyada topladım; çalışan model ve örnekleri inceleyebileceğimiz bir demo da hazır.

Toplantıda hem bulguları hem de hangi araştırma uzantısının anlamlı olacağını sizinle değerlendirmek isterim.

Teşekkür ederim hocam, iyi çalışmalar dilerim.

Saygılarımla,
Mehmet Oğuz Güneren
