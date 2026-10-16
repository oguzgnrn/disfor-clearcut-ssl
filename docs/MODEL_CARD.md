# Orman-SSL model kartı

**Dosya:** `models/model.pt` · Transformer · seed 7 · 24 ay × 10 S2 DN bandı.

## Amaç

İki yıllık geriye dönük zaman serisinde bozulmamış orman / ikinci yılda kesim ayrımı. Sınıflar kaynak görüntü yorumuna dayanır. Operasyonel alarm veya bütün dünyada orman bozulması nedeni çıkarımı değildir.

## Eğitim ve seçim

DISFOR sabit revision 2562332e35c94c2339aeb341ffaed2a99faae7d6. 1.266 train, 461 validation, 486 test. 5 km komşuluk ve olay bileşenleri korunur. Normalizasyon train-only. Yöntem üç seed'in ortalama validation macro-F1'iyle seçildi; çıktı seed=7'dir. Test skorundan seed seçilmedi.

Mimari tek Transformer encoder, hidden=32, heads=4, dropout=0,1. Bu seçilen model sıfırdan supervised eğitildi. SSL modelini sırf proje başlığında SSL var diye seçmedik; karşılaştırma sonuçları tercih gerekçesidir.

## Ölçüm

Seçilen model: test macro-F1 0,861; kesim precision 0,8125, recall 0,6842. Confusion matrix [[442,6],[12,26]]. 38 pozitif örnek 20 mekânsal gruptadır. Üç seed ortalaması farklı bir ölçümdür: supervised Transformer, tam etiketle 0,877 ± 0,019.

## Sınırlar

Tek coğrafi ayrım, dengesiz sınıflar ve kaynak kampanyalarına bağlı örneklem. Kaynak etiketler bağımsız yeni saha çalışmamız değildir. Hastalık, yangın ve SAR füzyonu bu modelin sınıfları/girdileri değildir. Türkiye'de bağımsız doğrulama yok. Olasılıklar kalibre değil; kullanım öncesi hedef bölgede doğrulama gerekir.

## Kullanım

`PYTHONPATH=src .venv/bin/python -m orman_ssl.predict --checkpoint models/model.pt --data data/processed/test_inference.npz --out reports/my_predictions.json`

Veri ve model metadata'sı bant sırasını denetler; days, observed ve x şekilleri doğrulanır. Kalite dışı seriler çıktı bayrağıyla işaretlenir. GeoJSON yalnızca test noktalarının tahminidir; bir tahmin rasterı değildir.

## Kaynak hakları

Veri [JR-DIGITAL DISFOR](https://huggingface.co/datasets/JR-DIGITAL/DISFOR), EUPL-1.2; lisans ve atıf bilgileri pakette korunur. Yayımlama/dağıtım kararı öncesinde kaynak verinin lisans yükümlülükleri gözden geçirilmelidir. Yeni kodun lisansı proje sahiplerince seçilecektir.
