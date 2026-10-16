# Orman SSL Proje Rehberi

16 Ekim 2026 | Kısaltılmış çalışma kitabı


## Proje ve uydu ölçümleri


### Projenin çözdüğü soruyu kendi cümlenle anlat

Bir orman noktasının iki yıllık uydu ölçümlerini düşün: İlk yıl orman olan yer ikinci yıl kesilmiş mi, yoksa iki yıl bozulmamış orman mı kalmış? Orman SSL, bu iki durumu sınıflandıran araştırma ve yerel uygulamadır.

Model tek fotoğraf yerine aynı konumun 24 aylık, 10 ışık bandındaki sayılarını inceler. Sınıf, cevap kategorisidir: 0 bozulmamış orman, 1 kesim. Kesim skoru, sabit 0,50 eşikle sınıfa çevrilir.

Araştırma sorusu ile ürünün görevi

Ürün uydu dizisinden tahmin üretir. Araştırma ise şunu sorar: Az etiket varken etiketsiz dizilerle ön alıştırma öğrenmeyi iyileştirir mi? Modeller aynı veri ve coğrafi ayrımlarda karşılaştırıldı; daha uzun eğitimin etkisi ayrıca kontrol edildi.

Etiket, kaynak araştırmacıların verdiği referans cevaptır. Etiketsiz veri boş değildir; öğrenirken sınıf cevabı kullanılmaz. SSL bu ayrımla anlaşılır.

Hocaya ilk cümlen

“Gerçek Sentinel 2 zaman serilerinden orman kesimini geriye dönük sınıflandırdık. Az etiketli öğrenmede SSL kazancının eğitim bütçesi kontrol edildiğinde sürüp sürmediğini araştırdık.” İleride bu cümlenin gerekçelerini öğreneceksin.

Model gelecekteki orman yangınını haber verir mi?

Hayır. Seçilmiş iki yıllık penceredeki kesimi sonradan sınıflandırır. Yangın, gelecek tahmini ve erken uyarı doğrulanmadı.


### Uydu görüntüsünün içindeki sayılar

Uzaktan algılama, dokunmadan sensörle ölçmektir. Sentinel 2, yeryüzünden gelen ışığı farklı dalga boylarında ölçen uydu görevidir. Fotoğrafın kırmızı, yeşil, mavi kanalları gibi bantları vardır; bazıları gözün görmediği ışığı ölçer. Bilgisayar renkleri sayı olarak görür.

Piksel küçük bir alanın ölçümüdür; tek ağaç değildir, ağaç, toprak ve başka yüzeyler içerebilir. Sentinel 2’nin 13 bandı, banda göre 10, 20, 60 metre örnekleme ölçeği vardır. Biz seçilmiş 10 bandın hazır konum serisini kullanırız; doğal çözünürlükleri aynı değildir. [G1]

| Kullandığımız bantlar | Basit karşılığı |
| B02 B03 B04 | Mavi yeşil kırmızı görünür ışık |
| B05 B06 B07 | Bitki örtüsüne ilişkin değişimleri incelemekte yararlı kırmızı kenar bölgesi |
| B08 B8A | Yakın kızılötesi ışık |
| B11 B12 | Kısa dalga kızılötesi ışık |

Ağaç örtüsüyle birlikte ölçülen ışık değişebilir; bulut, gölge, mevsim, nem ve arazi de etkiler. Tek bandın düşmesi kesin kesim değildir. Model, bant ve ayların birlikte oluşturduğu örüntüleri öğrenmeye çalışır.

Uydu görüntüsü indirme, pikselleri yeniden örnekleme ve fiziksel yansıtım düzeltme zinciri kurmadık. DISFOR’un hazır konum ölçümlerini, kaynak DN sayısal değerleriyle kullandık; yeni yansıtım dönüşümü eklemedik.

B08 bir ayda düşerse neden kesin kesim diyemeyiz?

Birden fazla nedeni olabilir. Diğer bantlar, önceki ve sonraki aylar, gözlem kalitesi ve bağımsız referans birlikte incelenmelidir.


## Örneğin yapısı ve veri hazırlama


### Bir örneğin biçimi ve zaman penceresi

Zaman serisi, aynı yerin sıralı zaman ölçümleridir; bir kişinin iki yıllık aylık sağlık ölçümleri gibi. Tek ölçümden çok birlikte değişmeleri önemlidir. Her örnek bir konum, satır bir ay, sütun bir banttır.

| Öğe | Bu projedeki anlamı |
| Bir örnek | Bir konum için tek bir 24 aylık pencere |
| x | 24 ay × 10 bantlık sayısal dizi |
| observed | Her ay ve bant için ölçüm mevcut mu bilgisi |
| days | Her ayın 15. gününün pencere başından itibaren gün karşılığı |
| y | Eğitim ve değerlendirmede kullanılan sınıf etiketi |
| id | Örneği dosyalar arasında eşleştiren benzersiz kimlik |

target_year 2019, Ocak 2018–Aralık 2019 demektir. Kesim örneğinde ilk yıl bozulmamış orman, ikinci yıl uygun kesim aranır. Negatif örneğin iki yıl boyunca orman referansı vardır. Tüm aylar tamamlandıktan sonra geriye dönük incelenir.

Tüm x dizisi 2213 × 24 × 10 biçimindedir: 2.213 konum, her konumda 240 hücre; bazıları eksiktir. 2213 × 240 bağımsız örnek değildir: aynı konumun ayları ilişkilidir.

Uygun veri pencereleri etiketlerle kuruldu. Tahmin programı etiket istemez; ölçümleri ve incelenecek iki yılı alır. Araştırma verimizin seçilmiş ve etiketli olduğu unutulmamalıdır.

target_year 2020 hangi dönemi kapsar?

Ocak 2019–Aralık 2020. Kesim olayı ikinci takvim yılında aranır; 24 aylık pencere kesin olay gününü tahmin etmez.


### Veri nereden geldi ve neden bu kadar örnek kaldı

DISFOR, Avrupa orman bozulmalarına ilişkin açık veridir. Kaynak araştırmacılar mevcut bilgiler ve uydu görüntülerini yorumlayarak referans etiketler sağlamıştır. Yeni arazi ziyaretiyle etiket toplamadık; model tahminini doğru cevap sayıp eğitim verisi yapmadık. [G2]

Yeniden aynı veriye erişmek için kimlikle belirlenen sabit sürüm indirildi. İndirilen konum tablomuz 3.822 kayıttır; kaynak kartındaki farklı sayılar işlediğimiz örnek sayısı değildir.

| Sıralı seçim adımı | Konum sayısı |
| İndirilen konum tablosu | 3.822 |
| Yüksek güven dışında kalanlar | −598 |
| Uygun ve açık iki yıllık pencere olmayanlar | −606 |
| Yeterli açık ay gözlemi bulunmayanlar | −116 |
| İkili görev dışında bırakılan yangın örnekleri | −289 |
| Son çalışma kümesi | 2.213 |
| Orman ve kesim dağılımı | 1.937 orman ve 276 kesim |

Filtreler tutarlı bir ikili görev kurar; sonuç tüm bozulmaları ve coğrafyaları temsil etmez. Kolay yorumlanan, yeterince gözlenen noktaları seçmek gerçek dünyanın zor örneklerini eksik temsil edebilir.

Kesim azlığı sınıf dengesizliğidir. Sürekli “orman” diyen model, çoğunluk sayesinde yüksek doğruluk alırken hiçbir kesimi bulamaz. Bu yüzden sınıfları ayrı değerlendiren ölçütler gerekir.

2.213 noktanın tamamını sahada biz mi ölçtük?

Hayır. DISFOR etiket ve ölçümlerine seçim ve hazırlama uyguladık. Kaynağın etiket katkısını kendi veri işleme katkımızdan ayırmalısın.


### Ham gözlemden kullanılabilir aylık veriye

Aynı ayda birden fazla gözlem olabilir. Kaynağın clear alanı doğruysa ve SCL değeri 4 ya da 5 ise gözlem tutulur. SCL sahne sınıflandırmasıdır: 4 bitki örtüsü, 5 bitkisiz yüzey. Kesim yüzeyi değiştirebildiğinden 5 de tutulur. Filtre kusursuz bulut temizliği sağlamaz. [G3]

Her ay ve bant için medyan, yani sıralı sayıların ortanca değeri alınır. Örneğin 100, 110, 900 için 110’dur; aşırı değer ortalamayı daha fazla etkiler. Bunlar gerçek deney sayıları değil, öğretici örnektir.

Uygun ölçüm yoksa değer uydurulmaz; observed maskesi hangi hücrenin kullanılabildiğini doğru/yanlışla belirtir. Eksikliği sıfır saymak gerçekten sıfır ölçüldüğünü iddia eder. Aylık hazırlamada zamansal ara değer doldurulmaz.

Kalite koşulu her takvim yılında en az altı gözlenen aydır; kod, en az bir bandı gözlenen ayı sayar. Arayüzde tamamen yeşil ay, 10 bandın da gözlendiğini belirtir. Kalite uygunluğu tahmin doğruluğu değildir.

Ölçekleme neden yalnız eğitimden öğrenilir

Bantların ölçekleri farklı olabilir. Eğitimde gözlenen değerlerden ortalama ve standart sapma öğrenilir, değerler bunlarla ölçeklenir. Testin genel bilgisi öğrenmeye girmesin diye testten yeni ölçekleyici hesaplanmaz. Eksiklik maskesi model boyunca korunur.

Eksik ayda çizgi neden kesilir?

Ölçülmeyeni ölçülmüş göstermemek için. Boşluk veri kalitesi bilgisidir; tek başına kesim kanıtı değildir.


## Öğrenme tahmin ve gerçek örnekler


### Öğrenme tahmin ve ölçme üç ayrı iştir

Öğrenci örnek soru ve çözümlerle yaklaşımını düzeltir; sınavda yeni soruyu cevaplar; cevap anahtarıyla değerlendirilir. Makine öğrenmesindeki eğitim, çıkarım ve değerlendirme de ayrı adımlardır.

| İşlem | Ne kullanır | Ne değişir |
| Eğitim | Ölçümler ve yönteme göre sınıf etiketleri | Modelin öğrenilen sayıları |
| Çıkarım | Yeni veya mevcut ölçümler ve kayıtlı model | Tahmin dosyası |
| Değerlendirme | Tahminler ve referans etiketler | Başarı ve hata ölçümleri |

“Örnek veride analizi çalıştır” modeli eğitmez. Eğitimde öğrenilen sayısal parametreler, yani hazır ağırlıklarla aynı paketli ham gözlemler işlenip tahminler yenilenir. Tekrar basmak yeni deney veya bağımsız test yaratmaz.

Öğretici örnek: 0,50 eşikte 0,80 skor “kesim”, 0,30 “orman” olur. 0,80, yeni ülkede o tahminin kesinlikle yüzde 80 doğru olduğu anlamına gelmez; bu yorum hedef koşullarda ayrıca kalibrasyon ve doğrulama gerektirir.

Geçen 58 yazılım testi dosyaları, veri kontrollerini ve işlem akışını denetler. Hepsini geçen program yeni bölgede kötü tahmin yapabilir. Model başarımı, uygun ayrılmış veri ve referans etiketlerle ölçülür.

Düğme çalıştıysa Türkiye performansı kanıtlandı mı?

Hayır; mevcut veride çıkarım doğrulandı. Türkiye başarımı, geliştirmede kullanılmamış ve yeterli referansı olan Türkiye verisinde ölçülmelidir.


### İki gerçek örneği birlikte oku

Grafikler ürünün gerçek aylık girdisindendir: Solda doğru bulunan kesim, sağda referansı kesimken orman denilen nokta vardır. Çizgiler bantların zaman değişimidir; boş aylar birleştirilmez.

Şekil 1. advanced_v3’ten iki örneğin B04 B08 B12 gözlemleri; kaynak DN ölçeği korunur. Skorlar 10 bant ve tüm pencereyi kullanan modelindir.

Önce yatay eksendeki ayları, bant rengini ve dikey ölçüm birimini bul. Dikey kesik çizgi ikinci yılın başlangıcıdır, kesim günü değildir. Çizgi değişimini doğrudan olay tarihi sayma.

İkisi de referansta kesimdir; yüksek ve düşük skor, modelin yanılabildiğini gösterir. Açıklama için seçildiler; toplam başarım bütün değerlendirme kümesinden hesaplanır. Grafiğin üç bandı, kullanılan on bandın bir bölümüdür.

Düşük skorlu sağ örneğin etiketini orman yapabilir miyiz?

Hayır. Model–referans çelişkisi ayrı kanıtlarla incelenir; model kararı tek başına referans değiştirme gerekçesi değildir.


### Bütün sistemi tek akışta birleştir

Hazırlama, öğrenme ve kullanım ayrı girdisi, görevi, çıktısı olan adımlardır; tek dosya değildir. Ayrımı bilirsen “Bu sayı nereden?” sorusuna doğru kanıtı açarsın.

Şekil 2. Araştırma ve ürün aynı veri ailesinden gelir, farklı değerlendirme protokolleri kullanır.

Bilimsel yol yöntem karşılaştırır. paper_v4’te etiket alt kümeleri ve coğrafi katlar aynıdır. Her yöntemin dış test tahminleri birleştirilerek tablo oluşturulur; test sonucu o koşunun eğitimine geri beslenmez.

Ürün yolu eğitilmiş sistemi kullanıma sunar. advanced_v3’te beş CNN ve beş SSL Transformer birlikte çalışır. Arayüz birleşik tahmini, konumu ve zaman serisini gösterir. Ürünün 486 noktalık ve makalenin 2.213 konumluk skorları farklı düzenlerdendir.

Araştırmanın tamamlanması soruların bittiği anlamına gelmez. Yöntem karşılaştırması, kanıt dosyaları, çalışan ürün ve raporlama tamamlandı; dış saha doğrulaması sonraki çalışmadır. Rehber, mevcut sonucu ve yeni çalışmayı başlatacak kararı anlamanı sağlar.

Ürün F1’i ile makale tablosunu neden doğrudan yarıştırmıyoruz?

Veri bölünmeleri, eğitim tarifleri, tekil model ve ensemble yapıları farklıdır. Adil karşılaştırma aynı önceden tanımlanan değerlendirme düzenini gerektirir.


## Model aileleri ve özdenetimli öğrenme


### Bir model öğrenirken gerçekte ne değişir

Model, girdiyi çıktıya dönüştüren matematiksel kuraldır: burada bir konumun 24 aylık uydu gözleminden kesim skoru üretir. İnsan gibi düşünmez; eğitimdeki sayısal ilişkileri öğrenir. Aynı girdi, kayıtlı model ve işlem koşulları aynı tahmini vermelidir.

Sinir ağında ağırlık, bilginin sonraki hesaplamaya etkisini belirleyen öğrenilebilir sayıdır. Başta uygun ayarda olmayan ses masası düğmeleri gibi, eğitim örnekleriyle ayarlanır. Mimari bağlantı düzenini, eğitilmiş model bu düzenle son ayar değerlerini kapsar.

Kayıp (loss), eğitim hedefine uzaklıktır; gerçek kesime düşük skor verilince artar. Gradyan, küçük ağırlık değişimlerinin kaybı hangi yönde değiştireceğini gösteren türevdir. Optimizasyon bu bilgiyle ağırlıkları günceller; sinir ağlarımız AdamW kullanır. Düşük eğitim kaybı yeni konumlarda başarı garantilemez.

Batch bir güncellemede işlenen örnek grubudur; boyutu 64’tür. Epoch, o aşamanın bütün eğitim örneklerinden bir geçiştir. Açıklayıcı örnek: 128 etiketli örnek iki batch, 40 epoch ise 80 güncellemedir. Gerçek katlardaki sayılar farklıdır; batch ve epoch farklı birimlerdir.

Seed, rastgele sayı üretiminin başlangıcıdır; ağırlık başlangıçlarını ve örnek sıralamalarını izlenebilir kılar. paper_v4’te 7, 17, 27 aynı araştırmayı farklı rastgele seçimlerle tekrarlar; üç yeni veri kümesi değildir. Aynı seed, farklı donanım/yazılımda birebir eşitlik garantilemez.

Tahminde ağırlıklar değişmez: ürün düğmesi kayıtlı modeli çalıştırır, eğitmez. Random forest sinir ağı değildir; gradyanla öğrenmez.

Kırk epoch, kırk örnek midir?

Hayır; her epoch bütün eğitim örneklerinden geçer, örnekler tekrar görülür.


### Üç model ailesi aynı seriyi nasıl okur

Mimari, bilgiyi işleme düzenidir. Aynı 24 aylık seriyi inceleyen üç kişiden random forest özet fişini, CNN yakın ay örüntülerini, Transformer uzak ay ilişkilerini de okur. İsimlerinden hangisinin üstün olduğunu bilemeyiz.

Random forest (rastgele orman), sayısal koşullarla dallanan karar ağaçlarını birleştirir; ana modelde 500 ağaç vardır. Ham diziden, her bantta gözlenen değerlerin ortalaması, standart sapması (değişkenliği), en küçüğü, en büyüğü, ikinci yıl ortalaması eksi ilk yıl ortalaması ve gözlenen hücre oranı çıkarılır. On bant × altı özet = 60 özellik; özellik, kararın sayısal girdisidir.

Özetler hızlı ve güçlü olabilir; aynı ortalamalı farklı dizilerin ayrıntılı sırasını kaybedebilir. Yıllar arası fark zaman bilgisi taşıdığından model tamamen zamansız değildir. Uydu görüntü parçalarını sınıflandırmaz.

CNN (evrişimli sinir ağı), öğrenilebilir küçük süzgeçleri ay ekseninde kaydırarak bantlardaki yakın değişimleri birlikte işler. Genişliği 64, artık blok sayısı üçtür. Artık bağlantı, blok girdisini işlenmiş çıktıya ekleyerek bilgiyi taşır. Süzgeç aralıkları büyüdükçe uzak aylar da ilişkilendirilir.

Transformer’ın dikkat işlemi, bir ayı yorumlarken diğer ayların ağırlığını hesaplar; insan dikkati veya neden açıklaması değildir. Ağ iki katmanlı, dört dikkat başlıklı, 48 genişliklidir. CNN ve Transformer ay başına on değer, on gözlem göstergesi, üç zaman özelliği kullanır.

Aileleri aynı veri ve koşullarda ölçeriz. Tam etikette CNN’in ortalama macro-F1’i 0,9299’dur; bu görevdeki sonuç bütün uydu problemlerine üstünlük sağlamaz.

Random forest neden 240 ham değer yerine 60 özellik alır?

Her bandın 24 aylık dizisi altı özetle temsil edilir.


### Özdenetimli öğrenmede model neyi tahmin eder

Denetimli öğrenmenin hedefi sınıf etiketidir: kesim veya orman. Özdenetimli öğrenme (self supervised learning, SSL) hedefi veriden üretir: gözlenen uydu değerlerini gizleyip görünür bölümden tahmin eder. Böylece sınıf etiketlerini doğrudan kullanmadan temsil öğrenir.

Cümlede gizlenen kelimeleri çevrelerindeki ilişkilerle tamamlamak gibi, burada aylık bant değerleri tamamlanır. Yeniden oluşturma (reconstruction) gizlenen sayıları tahmindir. Temsil, öğrenilen iç sayısal gösterimdir; bunu kesim sınıflandırmasına uyarlayan ikinci aşama ince ayardır (fine tuning).

Kalite/gözlem maskesi, kaynaktan kullanılabilir ölçüm gelip gelmediğini bildirir. Bulutla kaybolanın doğrusu bilinmez; yeniden oluşturma hedefi olamaz. Eğitim maskesi ise bilinen değeri geçici saklar; tahmin doğrusu ile karşılaştırılır. Eksik gözlemi sıfır kabul etmek bu ayrımı bozar.

Ana SSL, her seride ardışık iki–altı aylık blok ve iki tam bant gizler. Kontrol, gözlenen her hücreyi yaklaşık üçte bir olasılıkla bağımsız gizler. Tam gözlenen tabloda ortalama gizleme ölçekleri benzerdir; gerçek eksikliklerle her örnekte aynı hücre sayısının gizlenmesi garanti edilmez. Kod hem görünür bilgi hem gizli hedef kalmasını denetler.

Ön eğitim yalnız ilgili katın eğitim konumlarında 60 epoch, etiketli ince ayar 40 epoch sürer. Son karar katmanı eşlenen denetimli modelle aynı başlangıca döndürülür. %20 etikette ön eğitim bütün dış eğitim gözlemlerini, sınıflandırma kaybı yalnız seçilmiş etiketli örnekleri kullanır. Dış test iki aşamaya da girmez.

Bulutla hiç ölçülmemiş hücre doğru cevap olabilir mi?

Hayır; hedefler başlangıçta gözlenip sonradan yapay gizlenen hücrelerdir.


## Adil deney ve coğrafi değerlendirme


### Eğitim doğrulama ve test neden ayrılır

Eğitim ağırlıkları öğrenir; doğrulama (validation) ayar seçtirir; test, önceden kararlaştırılmış yöntemi değerlendirir. Çalışma kitabı, deneme ve final sınavı gibidir. Final sorularını tekrar inceleyerek yöntem değiştirmek sürpriz sınavı bozar.

Veri sızıntısı, değerlendirme bilgisinin eğitime/seçime uygunsuz karışmasıdır. Aynı konumun eğitim/testte bulunması veya bütün veriyle ölçekleme örnektir. Standardizasyon, ortalamayı çıkarıp standart sapmaya bölmektir. Testi bu hesaba katmak dağılımından bilgi kullanır; projede yalnız dış eğitim ortalaması ve standart sapması kullanılır.

Farklı kimlikler bağımsızlık sağlamaz: aynı kesimin komşu noktaları, aynı sorunun varyasyonları gibidir. Rastgele nokta ayırma bu yakınlığı gizleyebilir; mekânsal gruplar birlikte tutulur. Kesim etiketi ve insan yorumlu olay tarihi model girdisi değildir. Etiket geçmişi uygun pencere seçiminde kullanılmıştır; görev geriye dönüktür.

advanced_v3: 1.266 eğitim, 461 geliştirme, 486 geçmiş test konumu. Eğitim içindeki coğrafi karşılaştırmalar model tariflerini; geliştirme örnekleri kalibrasyon ve eşiği seçmeye yardım etmiştir. Kalibrasyon, skorları gözlenen sınıf sıklıklarına yaklaştıran dönüşümdür; yeni bölgede aynı işleyiş varsayılamaz.

paper_v4: beş dış kat, sabit eğitim süreleri; doğrulama skoruyla erken durdurma/eşik seçimi yoktur. Tarifler önceden aynı veride geliştirildiğinden yeni katlar doğrudan karışmayı önlese bile geçmiş tasarım bilgisini silemez. Bu bağımsız dış saha doğrulaması değildir.

Ayrı test dosyası tüm sızıntıyı önler mi?

Hayır; yakın olaylar, bütün veriden ön işleme ve tekrarlanan test odaklı seçimler de incelenmelidir.


### Beş coğrafi kat ve az etiket düzeni

Kat, çapraz doğrulamada sırayla teste ayrılan bölümdür. Beş katın biri test, dördü eğitim olur; sonraki turda test bölümü değişir. Beş okul grubu gibi: aynı aileyi ayırmak bağımsızlığı zayıflatır. Burada aile benzeri bağlılık mekânsal bileşendir.

Beş kilometre içindeki veya uygun kaynak kampanyasında aynı bozulma olayını paylaşan konumlar bağlanır. Bağlı bileşen, doğrudan/dolaylı ulaşılabilen tüm konumlardır: A–B ve B–C yakınsa A–C uzak olsa da birlikte kalabilir. Böylece aynı çevrenin katlara parçalanması sınırlanır.

2.213 konum, parçalanmadan beş kata dağıtılan 874 bileşendir; sınıflar olabildiğince dengelenir. İlk kat testinde 385 orman, 54 kesim vardır. Katlar arasındaki en yakın eğitim–test çifti 5,0011 km’dir: mesafe kuralını doğrular, ekolojik benzerliğin bittiğini değil.

Etiket bütçesi, sınıflandırmada kullanılan eğitim sınıf bilgisinin payıdır. %20’de her sınıf ayrı rastgele sıralanır; sayının %20’si yukarı yuvarlanır. İlk kattaki 1.552 orman ve 222 kesimden 311 orman + 45 kesim = 356 etiket seçilir. %100 bütün eğitim etiketlerini kullanır.

İç içe altküme, küçüğün büyükle aynı sıralamanın başından seçilmesidir. Eşlenmiş altkümede bütün yöntemler aynı kat/seed/bütçede aynı konum etiketlerini kullanır; yöntem farkına etiket seçimi karışmaz. Seed 7, 17, 27 seçim/başlangıç değişkenliğini gösterir. Sınıfa göre seçim nedeniyle %20 etiket, gerçek anotasyon maliyetinde %80 tasarruf kanıtlamaz.

Farklı kimlikler farklı katlara konabilir mi?

Her zaman değil; aynı mekânsal bileşendekiler birlikte tutulur.


### Yüz seksen eğitim kaydından sonuç tablosuna

Koşu, belirli yöntem × kat × seed × etiket bütçesinde model kurulumudur. Çarpım tablosu gibi, başka başlangıç veya test katı yeni koşudur; yeni veri kümesi değildir. Koşu ve bağımsız konum sayısı farklıdır.

Ana tasarım: 5 kat × 3 seed × 2 bütçe × 4 yöntem = 120 koşu. Yalnız %20’de dört kontrol: bağımsız hücre maskeli SSL, adım eşlenmiş Transformer, yalnız gözlem maskeli random forest, yalnız konum/yıl/kampanya bilgili random forest. Ek 5 × 3 × 1 × 4 = 60; toplam 180.

SSL’nin 60 epoch ön eğitimi ve 40 epoch sınıflandırması tek koşunun iki aşamasıdır. Random forest bir koşudur, epoch ile eğitilmez. Dosyalar yöntem/örnek kimlikleri, eğitim geçmişi ve test olasılıklarını saklar; güçsüz koşular da korunur.

OOF (out of fold), örneğin bulunduğu kat eğitim dışında bırakıldığında üretilen tahmindir. Bir seed/yöntemin beş test bölümü birleştirilince 2.213 konumun her birine bir tahmin düşer. Pooled bu birleştirmedir. Macro-F1 birleşik tahminlerden hesaplanır; beş kat F1’inin basit ortalaması değildir.

Üç seed’in ayrı macro-F1’leri ortalama ± standart sapma ile özetlenir. Sapma üç değerin ayrılığını gösterir, güven aralığı değildir. Aynı konumlar/örtüşen eğitimler tekrarlandığından 5 kat × 3 seed, on beş bağımsız başarı gözlemi sayılmaz.

Sekiz ana yöntem/bütçe + dört kontrol = on iki birleşim. Her biri üç kez 2.213 tahmin üretir: 12 × 3 × 2.213 = 79.668 olasılık. Veri yine aynı 2.213 konumdur.

SSL ön eğitim ve ince ayarı kaç koşudur?

Bir koşu: aynı tarifin tek kat/seed/bütçede iki aşaması.


## Başarı hesabı ve deney sonuçları


### Karışıklık matrisinden başarıyı hesaplamak

Karışıklık matrisi, yoklama çizelgesi gibi doğru/yanlış kararları sayar. Bu advanced_v3’ün önceden incelenmiş 486 konumudur; paper_v4 ortalamaları değildir. Satır gerçek sınıf, sütun model kararıdır.

| Gerçek sınıf | Orman tahmini | Kesim tahmini |
| Orman | 448 | 0 |
| Kesim | 10 | 28 |

Pozitif sınıf kesimdir; “iyi sonuç” demek değildir. TP doğru pozitif: kesime kesim = 28. FP yanlış pozitif: ormana kesim = 0. FN yanlış negatif: kaçırılan kesim = 10. TN doğru negatif: ormana orman = 448.

Precision (kesinlik), kesim kararlarının doğruluk payıdır: TP / (TP + FP) = 28 / 28 = 1. Recall (duyarlılık), bulunan gerçek kesim payıdır: TP / (TP + FN) = 28 / 38 = 0,7368. Bütün kesim kararları doğru olsa da kesimler kaçabilir.

F1, kesinlik/duyarlılığın dengeli olmasını isteyen harmonik ortalamadır. Kesim F1 = 2TP / (2TP + FP + FN) = 56 / 66 = 0,8485. Ormanı hedef sınıf yapınca F1 = 896 / 906 = 0,9890.

Macro-F1 sınıfların F1 değerlerini eşit ağırlıkla ortalar: (56/66 + 896/906) / 2 ≈ 0,9187. Accuracy (doğruluk), tüm doğru kararların payıdır: (448 + 28) / 486 = 0,9794. Orman çoğunluğu doğruluğu yüksek tutabilir. Bu 448 ormanda sıfır yanlış alarm, yeni bölgede garanti değildir.

Kesinlik birse bütün kesimler bulunmuş mudur?

Hayır; on kesim kaçmıştır, duyarlılık 28/38’dir.


### Skorlar ve belirsizlik hangi soruyu yanıtlar

Karar, skorun eşikle karşılaştırılmasıdır; paper_v4’te tüm eşikler 0,5’tir. Tek karar bazı bilgileri kaybettirir. AP (average precision), gerçek kesimleri kuyruğun önüne koyar gibi skor sıralamasını kesinlik/duyarlılıkla özetler: duyarlılık artışları ilgili kesinlikle ağırlıklandırılır. Yamuklarla hesaplanan genel eğri alanıyla aynı tanım değildir.

ROC-AUC, eşiklere göre doğru pozitif/yanlış pozitif oranlarını ilişkilendiren ROC eğrisinin alanıdır. Yanlış pozitif oranı, gerçek ormanlarda kesim denenlerin payıdır. Yüksek ROC-AUC genellikle iyi sıralamadır; nadir kesimlerde yanlış alarmın kullanıcı etkisini tek başına anlatmaz. AP sınıf oranından etkilenir: burada 276/2.213 = %12,47 kesim vardır; farklı bölge oranları eşit koşul değildir.

Brier, kesim olasılığı ile gerçek 0/1 etiketin kare farklarının ortalamasıdır; düşüğü iyidir. Gerçek kesime 0,8: (0,8 − 1)² = 0,04; 0,2: 0,64 hata. Olasılık doğruluğu ve sınıfları ayırma gücünden etkilenir; kusursuz kalibrasyon kanıtlamaz.

Bootstrap, yeniden örneklemeyle değişkenliği inceler. Torbaya noktalar değil 874 mekânsal bileşen konur; yerine geri koyarak 874’ü çekilir. Bazıları tekrarlanır, bazıları dışarıda kalır. Aynı çekiliş iki modele uygulanır, üç seed beraber tutulur: eşlenmiş karşılaştırma aynı coğrafi örneklerdedir.

2.000 çekilişin her birinde seed başına macro-F1 hesaplanır; üç F1 ortalanır, yöntem ortalamaları çıkarılır. Sıralı farkların %2,5–%97,5 sınırları raporlanır. Ana SSL farkının aralığı [0,0245; 0,0506]’dır. Mevcut veri/katlar/eğitilmiş tahminlere koşulludur: yeniden eğitim yapılmaz; geçmiş geliştirme ve yeni bölge belirsizliği içerilmez.

Neden noktalar bağımsız çekilmez?

Aynı olayın yakın noktaları bağımlıdır; bileşenleri birlikte çekmek bağlılığı korur.


### Gerçek deney tablosunu yorumlamak

Tablo paper_v4’ün tüm yöntem/bütçelerini gösterir. RF = random forest. Macro-F1, üç seed ortalaması ± standart sapmadır; yüzde doğruluk/güven aralığı değildir. AP sıralamayı, duyarlılık bulunan kesim payını anlatır.

| Etiket | Yöntem | Macro F1 ± SD | AP | Duyarlılık |
| %20 | RF | 0,8452 ± 0,0058 | 0,7969 | 0,7295 |
| %20 | CNN | 0,8721 ± 0,0081 | 0,8494 | 0,7983 |
| %20 | Transformer | 0,8322 ± 0,0236 | 0,8419 | 0,7995 |
| %20 | SSL | 0,8690 ± 0,0043 | 0,8636 | 0,8007 |
| %100 | RF | 0,8669 ± 0,0028 | 0,8382 | 0,7101 |
| %100 | CNN | 0,9299 ± 0,0071 | 0,9273 | 0,8853 |
| %100 | Transformer | 0,9285 ± 0,0057 | 0,9227 | 0,8720 |
| %100 | SSL | 0,9287 ± 0,0049 | 0,9337 | 0,8756 |
| %20 | Hücre SSL | 0,8609 ± 0,0098 | 0,8604 | 0,8068 |
| %20 | Uzun Transformer | 0,8987 ± 0,0112 | 0,8445 | 0,7971 |
| %20 | Maske kontrolü | 0,5515 ± 0,0129 | 0,1738 | 0,2826 |
| %20 | Konum kontrolü | 0,6455 ± 0,0300 | 0,3979 | 0,3949 |

%20’de SSL − kısa Transformer = 0,0368; koşullu %95 aralık [0,0245; 0,0506] sıfırı içermez. SSL − uzun Transformer = −0,0297; aralık [−0,0430; −0,0179]. SSL − hücre maskesi aralığı [−0,0013; 0,0178] üstünlüğü netleştirmez. Ana karşılaştırma kısadır; diğerleri keşifseldir, çoklu karşılaştırma düzeltmesi yoktur.

Bu, farklı süre çalışan iki öğrencinin karşılaştırma sonucunun değişmesine benzer. Uzun denetimli modelin macro-F1’i SSL’den, SSL’nin AP’si uzun modelden yüksektir. Tam etikette sinir ağları yakındır. Olumsuz bulgu başarısız araştırma değildir; üstünlük yorumunu değiştiren kontrolü gösterir.

SSL her zaman daha iyi midir?

Hayır; uzun denetimli kontrol %20’de daha yüksek macro-F1 vermiştir.


## Sınırlar sürümler ve dosya haritası


### Sınırlamaları bilmek araştırmayı nasıl güçlendirir

Karşılaştırıcı (baseline), yeni tarifi anlamak için yanında ölçülen yöntemdir. Ablasyon/bileşen kontrolü bir parçayı değiştirip etkisini inceler; yemeğin malzemesini veya pişirme süresini değiştirmek gibi. Birçok şeyi birlikte değiştirirsen farkı tek nedene bağlayamazsın.

Uzun Transformer 320 epoch ile SSL ön eğitim + ince ayarının yaklaşık optimizer adımı (ağırlık güncellemesi) sayısına ulaşır. İşlem yükü (FLOP), süre, öğrenme oranı ve etiketli örneklere tekrar maruz kalma eşitlenmez. Ek eğitimin tek mekanizma olduğunu kanıtlamaz; mekanizma, etkiyi oluşturan neden zincirinin açıklamasıdır.

Yalnız gözlem maskesi: 0,5515; yalnız konum/yıl/kampanya: 0,6455 macro-F1. Örnekleme bağlamı tahmin bilgisi taşır; spektral başarının hangi yüzdesini açıkladığı söylenemez. Beş kilometre yakınlığı sınırlar, geniş coğrafi örüntü/kampanya farklarını yok etmez.

Tam etiketli CNN veya SSL’nin üç seed’inden en az ikisinde yanıldığı 81 konum, insan incelemesi adayıdır. Modelin etikete katılmaması etiket hatasını kanıtlamaz; modele uydurarak değiştirmek sonraki değerlendirmeyi yanlılaştırabilir. Kaynak etiketleri değiştirilmemiştir.

Kullanılmamış konum denetiminde 111 uygun pencereden yalnız biri kesimdir; güvenilir kesim başarımı çıkarılamadığından skor verilmez. Aynı kaynaktaki kullanılmamış noktalar bağımsız saha toplaması değildir. Türkiye başarımı, yangın/hastalık tanısı ve erken uyarı doğrulanmamıştır.

Katkı yeni mimariden çok, güçlü kontrollerin yorumu değiştirmesini göstermektir. SOTA, mevcut yöntemlerin en iyisi iddiasıdır; kapsamlı uygun karşılaştırma ister. Burada iddia edilmez. Sonraki güçlü adım, skorları görmeden tasarlanan, yeterli bağımsız kesim olaylı yeni değerlendirmedir.

81 hata adayı neden düzeltilmiş veri değildir?

Model yanılabilir; her aday gözlemler ve bağımsız uzman değerlendirmesiyle incelenmelidir.


### Araştırma sürümü ile ürün sürümünü ayırmak

Araştırma aynı veride yöntemleri karşılaştırıp hangi koşulda hangi sonucun çıktığını ölçer; ürün eğitimli modeli kolay açılan arayüze bağlar. İlki bilimsel soruyu inceler; ikincisi örnekleri gösterip yeniden tahmin üretir. Birlikte sunulabilir, fakat sonuç sayıları ayrıdır.

| Sürüm | Ne için var | Hangi sonuçla konuşulur |
| paper_v4 | Bilimsel karşılaştırma ve kontrol deneyleri | 2.213 konum üzerinde beş coğrafi kat ve üç seed |
| advanced_v3 | Uygulamada çalışan kayıtlı model | Daha önce incelenmiş 486 örnekte ayrı değerlendirme |
| Ürün arayüzü 1.1 | Nokta seçme ve NPZ yükleyip modeli çalıştırma | Tahmin, gözlem kalitesi, spektral seri ve indirme |

paper_v4 içindeki 180 eğitim koşusu; yöntem, coğrafi kat, rastgele başlangıç ve etiket miktarı birleşimleridir, 180 ayrı icat değildir. advanced_v3, beş SSL Transformer ve beş CNN’den oluşan on eğitimli modelin sonuçlarını birleştirir. Ekrandaki düğme kayıtlı modellerle tahmin üretir; eğitim başlatmaz.

Tamamlanmış olanı nasıl anlatırsın

Gerçek veri hazırlama, eğitim kayıtları, karşılaştırmalar, çıkarım modeli, yerel arayüz, Türkçe rapor ve İngilizce makale hazır. Makale dosyası dergi kabulünü; çalışan ürün Türkiye’de bağımsız saha başarısını kanıtlamaz. Saha doğrulaması geliştirme kararlarında kullanılmamış uygun değerlendirme verisi gerektirir.

Ekranda “advanced_v3 modelini çalıştırıyorum”, tabloda “paper_v4 karşılaştırmalarına geçiyorum” de; böylece deneyleri ayırırsın. Kesim skoru tek örneğindir; makaledeki macro-F1 birçok örneğin tahminlerinden hesaplanan toplu ölçüttür.

Analizi yeniden çalıştırınca 180 deney de yeniden eğitilir mi?

Hayır. Ham örnek gözlemler işlenir, kayıtlı advanced_v3 ağırlıkları tahmin üretir. paper_v4 eğitimleri ayrı deney dosyaları ve eğitim komutundadır.


### Gerekli dosyaları bulmak ve kanıta ulaşmak

Klasörleri ezberleme; açacağın dosyayı ve kanıtını öğren. Yollar proje ana klasöründen başlar: output/final, output içindeki final klasörüdür. .pdf/.json uzantıları içerik türüdür.

| İhtiyacın | Açılacak yer |
| Canlı ürünü açmak | URUNU_AC.command |
| Türkçe sonuç raporunu okumak | output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf |
| İngilizce makaleyi okumak | output/pdf/Orman_SSL_Manuscript.pdf |
| Araştırmayı tarayıcıda incelemek | reports/paper_v4.html |
| Bir iddianın kaynağını bulmak | paper/CLAIM_LEDGER.md |
| Ürün modelinin kapsamını öğrenmek | models/advanced_v3/model_card.json |
| Son denetimin neyi kontrol ettiğini görmek | reports/final_delivery_verification.json |

İlk görüşmenin ana belgesi Türkçe rapordur. PDF sabit görünümle okumak/paylaşmak; aynı klasördeki aynı adlı .docx düzenlemek içindir. İngilizce makale daha resmî bilimsel anlatımdır; amaçları farklı olduğundan raporla başlıklarının aynı olması gerekmez.

Bir sayı sorulduğunda izleyeceğin yol

“SSL sayısı nereden geliyor?” sorusunda paper/CLAIM_LEDGER.md içindeki iddiaya bak. Toplu sayılar experiments/paper_v4/analysis.json, tek deneyler experiments/paper_v4/runs içindedir. Ürünün 486 örneklik sonucu models/advanced_v3/model_card.json dosyasındadır; araştırma ortalamasıyla karıştırma.

Klasörün varlığı tamamlanma kanıtı değildir. Kontrol kaydında status, incelenen dosyalar ve tarihi birlikte oku. “passed”, belirtilen teknik kontrollerin geçtiğini söyler; bilimsel yenilik veya dış saha doğruluğunu garantilemez. Sunumda ana raporu açık tut; ham veriye dalma, kanıta yalnız sorulan noktayı göstermek için geç.

Hoca yalnız okumak istiyorsa önce neyi açarsın?

Türkçe araştırma ve ürün raporunun PDF’sini. JSON kayıtları ayrıntılı kanıttır; ilk açıklamanın yerini tutmaz.


## Ürünü açma ve canlı gösterim


### Mac bilgisayarda ürünü açmak

Bu bilgisayardaki proje ortamı hazırdır. Finder’da NidaHocaylaPaper içindeki URUNU_AC.command dosyasına çift tıkla. Terminal, ardından tarayıcı ürün adresinde açılır. Uygulama Terminal’de çalışır; görüşmede açık tut. Tarayıcı kullanımı internete veri gönderildiğini göstermez; uygulama aynı bilgisayardadır.

Tarayıcı açılmazsa Terminal’deki adresi adres çubuğuna yapıştır: varsayılan http://127.0.0.1:8765. 127.0.0.1 kendi bilgisayarın, 8765 bağlantı numarasıdır. Projeyi internette aramak yerine adresi kullan. Açılıştaki 486 kayıt başlangıç verisinin yüklendiğini gösterir.

Başka bir bilgisayara taşırsan

Tam proje ZIP’i kodu, veriyi ve modelleri içerir; bilgisayara özgü .venv ortamını içermez. Yeni bilgisayarda Python 3.11 gerekir; ilk kurulumdaki bağımlılık indirmeleri internet gerektirebilir. Terminal’de proje klasöründeyken aşağıdaki komutla ortamı hazırla; ardından URUNU_AC.command ile aç. PDF okumak kurulum gerektirmez.

```
bash scripts/setup.sh
```

Çift tıklama izin hatası verirse

Çalıştırma izni eksikse Terminal’i aç; cd ve boşluk yaz, proje klasörünü Finder’dan Terminal’e sürükle, Enter’a bas. Doğru klasörde aşağıdaki komutu çalıştır. ZIP’in içini değil, dışarı çıkarılmış proje klasörünü kullan.

```
bash URUNU_AC.command
```

“Orman-SSL ortamı bulunamadı” kurulum gerektiğini söyler; çift tıklama sorunu değildir. “Address already in use”, bağlantı numarasının kullanımda olduğunu belirtir. Kendi açtığın eski ürün Terminal’ini Ctrl+C ile durdurup yeniden aç. Terminal kapanınca tarayıcıda kalan sayfa yeni analiz yapamaz; sunucuyu yeniden başlat.

Çalışırken Terminal’i kapatabilir misin?

Sunum boyunca açık tut: arayüz Terminal’deki yerel sunucuyla konuşur. İşin bitince Ctrl+C ile durdur.


### Beş dakikada gerçek bir gösterim yapmak

Bütün düğmelere basmak yerine gözlemden tahmine geçişi anlat. Dosyalardan doğrulanmış aşağıdaki iki kimlik aynı geçmiş değerlendirme kümesindendir. Referansları kaynak görüntü yorumlarıdır; yeni saha ziyareti yapıldığını söyleme.

- İlk dakika: “Örnekleri keşfet”te 486 kayıt ve 28 kesim tahminini göster; “Tüm tahminler” ve “Tüm yıllar” seçili olsun. “Mekânsal görünüm” gerçek koordinatları gösterir; altlık harita veya kesintisiz orman sınırı içermez.

- İkinci dakika: “Örnek kimliği ara…” alanına disfor-1733-2019 yazıp listedeki örneğe tıkla. “Kesim tahmini” ve 0,9981 skor görünür; referans etiketi de kesimdir. Dönem Ocak 2018–Aralık 2019; iki yılda da 10 gözlenen ay.

- Üçüncü dakika: “24 aylık spektral iz”de B04, B08, B12’yi göster: “10 model bandının üçünü görüyoruz.” Boş aylar bağlanmaz, değerler kaynak DN’dir. Grafik olayın nedenini tek başına kanıtlamaz.

- Dördüncü dakika: “Geçmiş değerlendirme”yi aç; “Yanlış sınıflandırılan örnekler”de disfor-1664-2018’e tıkla. Filtreler sıfırlanır, örnek açılır. Referans kesimken model orman demiştir; kesim skoru 0,0176. Dönem 2017–2018; iki yılda da dokuz gözlenen ay.

- Beşinci dakika: “Örnek veride analizi çalıştır”a bas. “Analiz çalışıyor…” bitince yeniden üretim durumunu göster. “Tüm sonuçları indir”den JSON veya GeoJSON seç. Ham gözlemler yeniden işlenir; model yeniden eğitilmez.

Aramada açık filtre örneği gizleyebilir; görünmezse filtreleri sıfırla. İndirme, süzülen noktayı değil aktif analizin tüm sonuçlarını verir. “Yüzde 99 kesin kesim” yerine “modelin kalibre edilmiş kesim skoru 0,9981” de. Kaçırılan örnek de kalite koşulunu karşılar: yeterli gözlem doğru tahmini garantilemez.

Kaçırılan örneği göstermek sunumu zayıflatır mı?

Hayır; hatayı ve sınırları bildiğini gösterir. Buradan dış doğrulamanın gerekliliğini açıklayabilirsin.


### Veri ve model dosyalarının dilini okumak

Uzantı dosya türünü anlatır: okunabilir metin veya büyük sayısal diziler. Hepsini Word’de açma; veri, model, sonuç ve açıklamayı ayır.

| Tür | Bu projedeki anlamı |
| JSON | Anahtar ve değerlerle yazılmış okunabilir kayıt; örneğin predictions ve classes. |
| GeoJSON | JSON biçiminde coğrafi kayıt; geometry konumu, properties açıklayıcı alanları taşır. |
| NPZ | NumPy sayısal dizi arşivi; x, observed, days ve ids gibi alanları saklar. |
| PT | PyTorch model dosyası; öğrenilmiş ağırlıkları ve ilgili model bilgilerini taşır. |
| Parquet | Ham gözlemler gibi büyük tabloları saklamak için kullanılan dosya biçimi. |
| model_card.json | Modelin görevi, veri kapsamı, değerlendirmesi ve kullanım sınırları. |
| manifest.json | Hangi girdinin ve modelin kullanıldığını gösteren kaynak ve bütünlük kaydı. |

predictions.json içinde ids kimlikleri, predictions sayısal sınıf kararları, probabilities iki sınıfın skorlarıdır. classes sırası undisturbed_forest, clear_cut olduğundan 0 orman, 1 kesimdir. Kimlik, karar ve skoru aynı liste konumunda eşleştir; kaydırırsan yanlış örneğe bağlarsın.

```
"classes": ["undisturbed_forest", "clear_cut"]
"threshold": 0.5
"quality_eligible": [true, true]
```

Bu kesit mevcut dosyadaki alanları gösterir; tam JSON değildir. threshold karar eşiğidir. quality_eligible=true aylık gözlem koşulunun karşılandığını söyler; tahminin doğruluğunu söylemez. GeoJSON coordinates sırası boylam, enlemdir; ters çevirmek konumu bozar.

Yeni girdide docs/VERI_SOZLESMESI.md esas alınır. x: N örnek × 24 ay × 10 bant; observed: gözlenen hücreler; days: zaman; metadata: bant sırası ve birim. Eğitim etiketi y çıkarımda gerekmez. DN yerine rastgele 0–1 yansıtım koymak, aynı dosya adına rağmen sözleşmeyi değiştirir.

PT’yi değiştirerek tahmini elle düzeltebilir misin?

Hayır; model dosyası sonuç tablosu değildir. Tahmin JSON’da incelenir; model değişikliği ayrı eğitim, sürüm ve değerlendirme gerektirir.


## Eğitim kaydı paketler ve çalışma programı


### Bir eğitim kaydını deney defteri gibi okumak

Gerçek eğitimi yalnız başarı sayısı kanıtlamaz: ayarlar, günlük ve eğitim dışı tahminler birlikte okunur. Dosyada f0 coğrafi kat 0, s7 rastgele başlangıç seed 7, b0.2 yaklaşık yüzde 20 etiket bütçesidir.

```
experiments/paper_v4/runs/ssl_transformer48_f0_s7_b0.2.json
```

| Dosyadaki alan | Bu koşuda okuduğun bilgi |
| method | ssl_transformer48 adlı SSL Transformer yöntemi |
| n_train ve n_labeled | 1.774 eğitim örneği; 356 etiketli örnek |
| epochs | 40 denetimli eğitim turu |
| train_ids ve test_ids | Eğitim kimlikleri ve ayrı tutulan 439 test kimliği |
| log.history | Tur numarası ile eğitim kaybının kaydı |
| y ve probabilities | Referans etiketler ile ayrı tutulan örneklerin kesim skorları |

Ayarlardan sonra log.history’ye bak: ilk tur loss ≈0,7594, kırkıncı tur 0,2119. Loss eğitim amacı bakımından hatayı özetler. Düşmesi eğitim verisine uyumun geliştiğini gösterir; saha başarısının aynı oranda arttığını göstermez. log.pretrain_loss ayrı SSL ön eğitimin kayıplarıdır; amaçları farklı olduğundan iki aşamanın kaybını aynı ölçek gibi karşılaştırma.

Sonra kimlik ayrımını kontrol et: bu kayıtta train_ids ve test_ids kesişmez; probabilities ayrı tutulan örneklerin skorlarıdır. Coğrafi kat tahminleri birleşince her örneğin kendisini görmeyen kat modelinden aldığı OOF tahminleri oluşur. experiments/paper_v4/oof_predictions.npz içindeki ssl_transformer48_0.2, üç seed için 3 × 2.213 değer taşır.

Hash dijital parmak izidir: SHA-256 eşitliği aynı baytları gösterir, bilimsel doğruluğu değil. signature.json kod/veri/protokol imzalarını; verification.json 180 koşu, ayrım ve OOF’nin yeniden kurulması kontrollerini saklar. Günlük tek başına yetmez; bağlantılı kayıtları ve tekrar üretimi birlikte değerlendir.

Kontrol edilen OOF’nin SHA-256 değeri aşağıdadır. Kopyayı karşılaştırırken bütün karakterler eşleşmelidir.

```
0df39e930d829cddd9c60d6d56efffb4e6cd0d0349c98778d72213e5a43ee14b
```

Loss azalınca “Model dış sahada doğrulandı” diyebilir misin?

Hayır. Kayıp öğrenme sürecini anlatır; dış doğrulama, geliştirmede kullanılmamış uygun veride ayrı ölçüm gerektirir.


### Sorun çıkarsa gösterimi sürdürmek ve doğru paketi paylaşmak

Görüşmeden önce Türkçe PDF’yi ve reports/paper_v4.html dosyasını açıp kontrol et. Araştırma HTML’i hazır sonuçları çevrimdışı gösterir. Canlı reports/product.html sunucu gerektirir; çift tıklamak aynı işlevi sağlamaz. Bunları ayırmak zaman kaybını önler; canlı gösterim tek anlatım yolun değildir.

Bir hata olduğunda sırayla düşün

- Sayfa açılmazsa ürün Terminal’ini ve adresi kontrol et; kapatıp açmadan önce mesajı oku.

- Analiz başarısızsa önceki kayıtlı sonuçları göster; yeni denemenin tamamlanmadığını söyle. Günlük: output/product_demo/inference.log.

- Kurulum/güvenlik engeli hemen çözülmezse Türkçe PDF ve çevrimdışı araştırma özetine geç; hazır sonuçla o anda yapılan çıkarımı ayır.

| ZIP paketi | Hangi ihtiyaç için |
| Orman_SSL_Hocaya_Sunum.zip | Rapor, makale ve görüşme belgelerini okuyup değerlendirmek. |
| Orman_SSL_Proje_Paketi.zip | Canlı ürünü, ham veriyi, modelleri ve bütün proje kodunu taşımak. |
| Orman_SSL_Paper_Paketi.zip | İşlenmiş veri ve 180 koşu kaydıyla bilimsel deneyi tekrar üretmek. |
| Orman_SSL_Nihai_Model.zip | Hazır etiketsiz NPZ girdisinde advanced_v3 çıkarımı yapmak. |

Dört ZIP output içindedir. Paper komutu tamamlanmış kayıtları önbellekten kullanır; sıfırdan eğitim için ayrı kopyada paper/SUPPLEMENT.md’yi izle. Sunum paketi okumak içindir; ham gözlem/ürün ağırlığı içermez. Paper bilimsel karşılaştırma paketidir, canlı ürün için değildir. Nihai model hazır girdiden tahmin üretir; ham gözlem hazırlama ve tam eğitim tam proje paketindedir. Her ZIP’in README’si kapsamını açıklar.

Önce Türkçe sonuç PDF’si ve Hocaya_Sunum paketini paylaşım için seç; İngilizce makale pakettedir. Ürünü çalıştırmak isteyen hocaya Proje_Paketi ve ürün kılavuzunu seç. Dosyalar yerelde hazırdır, otomatik gönderilmemiştir. Aynı adlı eski indirme kopyasını değil son sürümü kullan.

Sunum ZIP’i canlı modeli açmıyorsa ilk kontrolün?

Paket kapsamı. Sunum arşivi okumak içindir; canlı ürün tam proje paketi, uygun Python ortamı ve kurulum gerektirir.


### Yedi günde anlayarak öğrenme

Yedi gün boyunca günde yaklaşık 45 dakika çalış. Bu öneri uzmanlık veya hoca onayı vaat etmez. Hedef, ezberlemek değil dosyayı kapatınca yapılanı ve nedenini kendi sözlerinle açıklamak; açıklayamıyorsan geri dön.

Her gün aynı öğrenme döngüsünü uygula

10 dakika oku, 15 dakika örnek çöz, 10 dakika kaynağı kapatıp anlat, 10 dakika kanıtla karşılaştır. Kapalı anlatım aktif hatırlama, karşılaştırma geri bildirimdir. Yanlışlarını listele; ertesi gün önce onları çalış.

- 1. gün: Problemi öğren. Bir konumun iki yılını çiz; girdi, tahmin ve gerçek etiketi ayrı kutulara koy. Hangi yıl sınıflandırılıyor?

- 2. gün: Veride gözlenen ve eksik ayları göster. Eksik ölçümün sıfır yansıtım olmadığını günlük yaşamdan örnekle açıkla.

- 3. gün: Etiketli öğrenme, maskeli ön eğitim ve çıkarımı birer cümleyle tanımla; kullandıkları verileri yaz.

- 4. gün: Ürünün matrisinden bulunan ve kaçırılan kesimleri hesapla. Yüksek doğruluk neden tüm kesimlerin bulunduğunu göstermez?

- 5. gün: Kısa Transformer, SSL ve uzun Transformer sonuçlarını yan yana yaz; eğitim bütçesi kontrolünün yorumu nasıl değiştirdiğini sesli anlat.

- 6. gün: Üründe bir doğru tahmin ve bir hatayı incele; gerçek çıkarımı çalıştır. Sonuç gösterme ile yeniden eğitimi ayır.

- 7. gün: Sınavı kaynaksız çöz, yanıtları kontrol et. Zorlandığın iki konuyu tekrarla ve görüşme provası yap.

Her gün çizim, hesap, açıklama veya çalışan işlem üret; yalnız okunan sayfayı başarı sayma. Başkasına öğretirken eksiklerini fark etmen, anlamadığın terimleri düzgün söylemenden değerlidir.


## Hocaya anlatım ve ilk beş soru


### Üç uzunlukta dürüst anlatım

Metinleri kendi anladığın kelimelerle kur; yapmadığın işi sahiplenme. Süreler prova içindir: 2 dakikalık açıklama tablodaki duraklamaları, 7 dakikalık anlatım şekil ve ürün gösterimini içerir; metni okumak tek başına 7 dakika sürmez.

Otuz saniyelik giriş

Hocam, yapay zekâ desteğiyle hazırlanan projede gerçek uydu gözlemlerinden orman kesimi sınıflandırılıyor. Çalışan model, karşılaştırmalı deneyler ve makale taslağı var. Az etikette SSL kısa eğitime göre yararlı görünüyor; uzun denetimli eğitim daha iyi macro-F1 veriyor. Bağımsız Türkiye doğrulaması henüz yok.

İki dakikalık açıklama

Bir konumun iki yıllık, 24 aylık Sentinel-2 gözlemleriyle ikinci yıldaki kesimi geriye dönük sınıflandırıyoruz. Araştırmada 2.213 konum, 5 coğrafi kat, 3 seed ve 180 eğitim kaydı var. Yakın noktalar ve ortak olaylar aynı grupta tutuluyor.

Yüzde 20 etikette macro-F1: SSL 0,8690; kısa Transformer 0,8322; yaklaşık adım eşlenmiş uzun Transformer 0,8987. Bu yüzden genel SSL üstünlüğü söylemiyoruz. Ayrı ürün sürümündeki 10 üyeli model, önceden incelenmiş 486 örnekte 38 kesimin 28’ini bulup 10’unu kaçırdı.

Veri hattı ve çıkarım çalışıyor; sonuçlar kayıtlardan yeniden hesaplanabiliyor. Yapay zekâ kodlama, analiz denetimi ve yazıma yardım etti; kendi fiilî katkılarımı ayrıca açıklayacağım. Görüşmede bilimsel yorumu ve bağımsız değerlendirme adımını netleştirmek istiyorum. Güçlü taraf olumlu bulguyu zorlayıcı kontrollerle sınamak; sınır aynı veri kaynağında geliştirme. Bu ayrım tek yüksek skordan önemlidir.

Yedi dakikalık gösterimli anlatım

- 1. dakika: Girişten sonra bir seriyi aç; girdinin iki yılını ve eksik ayları göster.

- 2. dakika: Veri ayrımını çiz. Komşuluk kadar ortak olaylar da birlikte tutulmalı.

- 3–4. dakika: Sonuç şekilleriyle kısa eğitimdeki kazancı, uzun kontrolün yorumu nasıl değiştirdiğini anlat; yukarıdaki sonuç paragrafını kullan.

- 5. dakika: Ayrı 10 üyeli üründe bulunan ve kaçırılan kesimi göster; gerçek çıkarımı çalıştır.

- 6. dakika: Kanıt dosyasını aç. Yeniden hesaplama denetlenebilirlik sağlar; yeni ülke başarısını kanıtlamaz.

- 7. dakika: Bağımsız veri ve araştırma sorusu için karar iste; katkı kaydını ve açık sorularını göster.


### İlk beş soruyu açıklayabilmek

Soruyu sesli oku, yanıtla, sonra örneğe bak. Terimin anlamı kadar neyi değiştirdiğini açıkla. Yanıtı kopyalamak yerine bir cümle kısaltıp kendi örneğinle anlat.

Birinci soru Bu proje ne yapıyor

Seçilen konumun iki yıllık uydu gözlemleriyle ikinci yıldaki kesimi sınıflandırır. Hedef 2020 ise 2019 ve 2020 kullanılır. Tam iki yıl gerektiğinden anlık uyarı değildir.

İkinci soru Etiket nereden geliyor

Etiketler DISFOR’daki insan yorumları ve yardımcı bilgilerdendir; yeni arazi ölçümü yapılmadı. Eğitimdeki referans etiket ile model tahmini ayrıdır. Uyuşmamaları etiketi kesin yanlış yapmaz.

Üçüncü soru Model zaten kayıtlıysa düğme ne yapıyor

Çıkarım, yeni hazırlanmış girdiden kayıtlı ağırlıklarla skor ve sınıf üretir. Ağırlıklar eğitimde öğrenilen sayılardır; çıkarım bunları yeniden öğrenmez. Ürün hazır sonuçları da gösterir: ekranı açmak yeniden çıkarım çalıştırmak değildir.

Dördüncü soru Neden tek bir başarı yüzdesi yok

Doğruluk tüm örneklerde doğru karar oranını, kesim duyarlılığı gerçek kesimleri bulma oranını ölçer. Macro-F1 iki sınıfın F1’ini eşit ortalar. Çok sayıda orman örneği doğruluğu yüksek tutarken önemli kesimler kaçabilir.

Beşinci soru Bu veri gerçekten yeterli mi

2.213 konum kontrollü karşılaştırmayı destekler; her ülkeye yeterlilik kanıtlamaz. 276 kesim, kesim içeren 141 mekânsal bileşen var. Aynı olayın noktaları benzeyebilir; 3 seed yalnız eğitim rastlantısını inceler, yeni saha örneği eklemez.

Prova: Arkadaşın bu beş soruyu yalnız senin anlatımından yanıtlasın. Yanlış anladığını savunmaya geçmeden düzelt; böylece açıklamandaki eksikleri bulursun. Öğrenmenin göstergesi hiç soru almamak değil, somut örnekle yanıtlayabilmektir.


## Zor sorular sonraki deney ve toplantı


### Zor sorularda kanıta dönmek

Cevap sırası: gözlenen sonuç, kontrolün sınadığı şey, sonucun sınırı. Bir kavramı bilmek, ilgili tüm araştırma sonuçlarını bilmek değildir.

Altıncı soru İki farklı maske neden var

Gözlem maskesi gerçek ölçümleri; ön eğitim maskesi bunlardan geçici gizlenenleri gösterir. Yapılandırılmış maske ardışık aylar ve bantları, bağımsız hücre kontrolü tek tek değerleri gizler. Fark aralığı sıfırı içerdiğinden yapılandırılmış maskenin kesin üstünlüğü gösterilmiş değildir.

Yedinci soru SSL faydalı mı değil mi

Yüzde 20 etikette SSL kısa Transformer’dan iyi; yaklaşık adım eşlenmiş uzun denetimli kontrol SSL’den iyi macro-F1 verir. Yorum karşılaştırıcıya bağlıdır. Adım eşleme işlem maliyetini veya etiket görülme sayısını tam eşitlemez; tek bir nedensel açıklama kanıtlanmaz.

Sekizinci soru O zaman üründe neden SSL var

advanced_v3 ayrı üründür: eğitim içi coğrafi seçimde ilk iki tarif CNN ve SSL Transformer’dı; beşer eğitim birleştirildi. paper_v4 başka protokolde tekil modelleri karşılaştırır. Makale testine göre ürünü değiştirmek yerine değişiklik için yeni değerlendirme planlanmalıdır.

Dokuzuncu soru Sızıntı ve aşırı öğrenme çözüldü mü

Aşırı öğrenmede eğitimde işe yarayan ayrıntılar yeni örneklere taşınmaz; sızıntıda değerlendirme bilgisi öğrenme veya seçime uygunsuz biçimde girer. Coğrafi grup ayrımı, yalnız eğitimde ölçekleme ve dış testin ön eğitimden çıkarılması doğrudan karışmayı sınırlar. Aynı verideki geçmiş geliştirmeler nedeniyle tüm genelleme sorunları çözülmüş değildir.

Onuncu soru Yenilik var mı yayımlanır mı

Transformer ve maskeli öğrenme yeni icat değil. Aday katkı, eşlenmiş etiket alt kümeleri ve eğitim bütçesi kontrolleriyle şeffaf ampirik karşılaştırmadır. Yayın yeterliliği uzman değerlendirmesi ve literatür konumlandırması gerektirir; kabul, ortak yazarlık veya yeni saha doğrulaması olmuş sayılmaz.

Son iki soruyu kaynaksız yanıtla. Güçlü cümlelerin altını çiz; “tamamen, kesinlikle, her yerde” sözlerini hangi kanıtla savunacağını kontrol et.


### Sonraki deneyi birlikte tasarlamak

Bu plan yeni bağımsız saha çalışması içindir. Kör etiketleme ve protokol dondurma araçları hazır; gerçek veri ve insan etiketlemesi hocayla planlanmalı. Türkiye verisi var sayılmıyor. Daha büyük modelden önce kullanım amacını ve gereken bağımsız kanıtı belirle.

Önce soruyu ve veriyi belirle

- Hedefi sınırla: iki takvim yıllık kesim sınıflandırmasını yeni bölgeye taşımak örnektir. Yangın erken uyarısı seçilirse görev, etiket ve veri düzeni değişir.

- Bölge ve dönemi skorları görmeden seç; veri erişimi, kaynak hakları, bantlar, ölçek, bulut bilgisi ve aylık desteği araştır. Uygun veri yoksa temin planıyla başla.

- Orman ve kesimlerin seçileceği kaynakları önceden yaz; coğrafi ve olay ilişkilerini kaydet. Tek olaydan 100 yakın nokta, 100 bağımsız olay değildir.

- Yorumlayıcı skoru görmeden etiketlesin. Belirsiz örnekler, ikinci yorumlayıcı ve uzlaşma kuralları önceden belirlensin. Gereken kurumsal izinler ve sorumluluklar gerçek çalışma kapsamına göre netleştirilsin.

Sonra ölçme kuralını dondur

- Örneklem hesabını duyarlılık ve yanlış alarm belirsizliğine göre yap; evrensel yeterli sayı yok. 111 adayda 1 kesim, kesim değerlendirmesini desteklemez.

- Geliştirmeye kapalı konum ve olayları baştan ayır; model, eşik ve ana ölçütü sonuçlardan önce sabitle. Teste göre ayar, testin dokunulmamışlığını bitirir.

- Önce dondurulmuş modeli ölç: macro-F1, AP, kesim duyarlılığı ve yanlış alarm sayısını destekleriyle raporla. Uyarlama için ayrı geliştirme verisi, değişmiş modeli ölçmek için başka korunmuş test gerekir.

Alıştırma: Bir sayfaya bölgeyi, veri adayını, olay birimini, etiketleme sorumlusunu, ana ölçütü ve sabit kararları yaz. Bilinmeyene “bilinmiyor” de; hocayla hangi boşluğun nasıl araştırılacağını kararlaştır.


### Görüşmeyi öğrenmeye ve karara dönüştürmek

Hazırlık her cevabı bilmek değil; sonucu doğru göstermek, bilinmeyeni ayırmak ve sonraki adımı kaydetmektir. Hocanın sorusunu saldırı değil açıklık ihtiyacı olarak gör.

Toplantıdan önce kontrol et

- Ürünü kendi bilgisayarında açıp gerçek çıkarımı bir kez dene. Sorun varsa gizleme; başladığı adımı ve hata mesajını kaydet.

- Türkçe rapor, İngilizce makale ve görüşme notunu hazır tut. Sayıları kaynakta bul; eski MVP ile güncel tabloyu karıştırma.

- Bir doğru ve bir kaçırılan kesim hazırla; skorun etiket veya doğruluk garantisi olmadığını açıkla.

- Üç açık sorun ve bir karar önerisi yaz. Veri adayını araştırma önerisi, verinin temin edildiği anlamına gelmez.

Bilmediğin soruya nasıl cevap verilir

“Bu ayrıntıyı güvenle açıklayamıyorum. Bildiğim kısım şu; belirsiz kısmı kod veya kaynaktan kontrol edip gerekçeli yanıt hazırlamak istiyorum.” Soruyu kendi sözlerinle tekrarlayıp doğru anladığını doğrula; bilmediğin terimi açıklat. Tahminle kesin yanıt verme.

Katkı kaydını somut tut

Kişisel notunda üç sütun kullan: yapılan iş / yapan kişi veya araç / benim kontrolüm. Yalnız yaptıklarını yaz; yapay zekânın kodlama, denetim ve yazım yardımını belirt. Dosyayı okumak ile algoritmayı geliştirmek farklı katkılardır; ikisini doğru adlandır.

Toplantıdan sonra ne kaydedilir

Aynı gün karar, açık soru, sorumlu ve anlaşılan tarihleri yaz. Öneriyi karardan; onaylanmamış yazarlık/yayını onaydan ayır. Yeni kuralları sonuçlardan önce ayrı sürümde tanımla; hocanın düzeltmesini ve gerekçesini kaydet. Sonraki çalışmayı buradan başlat.


## Kendini sınama ve cevap anahtarı


### Kaynağı kapat ve kendini sına

Bu sınav resmî yeterlik ölçümü değil, çalışma önerisidir. 25 dakika ayır; notları, ürünü ve yanıt bölümünü kapat. Cevaplarını yaz; zihninden doğru bildiğini düşünmek yetmez. Hesap makinesi serbest; işlemin nedenini açıkla.

Toplam 100 puan. Bilmediğini boş bırak veya eksik kısmı yaz; bu eksik kaydı değerlidir. Her yanıta “eminim / kısmen eminim / kontrol etmeliyim” ekle. Bütün soruları bitirmeden yanıt bölümünü açma.

- 1 — 6 puan: Hedef 2020 ise pencere ve modelin sorusu nedir? Neden anlık alarm değildir?

- 2 — 6 puan: Eğitim ve kayıtlı modelle çıkarım nasıl ayrılır? Yeni tahmin gerçek etiket ister mi?

- 3 — 8 puan: 2.213 konum, 276 kesim, 874 mekânsal bileşen neyi sayar? Neden tüm noktalar bağımsız değildir?

- 4 — 8 puan: Kat, seed ve eğitim koşusu nedir? 180 koşu neden 180 bağımsız veri kümesi değildir?

- 5 — 10 puan: İki doğrudan sızıntı önlemi söyle. Çalışma neden yine de bağımsız dış doğrulama değildir?

- 6 — 10 puan: Gözlem maskesini SSL maskesinden ayır. Ölçülmemiş değer gizlenen eğitim hedefi olabilir mi?

- 7 — 8 puan: 0,8322 / 0,8690 / 0,8987 neyi karşılaştırır? Çıkarılamayacak bir iddia söyle.

- 8 — 8 puan: Macro-F1 ve doğruluk neden farklı? Orman çoğunluğu yorumu nasıl etkiler?

- 9 — 8 puan: 38 gerçek kesimin 28’i bulunduysa kaçırılan sayı ve duyarlılık nedir? İşlemini göster.

- 10 — 8 puan: 448 ormanda sıfır yanlış alarm Türkiye’de neyi garanti etmez? Örnek desteğini belirt.

- 11 — 10 puan: paper_v4 ve advanced_v3 neden ayrı anlatılır? Üründeki SSL, uzun eğitim kontrolüyle çelişir mi?

- 12 — 10 puan: Bağımsız deney için iki karar öner. Yapay zekâ yardımını ve kendi katkını nasıl dürüstçe açıklarsın?


### Yanıtları kontrol et ve eksiklerini bul

Önce soruları bitir. Aynı sözcükler değil doğru anlam ve gerekçe aranır. Her yanıttaki iki parçayı ayrı puanla; doğru terimi açıklayamıyorsan ilgili kısmın puanının en fazla yarısını ver. Toplam en çok 100.

- 1: 2019–2020 penceresi, hedef 2020 kesimi (3); tam iki yıl kullanımı anlık alarm değildir (3).

- 2: Eğitim ağırlık öğrenir, çıkarım kayıtlı ağırlığı kullanır (3); çıkarım gerçek etiket gerektirmez (3).

- 3: 2.213 konum, 276 kesim, 874 bağlı bileşen (4); yakınlık ve ortak olay bağımlılığı (4).

- 4: Kat veri ayrımı, seed rastlantı başlangıcı, koşu bir eğitimdir (4); aynı veri tekrar kullanılır (4).

- 5: Grup ayrımı ve yalnız eğitimde ölçekleme gibi iki önlem (5); aynı veride geçmiş geliştirmeler (5).

- 6: Gerçek gözlem desteği ile yapay gizleme ayrımı (5); ölçülmeyen değer bilinen yeniden kurma hedefi olamaz (5).

- 7: Yüzde 20 etikette kısa Transformer 0,8322; SSL 0,8690; uzun Transformer 0,8987 (4); genel SSL üstünlüğü çıkarılamaz (4).

- 8: Macro-F1 sınıf F1’lerini eşit ortalar; doğruluk örnek sayar (4); çoğunluk kaçırılan kesimleri gizleyebilir (4).

- 9: Kaçırılan 38−28=10 (4); duyarlılık 28/38≈0,7368, yüzde 73,68 (4).

- 10: Sıfır, incelenen 448 ormandaki gözlemdir (4); yeni coğrafyaya garanti değildir (4).

- 11: Tekil araştırma modelleri ve ayrı ürün birleşimi (5); üyeler önceki eğitim içi seçimle belirlendi (5).

- 12: Sonuç öncesi bölge, olay ayrımı veya eşik gibi iki karar (5); yardımı belirtip yalnız gerçek katkını sahiplenmek (5).

Puan geçme belgesi değildir. En düşük üç yanıtı, özellikle “eminim” dediğin yanlışları yeniden çalış; ertesi gün farklı örnekle çöz. Yüksek toplam, sürüm ayrımını ve dış doğrulama sınırını açıklayamadığın konuları bildiğini göstermez.


## Sözlük ve teknik başvuru


### Kavram sözlüğü veri ve öğrenme

Takıldığın terimi sözlükte bul; tanımını öğrenip projeden örneğe bağla. “Maske” derken gerçek eksikliği mi, SSL için yapay gizlemeyi mi kastettiğini belirt.

| Terim | Bu projede nasıl düşünmelisin |
| Uzaktan algılama | Yeryüzünü sensörle uzaktan ölçme. |
| Bant | Belirli bir dalga boyu aralığındaki ölçüm kanalı. |
| Piksel | Görüntüde bir alanı temsil eden ölçüm; tek ağaç sayılmaz. |
| Zaman serisi | Aynı konumdan zaman boyunca alınan sıralı ölçümler. |
| DN | Kaynağın sayısal ölçüm değeri; bu projede yeni yansıtım dönüşümü eklenmedi. |
| Etiket | Karşılaştırma için kullanılan kaynak referans sınıfı. |
| Özellik | Modelin girdisinden kullandığı bilgi; örneğin bant ölçümü. |
| Maske | Hangi hücrelerin gözlendiğini veya bilinçli saklandığını belirten işaret. |
| Model | Girdileri tahmine dönüştüren öğrenilmiş kural veya işlev. |
| Parametre ve ağırlık | Eğitimle öğrenilen sayısal değer. |
| Hiperparametre | Öğrenme hızı gibi eğitimden önce belirlenen ayar. |
| Loss ve kayıp | Eğitimde küçültülmeye çalışılan hata hedefi. |
| Epoch | İlgili eğitim kümesinin bir kez işlenmesi. |
| Batch | Bir güncellemede birlikte işlenen örnek grubu. |
| Seed | Rastgele işlemleri başlatan sayı; yeni saha verisi yaratmaz. |
| SSL | Sınıf etiketi yerine verinin kendisinden görev kurarak ön öğrenme. |
| Fine tuning | Önceden öğrenilmiş modeli etiketli görev için uyarlama. |
| Çıkarım | Eğitilmiş modeli kullanarak tahmin üretme. |

Parametre ile hiperparametreye birer örnek ver.

Öğrenilen bağlantı ağırlığı parametre; eğitim öncesi seçilen öğrenme hızı hiperparametredir. İkisi de ayar gibi görünür; belirlenme biçimi farklıdır.


### Kavram sözlüğü değerlendirme ve dosyalar

Ölçütün verisini, eşiğini ve sınıfını sor; her ölçüt aynı soruyu yanıtlamaz. Dosyaları görevlerine göre aç; hepsi metin değildir.

| Terim | Kısa açıklama |
| Baseline | Yeni yöntemin kıyaslandığı temel karşılaştırıcı. |
| Ablasyon ve kontrol | Bir tasarım tercihinin katkısını sınayan karşılaştırma. |
| Fold ve kat | Çapraz doğrulamada sırayla dış test olan veri bölümü. |
| OOF | Her örneğin kendisini eğitimde görmeyen kat modelinden aldığı tahmin. |
| Veri sızıntısı | Test bilgisine öğrenme veya seçim aşamasında erişilmesi. |
| Aşırı uyum | Eğitimde iyi görünürken yeni örneklere iyi genellenememe. |
| Precision ve kesinlik | Kesim dediklerimizin kaçının referansta kesim olduğu. |
| Recall ve duyarlılık | Referanstaki kesimlerin kaçını bulduğumuz. |
| F1 | Kesinlik ve duyarlılığı birlikte özetleyen harmonik ortalama. |
| Macro F1 | Her sınıfın F1 değerinin eşit ağırlıklı ortalaması. |
| AP | Skor sıralamasının kesinlik ve duyarlılık üzerinden özeti. |
| Kalibrasyon | Skorların gözlenen sıklıklarla uyumunu geliştirme veya değerlendirme. |
| Bootstrap | Belirlenen örnekleme birimlerini yeniden seçerek belirsizliği inceleme. |
| Ensemble | Birden fazla modelin çıktılarının birleştirilmesi. |
| JSON ve GeoJSON | Yapılandırılmış metin; GeoJSON ayrıca coğrafi geometri taşır. |
| NPZ ve PT | Sayısal diziler için arşiv; PyTorch model kaydı için dosya uzantısı. |
| Manifest ve SHA 256 | İçerik/provenans kaydı ve dosyanın değişip değişmediğini sınayan özet. |

SHA-256 eşleşmesi içerik eşitliğini gösterir, bilimsel yorumun doğruluğunu kanıtlamaz. İyi ROC-AUC de sabit eşikte tüm kesimlerin bulunduğu anlamına gelmez.


### Teknik ayrıntılar için başvuru sayfası

Bu ayarlar ezber için değil, sorulduğunda kaynağı bulmak içindir. Büyük mimari otomatik olarak iyi değildir; deney ve eğitim düzenine bak.

| paper_v4 ayarı | Sabit düzen |
| Etiket oranları | Eğitim bölümünde yüzde 20 ve yüzde 100; test etiketleri ayrı. |
| Başlangıçlar ve katlar | Seed 7 17 27; 5 coğrafi kat. |
| Standart sinir ağı eğitimi | 40 denetimli epoch; batch 64. |
| SSL ön eğitim | 60 epoch; saklanan gözlenmiş değerlerde Smooth L1 kaybı. |
| Denetimli kayıp | Sınıf ağırlıklı çapraz entropi; label smoothing 0,02. |
| Transformer | Genişlik 48; 2 katman; 4 attention başlığı; dropout 0,15. |
| CNN | Genişlik 64; 3 artık bağlantılı blok; dropout 0,20. |
| Öğrenme hızı | CNN 0,001; Transformer 0,0005; SSL ön eğitim 0,001. |
| Optimizasyon | AdamW; weight decay 0,01; gradyan norm sınırı 1. |
| Random forest | 500 ağaç; en küçük yaprak 4; max_features 0,7. |
| Ek denetimli kontrol | Yüzde 20 etikette yaklaşık adım eşleşmesi için 320 epoch. |
| Karar ve belirsizlik | Eşik 0,50; mekânsal bileşen üzerinden 2.000 bootstrap çekimi. |

Attention başlığı, dizideki ilişkileri hesaplayan paralel dikkat bileşenidir. Dropout eğitimde bazı ara etkinlikleri rastgele kapatarak aşırı bağımlılığı azaltmayı hedefler. Artık bağlantı girdiyi çıktıya ekler. AdamW güncelleme kuralı; gradyan sınırlaması çok büyük güncellemelerin frenidir. Bunlar tek başına yeni yöntem katkısı değildir.

Ürün farklıdır: advanced_v3’ün beş SSL Transformer’ı 36, beş CNN’i 21 denetimli epoch kullanır. Seçim eğitim içindeki dört coğrafi katla yapılır. 461 geliştirme noktasında kalibrasyon vardır; paper_v4 ana deneyinde yoktur.


## Kaynaklar ve son tekrar


### Kaynakları hangi soruyla okumalısın

Önce örnekleri çalış, sonra kaynaklara belirli soruyla git. İlk görüşme için her makaleyi baştan sona okuyup tüm matematiğini anlamak gerekmez. Bağlantılar birincil kaynaklardır; projedeki tercihler için kod ve protokole bak.

[G1 ESA Sentinel 2 cihazı ve bantları](https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-2/Instrument)

Soru: Bant ve piksel çözünürlüğü nedir; cihazda 13 bant varken modelde neden 10 girdi var?

[G2 DISFOR veri kümesinin kaynak makalesi](https://essd.copernicus.org/preprints/essd-2026-185/)

Soru: Etiketler nereden? 30 Eylül 2026 kontrolünde değerlendirmedeki ön baskıydı; bizim makalemiz değildir.

[G3 Copernicus Sentinel 2 işleme ve SCL açıklaması](https://sentiwiki.copernicus.eu/web/s2-processing)

Soru: Kalite ve sahne sınıfları nasıl tanımlanır? Projenin seçim kodunu da oku.

[G4 scikit learn Average Precision tanımı](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html)

[G5 scikit learn F1 tanımı](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html)

Soru: AP trapez alanıyla aynı mı; macro-F1 hangi sınıfları nasıl ortalar? Kodumuz AP kullanır.

[G6 Zerveas ve arkadaşları zaman serilerinde Transformer ön öğrenmesi](https://github.com/gzerveas/mvts_transformer)

[G7 Roberts ve arkadaşları yapılandırılmış veride çapraz doğrulama](https://epub.uni-regensburg.de/39299/)

[G8 Tseng ve arkadaşları Presto](https://arxiv.org/abs/2304.14065)

[G9 Guo ve arkadaşları sinir ağlarında kalibrasyon](https://proceedings.mlr.press/v70/guo17a.html)

G6–G9 soruları sırasıyla: Etiketsiz görev nasıl kurulur? Rastgele ayrım neden yanıltır? Uzaktan algılama ön öğrenmesinde önce ne yapılmış? Skor neden güven garantisi değildir? Farklı veri kümelerindeki skorları yarıştırma.

İngilizce makalenin 8 kaynaklı tam listesi paper/references.json içindedir. Çizimler proje için yeniden üretildi; gerçek örnek grafikleri mevcut veri ve tahminlerdendir. Sayılar 30 Eylül teslim denetimiyle eşleşir.


### Görüşmeden hemen önce son tekrar

Görüşme öncesi sesli anlat, sonra dosyayı gerçekten bul. Sınav eksiklerini gidermeden bu sayfayı ezberlemek, devam sorularına yetmez.

Otuz saniyede projem

“Gerçek Sentinel-2 zaman serilerinden orman kesimini geriye dönük sınıflandırıyoruz. 2.213 konum, 5 coğrafi kat, 3 başlangıç ve 180 eğitim kaydı var. Az etikette SSL kısa eğitimli modelden iyi; adımlar eşlendiğinde üstünlük sürmüyor. Ayrı eğitilmiş ensemble’ı çalışan yerel üründe gösterebiliyorum. Sonraki hedef bağımsız veride doğrulama.”

| Aklında tut | Nerede göster |
| 2.213 konum ve 276 kesim | Türkçe raporun veri bölümü |
| 24 ay ve 10 bant | Üründeki gözlem serisi ve veri sözleşmesi |
| 5 kat × 3 seed ve 180 koşu | paper_v4 protokolü ve runs klasörü |
| Yüzde 20 SSL 0,8690 | paper_v4 sonuç tablosu |
| Kısa 0,8322 ve adım eşlenmiş 0,8987 | Aynı tablonun karşılaştırıcıları |
| Ürün 38 kesimin 28’ini buldu | Geçmiş değerlendirme matrisi |
| 58 yazılım testi saha başarımı değildir | Nihai teslim doğrulaması |
| Bağımsız Türkiye doğrulaması yok | Raporun kapsam ve gelecek çalışma bölümü |

Açılış sırası

URUNU_AC.command ile ürünü aç; Türkçe sonuç raporunu hazır tut. Doğru kesim disfor-1733-2019’u, ardından geçmiş değerlendirmede kaçırılan disfor-1664-2018’i göster. Makalede kısa/uzun karşılaştırmasını anlat; son olarak eğitim kaydı ve sonraki deney önerisini aç.

Bilmediğinde kullanacağın cümle

“Bu ayrıntıyı ezberden yanlış söylemeyeyim. Kodu ve deney kaydını kontrol edebilirim; bulamazsam not alıp kanıtıyla döneceğim.” Bu, rastgele teknik kelimelerden daha güvenilir bir araştırma alışkanlığıdır.

Üç kararla çık: hangi araştırma sorusu ilerletilecek, bağımsız değerlendirme verisi nasıl sağlanacak, benim ve diğer araştırmacıların sonraki somut görevleri ne? Yapay zekâ yardımını ve kendi fiilî katkını doğru belirt.


## Dosya dayanakları ve okuma rotası

D01 README.md

D02 URUNU_AC.command

D03 data/disfor/downloads.json

D04 data/disfor/sample_manifest.json

D05 data/examples/inference_windows.json

D06 docs/ARASTIRMA_VE_URUN_RAPORU.md

D07 docs/GORUSME_AKISI_VE_SORULAR.md

D08 docs/NIHAI_BILIMSEL_DENETIM.md

D09 docs/URUN_KILAVUZU.md

D10 docs/VERI_SOZLESMESI.md

D11 experiments/advanced_v3/evaluation.json

D12 experiments/paper_v4/analysis.json

D13 experiments/paper_v4/completion.json

D14 experiments/paper_v4/folds.json

D15 experiments/paper_v4/jobs.json

D16 experiments/paper_v4/oof_predictions.npz

D17 experiments/paper_v4/protocol.json

D18 experiments/paper_v4/runs/ssl_transformer48_f0_s7_b0.2.json

D19 experiments/paper_v4/signature.json

D20 experiments/paper_v4/support_error_audit.json

D21 experiments/paper_v4/unused_probe_audit.json

D22 experiments/paper_v4/verification.json

D23 models/advanced_v3/bundle.json

D24 models/advanced_v3/model_card.json

D25 output/advanced_prediction/input.npz

D26 output/advanced_prediction/manifest.json

D27 output/advanced_prediction/predictions.geojson

D28 output/advanced_prediction/predictions.json

D29 paper/AUTHOR_CONFIRMATION.md

D30 paper/CLAIM_LEDGER.md

D31 paper/ERROR_AUDIT.md

D32 paper/SUPPLEMENT.md

D33 paper/manuscript.md

D34 paper/references.json

D35 reports/disfor_preparation.json

D36 reports/final_delivery_verification.json

D37 reports/paper_v4.html

D38 reports/product.html

D39 reports/product_ui_verification.json

D40 scripts/analyze_paper.py

D41 scripts/package_advanced.py

D42 scripts/package_paper.py

D43 scripts/package_project.py

D44 scripts/prepare_disfor.py

D45 scripts/run_advanced.py

D46 scripts/serve_product.py

D47 scripts/setup.sh

D48 scripts/train_paper.py

D49 scripts/verify_paper.py

D50 src/orman_ssl/advanced.py

D51 src/orman_ssl/experiment.py

D52 src/orman_ssl/inputs.py
