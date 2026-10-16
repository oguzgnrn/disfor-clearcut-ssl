# Nida Hoca ile ilk toplantı

## 8 dakikalık anlatım

**0:00-1:00 · Soruyu söyle.** “Az etiketli orman bozulması probleminde, etiketsiz zaman serilerinden ön öğrenmenin faydasını ölçmek istiyorum. İlk aşamada tek bölge ve sınırlı sınıfla başlayıp coğrafi genellemeyi kontrol etmeyi öneriyorum.”

**1:00-2:30 · Veri bulgusunu göster.** GFD gerçek rasterını ve kaynak sürümü notunu aç. Üretilmiş harita ile ham uydu görüntüsünün farkını açıkla. 0 kodu, NoData yokluğu ve olay tarihi eksikliğini söyle. Bunlar hocanın veri inceleme talebine somut cevaptır.

**2:30-4:00 · Gerçek uydu demosunu çalıştır.** `reports/demo.html` aç; Sentinel tarihlerini, maskeyi ve dNBR haritasını göster. Eşiği değiştir. “Bu bir değişim taraması; doğrulanmış yangın alanı veya eğitilmiş tür tahmini değil.”

**4:00-5:30 · Öğrenme deneyini göster.** Sentetik etiketi görünen karşılaştırma tablosunu aç. RF'yi çıkarma. “Deney altyapısı çalışıyor; bu sayılar gerçek uydu başarımı değil. Aynı modeli ön eğitimli/ön eğitimsiz karşılaştırabildiğimi gösteriyor.”

**5:30-7:00 · İlk gerçek deneyi öner.** Bölge, bağımsız etiket, olay tarihleri ve ayrım protokolünü konuş. Az etiket bütçesinde validation etiketlerinin ek maliyet olduğunu belirt.

**7:00-8:00 · Bir sonraki haftayı somutlaştır.** Bölge/sınıf ve 20 olaylık inceleme görevi netleşsin. GPU veya büyük veri mimarisi kararını veri ihtiyacından sonra ver.

## Hocaya sorulacak beş soru

1. Başlangıç için Türkiye mi, daha güvenilir açık etiketli yabancı bir bölge mi uygun?
2. İlk hedef iki sınıflı bozulma tespiti mi, yeterli olay varsa yangın/kesim ayrımı mı olsun?
3. Olay tarihleri ve bağımsız doğrulama etiketleri için kullanabileceğimiz kamuya açık veya izinli kaynak var mı?
4. SSL makalesinin tam yöntemi ve varsa koduna birlikte erişebilir miyiz; Figshare sürüm farkını yazarlara sormalı mıyız?
5. Bir sonraki toplantıya 20 olay incelemesi ve veri sözleşmesine uyan ilk zaman serisi örneklerini getirmem uygun mu?

## Gelebilecek sorulara dürüst cevap

**“Proje bitti mi?”** Toplantıya hazır başlangıç ve teknik MVP tamam; bilimsel çalışma için gerçek olay etiketleri ve gerçek coğrafi test henüz yok.

**“Neresi yeni?”** Yenilik henüz kanıtlanmış değil. Aday katkı etiket verimliliği, gözlem kaybı ve coğrafi aktarımı aynı kontrollü protokolde ölçmek. Yeni mimari iddiasıyla başlamıyorum.

**“Sentetik veri niye var?”** Veri ayrımı, kayıp maskesi, eğitim, checkpoint ve ölçüm hattını gerçek veri gelmeden test etmek için. Yayın başarımı olarak kullanılmayacak.

**“Gerçek veride neyi yaptın?”** İki GFD dosyasını indirip denetledim; gerçek S2 kesitlerinde kalite maskeli indeks ve fark haritası hesapladım. SSL sınıflandırmasını gerçek doğrulanmış olaylarla henüz eğitmedim.

**“RF daha iyi çıkarsa?”** Bunu raporlarım. SSL'nin ek maliyetine değip değmediği araştırma sorusunun parçası.

## E-posta taslağı — GÖNDERİLMEDİ

Hocanın istediği gibi mevcut e-posta zincirine cevap olarak kullanılabilir:

> Nida Hocam merhaba,
>
> Yönlendirmeniz doğrultusunda temel CBS/uzaktan algılama notlarını ve paylaştığınız çalışmaların ilk incelemesini hazırladım. Küresel orman bozulması veri setinden iki örneği indirip yapısını inceledim; ayrıca gerçek Sentinel-2 görüntülerinde küçük bir değişim analizi ve self-supervised öğrenme için çalışan bir deney altyapısı oluşturdum.
>
> Öğrenme hattını şu aşamada sentetik veriyle kontrol ettim; gerçek uydu verisinde doğrulanmış bir sınıflandırma sonucu henüz üretmedim. İlk gerçek deney için bölge, sınıf ve bağımsız etiket kaynağını sizinle netleştirmek isterim. Veri setinin yayımlanan makalesi ile Figshare açıklaması arasında da görüşmede paylaşmak istediğim birkaç fark gördüm.
>
> Toplantıda kısaca gösterebilmek için proje notlarını ve örnek çıktıları bir dosyada topladım. Uygun olduğunuz zamanda üzerinden geçebiliriz.
>
> Çok teşekkür ederim hocam, iyi çalışmalar dilerim.
>
> Saygılarımla,
> Mehmet Oğuz Güneren

Metni kendi okuma ve anlama düzeyine göre gözden geçir. Toplantı öncesinde kodun `split_groups`, `normalize`, `pretrain` ve `finetune` fonksiyonlarını okuyup kendi cümlelerinle açıklayabilmen özellikle yararlı olacaktır.
