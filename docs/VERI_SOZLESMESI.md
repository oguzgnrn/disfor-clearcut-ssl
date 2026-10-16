# Güncel veri sözleşmesi

## Hazır veriler

- `data/processed/real_series.npz`: 2.213 gerçek örnek, etiket ve gruplarla eğitim girdisi.
- `data/processed/test_inference.npz`: yalnız testteki 486 örnek; y/groups çıkarılmış, doğrudan tahmin girdisi.
- `data/disfor/sample_manifest.json`: örnek ID, kaynak nokta, yıl, koordinat, etiket kökeni, mekânsal grup ve split.

| Alan | Biçim | Çıkarımda gerekli mi? |
|---|---|---|
| x | float32 [N,24,10]; kaynak DN birimi | Evet |
| observed | bool [N,24,10]; geçerli gözlem maskesi | Evet |
| days | float32 [N,24]; pencere başlangıcından gün | Evet |
| ids | tekil Unicode [N] | Evet |
| metadata | JSON Unicode scalar; channels ve units zorunlu | Evet |
| y | int64 [N]; 0=bozulmamış, 1=kesim | Yalnız eğitim/değerlendirme |
| groups | bağımsız mekânsal/olay grubu [N] | Yalnız eğitim/değerlendirme |

Bant sırası: B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12. Mevcut modele yansıtım 0-1 veya SAR dB değerleri bu DN bantlarının yerine verilmez. Kaynakta açıkça belgelenmeyen ofset uygulanmadı; başka işleme geçmişinden gelen görüntüler doğrudan uyumlu varsayılmaz.

Zaman penceresi iki tam takvim yılıdır; günler her ayın 15'ini pencere başlangıcına göre kodlar. Model anlık olay tespiti yapmaz. Hedef, ikinci takvim yılında kesim olup olmadığının geriye dönük sınıflandırılmasıdır. Yeni örneklerde arazi türü ve zaman kapsamı eğitim sözleşmesiyle uyuşmalıdır.

Aylık medyan oluştururken source clear ve SCL 4/5 geçerli kabul edilir. Her yılda en az 6 ay gözlenmiş olmalı. observed=False hücreler NaN olabilir; modelden önce train ölçekleyicisiyle standardize edilir ve sıfır dolgusu + ayrı maskeyle verilir. Eksik değer yeni gözlem sayılmaz.

`quality_eligible=False` sonucu girişin eğitimde kullanılan aylık kalite koşulunu sağlamadığını belirtir. Bunun True olması coğrafi/ekolojik alan uyumunu veya doğruluğu garanti etmez. Çıktı olasılıkları kalibre edilmiş güven değildir.

Torch checkpoint `weights_only=True` ile yüklenir. RF joblib dosyaları yalnızca bu proje tarafından üretilmiş güvenilir yerel dosyalardan yüklenmelidir; bilinmeyen joblib dosyası açılmamalıdır.

Girdi doğrulaması boş örnek kümesini, yanlış bant sayısını/sırasını, tekrarlı veya yanlış boyutlu kimlikleri, yanlış birimleri ve takvim aylarının 15. gününe karşılık gelmeyen zaman ofsetlerini reddeder. `units` alanı modeldeki kaynak DN açıklamasıyla aynı olmalıdır; elle düzenlemek fiziksel veri uyumunu sağlamaz. Ham gözlemler için `orman_ssl.inputs` veya `scripts/run_mvp.py` bu alanları uygun biçimde üretir.
