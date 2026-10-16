# Orman-SSL — hocaya sunum ve inceleme paketi

Bu arşiv Türkçe araştırma raporu, İngilizce makale ve görüşme belgelerini
içerir. Hazır belgeleri okumak için Python kurulumu gerekmez.

## Önce açılacak dosyalar

1. `output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf`: Türkçe araştırma ve
   ürün raporu; düzenlenebilir Word karşılığı aynı klasördedir.
2. `docs/HOCAYA_ILK_NOTLAR_VE_FIKIRLER.md`: hocanın verdiği başlıklara
   karşılıklar, makale notları, pilot bulgular ve sorular;
   `docs/PAZAR_TOPLANTI_AKISI.md`: 18 Ekim görüşme akışı. Eski uzun akış
   `docs/GORUSME_AKISI_VE_SORULAR.md` içindedir.
3. `output/pdf/Orman_SSL_Manuscript.pdf`: İngilizce bilimsel makale;
   Word dosyası `output/paper/Orman_SSL_Manuscript.docx` içindedir.
4. `reports/paper_v4.html`: çevrimdışı araştırma özeti ve hata inceleme
   tablosu. Mac'te `PAPER_RAPORUNU_AC.command` ile de açılır.

`docs/URUN_KILAVUZU.md` ürünün kullanımını anlatır. Bu küçük sunum arşivi
ürün sunucusunu, ham veriyi ve model ağırlıklarını içermez. Ürünü gerçekten
çalıştırmak için `Orman_SSL_Proje_Paketi.zip` dosyasını açıp o paketin
README'sindeki kurulum ve `URUNU_AC.command` yönergelerini kullanın.

## Diğer paketler

- `Orman_SSL_Paper_Paketi.zip`: işlenmiş veri, 180 koşunun kayıtları ve
  paper_v4 deneyini yeniden çalıştırmak için bilimsel kod.
- `Orman_SSL_Proje_Paketi.zip`: yerel ürün, ham ve işlenmiş veri, bütün
  model ağırlıkları, eğitim kodu ve testler.
- `Orman_SSL_Nihai_Model.zip`: 10 üyeli advanced_v3 modeliyle hazır etiketsiz
  NPZ girdisinden çıkarım; bu paketin kendi README'si izlenmelidir.

Buradaki `paper/SUPPLEMENT.md` bilimsel tekrar üretim yöntemini açıklar;
komutları uygulamak için paper veya tam proje arşivi gerekir. Bu sunum
arşivi eğitim veya canlı ürün çalıştırma paketi değildir.

paper_v4, 2.213 konum üzerinde geriye dönük coğrafi araştırma denetimidir;
paper_v5 (gruplama yarıçapı, tek seed) ve paper_v6 (etiket bütçesi eğrisi)
aynı kohort üzerinde ilan edilmiş uzantılardır ve `experiments/` altında
özetleri bulunur.
Ürünün advanced_v3 modeli ayrı bir sürümdür; 486 noktalık değerlendirmesi
daha önce incelenmiş benchmark üzerindedir. İkisi bağımsız Türkiye saha
başarımı veya makale kabulü olarak sunulmaz. Yazar, kurum, katkı, fon ve
yayımlama kararları gerçek araştırmacılar tarafından kesinleştirilmelidir.

`docs/NIHAI_BILIMSEL_DENETIM.md` ve `docs/NIHAI_TEKNIK_DENETIM.md` kapsamı
açıklar. Mevcut `reports/final*.json`, `reports/final*.log` ve varsa
`reports/product_ui_verification.json` denetim kayıtları pakete eklenir.
Her kayıt, kendi tarihine ve kapsadığı sürüme göre okunmalıdır.

`PACKAGE_MANIFEST.json`, bu README dahil paketteki dosyaların boyut ve
SHA-256 değerlerini taşır. Yapay zekâ yardımı ve insan araştırmacı
sorumluluğu raporda belirtilmiştir.
