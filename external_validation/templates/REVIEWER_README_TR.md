# Bağımsız yorumlama formu

Size yalnız kendi CSV formunuz ve bu açıklama verilmelidir. Diğer yorumlayıcının yanıtlarını, model skorlarını ve ürünün tahmin ekranını ilk değerlendirmeniz bitmeden açmayın. Koordinatörün özel kimlik eşleştirmesi de bu aşamada gerekli değildir. CSV'de model skoru veya önceden doldurulmuş gerçek etiket yoktur.

Her satır, hedef yıldan önceki yılın 1 Ocak günü ile hedef yılın 31 Aralık günü arasındaki iki tam yıllık pencereyi anlatır. `evidence_ref` alanı inceleyeceğiniz görüntü veya kaynak kaydını gösterir; bu araç görüntü indirmez ve kanıtın doğruluğunu sizin yerinize belirlemez. Kaynakta görünür model tahmini veya hazır referans etiketi varsa, ilk yorumdan önce koordinatöre bildirin. Böyle bir bilginin farkında olduğunuz halde kör yorum yaptığınızı söylemeyin.

Formu ayrı bir dosyaya kopyalayın. İlk altı sütunu değiştirmeyin: `review_id`, `target_year`, `lon`, `lat`, `evidence_ref`, `reviewer_id`. Bunlar dondurulmuş aday ve yorumlayıcı eşleşmesidir. Kimlikler okunabilir aday adlarından bağımsız rastgele üretilir. Koordinatların veya kanıt yolunun yanlış olduğunu düşünüyorsanız durumu gerekçeye yazın; başka konuma sessizce taşımayın.

Son dört sütunu doldurun:

- `label`: `0` iki yıl boyunca bozulmamış orman; `1` ilk yılda bozulmamış orman ve ikinci yılda kesim; `uncertain` karar vermeye yetmeyen kanıt; `exclude` protokolde yazılı bir uygunluk kuralına göre dışarıda. Özel çalışma tanımları için koordinatörün dondurduğu protokol kullanılmalıdır.
- `confidence`: `high`, `medium` veya `low`. Yetersiz kanıtta yüksek güven seçmeyin.
- `rationale`: İncelediğiniz kanıt ve kararın gerekçesi. Dışlamada önceden tanımlı hangi kurala dayandığınızı belirtin.
- `reviewed_at`: Gerçek inceleme zamanı; saat dilimli ISO biçimi gerekir. Örnek biçim `YYYY-MM-DDTHH:MM:SS+03:00`. Yerel dondurma tarihinden önceki tarih kabul edilmez.

UTF-8 CSV olarak kaydedin; alan adlarını eklemeyin veya değiştirmeyin. Virgül içeren açıklamaları CSV düzenleyicisinin doğru tırnaklamasına izin verin. Kaynak dosyanızı değiştirmeden saklayın.

İki yorumlayıcının aynı, yüksek güvenli kararı otomatik uzlaşma sayılır. Kararsızlık, farklı karar veya düşük güven üçüncü kişiye gider. Üçüncü yorumlayıcı iki gerekçeyi görebilir; yine model skorunu görmez. O da güvenle karar veremiyorsa belirsizliği yapay biçimde orman/kesim sınıfına çevirmeyin. Gerekirse önceden yazılmış kanıt yetersizliği kuralıyla açık dışlama ve gerekçe gerekir.

Formdaki kişi adı bir katkı kaydıdır; yazılım kimliğinizi doğrulayan hesap sistemi veya körlüğün bağımsız kanıtı değildir. Gerçek bilimsel sorumluluk yorumlayıcılarda ve koordinatördedir.
