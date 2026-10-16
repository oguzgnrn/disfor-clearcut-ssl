# Bağımsız değerlendirmeye hazırlık aracı

Bu klasör **gelecekte edinilecek gerçek veri** için protokol, kör etiketleme ve örnek desteği iş akışını sağlar. Henüz dış saha verisi toplanmadı. Şablonlar boştur; testlerdeki yapay kayıtlar gerçek veri veya başarı sonucu değildir. Araç model çalıştırmaz, doğruluk/F1 üretmez ve mevcut araştırma dosyalarını değiştirmez.

İhtiyaç: mevcut projenin Python 3.11 ortamı. Ek Python paketi gerekmez. Komutları tam projenin ana klasöründe çalıştırın. Çıktı klasörleri her adımda yeni olmalıdır; mevcut kayıt üzerine yazılmaz.

## Hocayla önce kararlaştırılacaklar

Hedef, iki tam yıldan ikinci yıldaki kesimin sınıflandırılmasıdır. Bölge/dönem, veri kaynağı, örnekleme, görev dışı durumlar, iki ayrı yorumlayıcı ve üçüncü uzlaşma sorumlusu belirlenir. Kesim ve orman için hem asgari konum hem asgari bağımsız bileşen sayısı, istenen ölçüm belirsizliğine dayalı gerekçeyle önceden yazılır. Bu eşikler otomatik seçilmez.

`templates/protocol.json` içindeki boş alanlar ve `null` destek eşikleri özellikle tamamlanmamıştır. Yazılımın kabul ettiği en küçük eşik 2'dir; **bu, iki olayın bilimsel olarak yeterli olduğu anlamına gelmez.** Örneklem hesabı ve gerekçesi insan araştırmacılar tarafından yapılmalıdır. Hazır 111 kullanılmamış DISFOR penceresindeki yalnız bir kesim, bu kapıyı bile geçemez; buraya hazır dış veri diye taşınmamalıdır.

Model `advanced_v3`, karar eşiği mevcut bundle ile aynı olmalıdır. Farklı model veya yeni eşik değerlendirmek ayrı plan gerektirir. Bu araç karşılaştırmalı yeni model eğitimi gerçekleştirmez.

## 1 Boş çalışma dosyalarını oluştur

```bash
.venv/bin/python external_validation/workflow.py init --out external_validation/calisma_taslagi
```

`calisma_taslagi/protocol.json` dosyasını hocayla tamamlayın. `model_scores_not_inspected` ve `review_evidence_has_no_model_scores` beyanlarını ancak gerçekten sağlandıysa `true` yapın. Koordinatör, bölge/dönem veya adaylar seçilirken model sonuçlarını gördüyse bunu dondurulmadan yapılmış bağımsız seçim olarak sunmayın.

`calisma_taslagi/candidates.json` başlangıçta `[]` içerir. Yalnız gerçekten edinilmiş adayları ekleyin. Alanların açıklaması `candidate_schema.json` içindedir. Gerekli alanlar:

| Alanlar | Anlamı |
|---|---|
| `id`, `source_namespace`, `sample_id` | Yeni kaydın kimliği, gerçek kaynak adı ve kaynağın kalıcı nokta kimliği |
| `target_year`, `lon`, `lat` | İkinci takvim yılı ve WGS84 boylam/enlem |
| `event_namespace`, `event_id` | Aynı gerçek olayı bağlayan kaynak ve kimlik; bilinmiyorsa ikisi de boş metin |
| `partition` | Önceden atanmış `test` veya `development` |
| `evidence_ref` | Model skoru içermeyen kaynak görüntü/kayıt yolu veya inceleme açıklaması |

Aday dosyasında `label`, `score`, `probability` veya başka ek sütun kabul edilmez. Görüntüler otomatik indirilmez; `evidence_ref` içindeki kaynakların erişilebilir ve model skorlarından arındırılmış olması insan tarafından kontrol edilir. Ayrı şablondaki açıklama cümlelerini gerçek aday diye kullanmayın.

DISFOR'dan gelen noktalarda kaynak adını `DISFOR` yazın. Kampanya 1/3 olayları için `DISFOR:dataset:1` / `DISFOR:dataset:3` kullanın. Kampanya 2 örnekleme katmanı olay değildir. Başka kaynaktaki aynı olay biliniyorsa kaynağın eşleştirmesini önceden çözün; farklı bir isim vermek olayı bağımsız yapmaz.

## 2 Kimlik ve coğrafi ayrımı denetle

```bash
.venv/bin/python external_validation/workflow.py audit --candidates external_validation/calisma_taslagi/candidates.json
```

Varsayılan referans `data/disfor/sample_manifest.json` içindeki daha önce kullanılan **bütün 2.213 konumdur**; yalnız eğitim alt kümesi değildir. Aynı kayıt kimliği, aynı DISFOR nokta kimliği, önceki konumlara en fazla 5 km uzaklık veya ortak bilinen kaynak olayı dondurmayı engeller. Yalnız tam 5 km'den büyük mesafe kabul edilir.

Yeni adaylar arasında da yakınlık, aynı kaynak noktası ve aynı olayla bağlı bileşenler oluşturulur. A–B ve B–C yakınsa A–C uzak olsa da aynı bileşendir. Bir bileşen hem `development` hem `test` içerirse süreç durur. Adaylar sessizce elenmez; sebepler raporlanır. Aday listesinin değişmesi sonuçlar görülmeden, gerekçesi kaydedilerek yapılmalıdır.

Bu kontrol bütün mekânsal bağımlılığı veya bilinmeyen olay eşleşmelerini kanıtlayamaz. Başka araştırmalarda kullanılmış veriler, yanlış kaynak adı veya yanlış koordinat gibi durumları koordinatör ayrıca incelemelidir. DISFOR adayları için iddia yalnız `same_source_probe` olabilir; adını değiştirerek dış doğrulama üretilemez.

## 3 Etiketlerden ve model sonuçlarından önce dondur

```bash
.venv/bin/python external_validation/workflow.py freeze --protocol external_validation/calisma_taslagi/protocol.json --candidates external_validation/calisma_taslagi/candidates.json --out external_validation/dondurulmus_v1
.venv/bin/python external_validation/workflow.py verify-freeze --run external_validation/dondurulmus_v1
```

Protokol, adaylar, kullanılan konumlar, grup denetimi ve model dosyalarının SHA-256 bilgileri saklanır. Bundle üyelerinin hash'leri okunup doğrulanır; ağırlıklar çalıştırılmaz. `freeze.json` yerel zaman ve bütünlük kaydıdır. Haricen zaman damgalanmış bir ön kayıt veya araştırmacıların sonuç görmediğinin bağımsız kanıtı değildir.

Dondurulmuş dosyaları düzenlemeyin. Sonradan değişiklik gerekirse yeni sürüm ve değişiklik gerekçesi oluşturun; hangi sonuçların görüldüğünü açıkça kaydedin. Yeni sürüm eski bilgiye maruz kalmayı silmez.

## 4 İki bağımsız yorum al

Koordinatör, her yorumlayıcıya yalnız kendi `packets/reviewer_a.csv` veya `packets/reviewer_b.csv` dosyasını, `packets/OKU_BENI.md` açıklamasını ve dondurulmuş sınıf tanımlarını verir. **Bütün dondurulmuş klasörü dağıtmayın.** Özel kimlik eşleştirmesi koordinatörde kalır. Araç hiçbir dosyayı otomatik göndermez.

Formlarda rastgele inceleme kimliği, konum, hedef yıl ve kanıt yolu vardır; model skoru veya doldurulmuş etiket yoktur. Yorumlayıcılar birbirlerinin kararını ilk okumadan önce görmez. Formları ayrı çalışma kopyalarına kaydetsinler; `packets/` içindeki özgün şablonlar değişmesin.

`label` alanı `0`, `1`, `uncertain`, `exclude`; `confidence` alanı `high`, `medium`, `low` olur. Gerekçe ve saat dilimli gerçek inceleme zamanı zorunludur. Belirsizlik otomatik ormana çevrilmez. Kişi adları kimlik doğrulama hesabı değildir; bağımsız okuma beyanının sorumluluğu insanlardadır.

## 5 Uyuşmazlıkları çöz ve desteği kontrol et

Aşağıdaki `yanit_a.csv` ve `yanit_b.csv`, yorumlayıcıların gerçek tamamlanmış dosyalarıdır; henüz paket içinde yoktur.

```bash
.venv/bin/python external_validation/workflow.py reconcile --run external_validation/dondurulmus_v1 --a external_validation/yanit_a.csv --b external_validation/yanit_b.csv --out external_validation/uzlasma_v1
```

Aynı yüksek güvenli kararlar birleşir. Farklı veya belirsiz kararlar, düşük güven ve görev dışı durumlar üçüncü yorumlayıcıya gider. `disagreements.json` iki gerekçeyi gösterir; model skoru yine yoktur. Üçüncü kişi `adjudication_template.csv` dosyasının kopyasını doldurur. Karar hâlâ belirsizse uygun dışlama kuralı veya ek kanıt gerekir; yapay kesinlik üretilmez.

```bash
.venv/bin/python external_validation/workflow.py finalize --run external_validation/dondurulmus_v1 --a external_validation/yanit_a.csv --b external_validation/yanit_b.csv --adjudication external_validation/uzlasma_yaniti.csv --out external_validation/etiket_sonucu_v1
```

Uyuşmazlık yoksa `--adjudication` seçeneğini kullanmayın. `labels.json` kabul/dışlama kararlarını ve grup kimliklerini, `readiness.json` test kümesinin sınıf ve bileşen desteğini saklar. Development etiketleri test desteğine sayılmaz. Kesim etiketli bir test adayının olay kimliği bilinmiyorsa hazırlık tamam sayılmaz.

`insufficient_support`: eşikler karşılanmıyor veya pozitif olay kimliği çözülmedi. Sonuçları görüp eşiği azaltmayın. `annotation_support_ready`: yalnız etiketleme ve önceden tanımlanmış destek kapıları geçti. Bu ifade dış saha başarımı değildir; adayların gerçek 24×10 model girdileri, DN işleme uyumu ve yıllık en az altı gözlenmiş ayı ayrıca doğrulanmalıdır. Bu araç bunları veya model tahminlerini üretmez. Sonraki değerlendirme, dondurulmuş bundle/eşik ve dokunulmamış testte ayrıca yürütülür.

## Testler ve mevcut durum

```bash
.venv/bin/python -m unittest discover -s external_validation/tests -v
```

Sentetik fixture testleri çakışma, kör form, dosya değişikliği, bağımsız yorum, üçüncü uzlaşma, belirsiz etiket ve yetersiz sınıf/olay desteğini sınar. Son çalıştırma `verification.json` ve `tests.log` içindedir. Hiç gerçek dış veri, insan etiketleme sonucu veya dış doğrulama skoru oluşturulmadı.
