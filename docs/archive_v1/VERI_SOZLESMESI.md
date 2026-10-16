# Gerçek deney için veri sözleşmesi

NPZ, `allow_pickle=False` ile açılmalıdır. Nesne dizileri kullanılmaz. Bu sözleşme Sentinel sahne indirme ve uzman etiketleme sürecinin çıktısıdır; mevcut iki tarihli demo otomatik olarak eğitim verisine dönüştürülmez.

| Alan | Biçim | Anlam |
|---|---|---|
| x | float32 [N,T,C] | Fiziksel birimi belli, grid uyumlu zaman serisi |
| observed | bool [N,T,C] | Gerçekten geçerli gözlem; eksik x değeri NaN olabilir |
| days | float32 [N,T] | Ortak başlangıç tarihinden geçen gün; artan sıra |
| y | int64 [N] | 0'dan başlayan ardışık sınıf ID |
| groups | tamsayı veya Unicode [N] | Ayrıştırılamaz bağımsız olay/coğrafi blok |
| ids | Unicode [N] | Tekil örnek ID |
| metadata | Unicode scalar, JSON | Köken, sınıflar, kanallar ve hizalama |

Gerçek veri metadata'sında `kind: real`, `classes`, `channels`, `source`, `label_provenance`, `group_definition`, `temporal_alignment` zorunludur. Bu alanların bulunması, içeriğin doğru olduğunun otomatik kanıtı değildir. Kaynak DOI/sahne ID, sürüm, koordinat, CRS ve olay tarihleri ayrı örnek manifestinde tutulmalıdır.

Örnek metadata (şablondur, toplanmış veri değildir):

```json
{
  "kind": "real",
  "classes": ["verified_stable_forest", "verified_disturbance"],
  "channels": ["B4_reflectance", "B8_reflectance", "B12_reflectance", "VV_db", "VH_db"],
  "source": "Her sahnenin STAC ID ve hash kaydı",
  "label_provenance": "Bağımsız uzman anotasyonu ve olay kaydı referansları",
  "group_definition": "Aynı olayın tamamı tek grup; blok tamponları ayrıca kontrol edildi",
  "temporal_alignment": "UTC edinim tarihleri; olay tarihi ve inceleme penceresi manifestte"
}
```

En az 10 grup ve her splitte tüm sınıflar gerekir. Bu yalnızca teknik alt sınırdır; bilimsel yeterlilik için daha çok bağımsız olay gerekir. Kod uygun olmayan ayrımı hatayla durdurur; test başarımına göre uygun seed aramaz.

Mevcut deney tüm örneklerde sınıf etiketi olmasını bekler, fakat yalnızca seçilen eğitim etiketlerini fine-tune sırasında kullanır. Ek, tamamen etiketsiz bir havuzun y=-1 ile eklenmesi şu an desteklenmez. Gerçek pilotta etiket bütçesi deneyini tamamladıktan sonra ayrı train-only etiketsiz havuz desteği eklenebilir.

Kanal sırası checkpoint metadata'sıyla aynı olmalıdır. SAR dB ile optik yansıtım karıştırılmadan açıklanmalı; normalizasyon yalnızca eğitim gözlemlerinden hesaplanır. Uzunluklar bu MVP'de sabittir; değişken uzunluklu seriler takvim slotlarına ve observed maskesine dönüştürülmelidir. Gerçek gözlenmeyen hücreler SSL hedefi olamaz.
