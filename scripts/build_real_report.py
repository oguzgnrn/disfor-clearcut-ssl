"""Generate the final offline report and paper-style results from recorded real runs."""
from pathlib import Path
import json,base64,html,re
import numpy as np
root=Path(__file__).resolve().parents[1]
r=json.loads((root/'reports/real_experiment/results.json').read_text());a=json.loads((root/'reports/real_analysis.json').read_text());prep=json.loads((root/'reports/disfor_preparation.json').read_text());card=a['selection']
d=dict(np.load(root/'data/processed/real_series.npz',allow_pickle=False));pred=json.loads((root/'reports/real_experiment/selected_test_predictions.json').read_text());lookup={v:i for i,v in enumerate(d['ids'])};manifest={v['id']:v for v in json.loads((root/'data/disfor/sample_manifest.json').read_text())}
examples=[]
for k,sid in enumerate(pred['ids']):
 i=lookup[sid];v=manifest[sid]
 examples.append(dict(id=sid,year=v['year'],lon=v['lon'],lat=v['lat'],truth=int(d['y'][i]),prediction=pred['predictions'][k],score=pred['probabilities'][k][1],
  series=[[float(x) if np.isfinite(x) else None for x in d['x'][i,:,band]] for band in [2,6,9]]))
def image(path):return 'data:image/png;base64,'+base64.b64encode((root/path).read_bytes()).decode()
rows=[]
for f in [.05,.1,.2,1.]:
 rs=[v for v in r['summary'] if v['label_fraction']==f]
 rows.append([f'%{int(100*f)}']+[f'{v["macro_f1_mean"]:.3f} ± {v["macro_f1_std"]:.3f}' for v in rs])
metric_rows=''.join('<tr>'+''.join('<td>'+x+'</td>' for x in row)+'</tr>' for row in rows)
ci=a['ssl_minus_supervised_at_20_percent']['bootstrap_95_interval']
md=f'''# Orman-SSL: gerçek Sentinel-2 verisinde kesim sınıflandırması

## Tamamlanan araştırma MVP'si

Bu sürüm gerçek etiketli veriyle eğitilmiş modeller, kilitli coğrafi test, etiket verimliliği karşılaştırması, gözlem kaybı deneyi, hata atlası, coğrafi tahmin dosyası ve yeni girdide çalışan tahmin komutu içerir. Tamamlanmış bir saha ürünü veya kabul edilmiş makale iddiası değildir.

## Kısa araştırma özeti

DISFOR'un yüksek güvenli yorum etiketlerinden **{prep['n']} gerçek 24 aylık Sentinel-2 serisi** hazırlandı. Girdi 10 spektral DN bandının aylık medyanıdır. Görev, ikinci yılda kesim gerçekleşen orman ile iki yıl boyunca yorumlanmış bozulmasız ormanı ayırmaktır. Yakın noktalar ve aynı olay grupları birleştirilerek eğitim/validation/test coğrafyaları arasında en az 5 km mesafe bırakıldı. Testte 448 bozulmamış ve 38 kesim örneği bulunur; kesim örnekleri 20 bağımsız mekânsal gruba dağılır.

RF, sıfırdan Transformer ve maskeli ön eğitimli Transformer üç seed ve dört eğitim etiketi bütçesinde karşılaştırıldı. Tam eğitim etiketiyle Transformer ortalama macro-F1=0,877 elde etti. %20 etikette RF=0,811; supervised Transformer=0,490; SSL Transformer=0,484. Bu kurulumda az etiketli SSL üstünlüğü gözlenmedi. Sonuç, SSL yaklaşımının genel olarak işe yaramadığı anlamına gelmez; model/ön eğitim seçimi, sınıf dengesizliği ve örnek çeşitliliğiyle sınırlıdır.

## Veri ve örnekleme

Kaynak: [DISFOR, JR-DIGITAL](https://huggingface.co/datasets/JR-DIGITAL/DISFOR), sabit revision `2562332e35c94c2339aeb341ffaed2a99faae7d6`, EUPL-1.2. İndirilen tabloda 3.822 nokta vardır; kaynak kartındaki 3.823 sayısı yerine dosyadan ölçülen sayı kullanıldı. Kaynak zaman serileri ve yorumlanmış segmentler birlikte sağlanır; bu etiketler bizim topladığımız arazi ölçümleri değildir. Kaynağın yayınlanan split'i kullanılmadı; bu proje özel bir coğrafi protokoldür, resmi benchmark sonucu değildir.

Yüksek güvenli örnekler, 2018-2023 hedef yılları, her yıl en az altı açık gözlem ayı. Kesim penceresinde önceki takvim yılı bozulmamış orman olmalı; iki yılda yalnızca bir bozulma olayı bulunmalı. Negatif pencereyi 110 etiketi bütünüyle örtmeli. Bir noktadan tek pencere kullanıldı; pencereler olayın kesin günü etrafında merkezlenmedi. Etiket veya olay günü model girdisi değildir.

İlk üç sınıflı veri hazırlığında testte bir yangın örneği kaldığı görüldü. Skorlar okunmadan ana görev kesim/bozulmamış orman olarak sınırlandı; yangın performansı iddia edilmedi. Seçim kararları `docs/REAL_PROTOCOL.md` ve hazırlama kodunda kayıtlıdır.

## Yöntem

10 bant: B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12. Kaynak DN değerleri korunur; belgelenmemiş ofset uygulanmaz. Bulut temizliği için source clear AND SCL 4/5 kullanılır. Eksik aylar NaN ve gözlem maskesiyle saklanır. Standardizasyon yalnızca eğitim gözlemlerinden hesaplanır. Grup kuralı 5 km komşuluk bağlı bileşenleri ve aynı kaynak hasar poligonu/fırtınasıdır; örnekleme strata'sı olay kabul edilmez.

Transformer: bir encoder, 32 gizli boyut, dört attention head, dropout=0,1. Değer, maske ve göreli takvim bilgisi girişe verilir. SSL: gözlenen hücrelerin %30'unun rekonstrüksiyonu; yalnızca eğitim coğrafyası, 30 epoch. Fine-tune: 25 epoch; validation macro-F1 checkpoint seçimi. RF: 200 ağaç, min_samples_leaf=2, balanced ağırlık ve zaman özetleri. Fine-tune çapraz entropisi bu sabit ana deneyde sınıf ağırlıksızdır; bu, az etiket sonuçları yorumlanırken dikkate alınır.

Her bütçede yöntemler aynı eğitim etiketlerini kullanır. Eğitim oranları validation maliyetini içermez. Kümeler: 1.266 eğitim, 461 validation, 486 test. Tek coğrafi ayrım üzerinde seed 7/17/27 kullanıldı. Test verisi ön eğitim, standardizasyon veya checkpoint seçimine girmedi. SSL ek hesaplama kullanır; eşit toplam hesaplama karşılaştırması yapılmadı.

## Ölçülmüş sonuçlar

| Eğitim etiketi | Random Forest | Transformer | SSL Transformer |
|---|---:|---:|---:|
'''+''.join('| '+' | '.join(row)+' |\n' for row in rows)+f'''
Değerler test macro-F1 ortalama ± seed standart sapmasıdır. Seed standart sapması güven aralığı değildir. %20 etikette SSL-supervised farkı {a['ssl_minus_supervised_at_20_percent']['mean']:.4f}; 1.000 eşleştirilmiş test grubu bootstrap tekrarında %95 aralık [{ci[0]:.4f}, {ci[1]:.4f}]. Aralık sıfırı kapsar. Bu aralık tek veri hazırlama ve coğrafi ayrım koşuluna bağlıdır.

## Kullanıma ayrılan model

Yöntem, %100 eğitim etiketi koşulundaki ortalama validation macro-F1 ile seçildi; seed=7 önceden sabitlendi. Seçilen yöntem {card['method']}; model `models/model.pt`. Bu tek checkpoint'in test macro-F1 değeri **{a['selected_test_macro_f1']:.3f}**. Bu sayı, üç seed ortalaması 0,877 ile karıştırılmamalı.

Confusion matrix, satırlar gerçek / sütunlar tahmin; sıra bozulmamış-kesim:

```
442    6
 12   26
```

Kesim precision=26/32=0,8125; recall=26/38≈0,6842. Kaçırılan 12 kesim, sistemin sınırını gösterir. Olasılıklar kalibre edilmiş güven değildir. Yeni girdi aynı bant sırası, DN tanımı ve 24 aylık takvim sözleşmesini izlemeli. Uygun olmayan kaliteyi model çıktısındaki `quality_eligible` alanı işaretler.

## Eksik gözlem ve hata analizi

%20 etiket modelleri yeniden ayarlanmadan test aylarına %0/%20/%40/%60 ek kayıp uygulandı. Yöntemler aynı seed'e ait aynı maskeleri görür. Sonuçlar `figures/real_robustness.png` ve `reports/real_analysis.json` içinde. Bu kontrollü silme gerçek bulut oluşumunun mevsimsel dağılımını bütünüyle modellemez.

Hata atlası DN eğrilerini yanlış ve doğru örneklerle gösterir. `reports/real_experiment/test_predictions.geojson` yalnızca test noktalarının gerçek koordinat, etiket, tahmin ve skorlarını içerir. Bu noktalar arasında sürekli raster tahmin yapılmış değildir.

## Sonuç ve savunulabilir katkı

Tamamlanan çıktı, gerçek Sentinel-2 verisine dayalı tekrarlanabilir bir karşılaştırma ve çalışan çıkarım aracıdır. Basit RF'nin az etikette güçlü olduğu; uygulanan SSL ön eğitiminin mevcut protokolde üstünlük sağlamadığı görülmüştür. Bu olumsuz bulgu saklanmaz. Nokta örneklemesi, kampanya/coğrafya farkları, negatiflerin fazlalığı, yalnızca bir coğrafi ayrım ve kaynak DN işleme geçmişi genelleme sınırlarıdır.

Gerçek Sentinel-1 füzyonu, Türkiye'de bağımsız saha doğrulaması, yangın/hastalık türlerinin güvenilir değerlendirmesi ve yayın yeniliğinin kanıtı bu tamamlanmış S2 kesim MVP'sinin kapsamı dışındadır. Bunlar eldeki sonuçların var olmadığı anlamına gelmez; hangi problemi gerçekten çözdüğünü tanımlar.

## Tekrar çalıştırma

```bash
.venv/bin/python scripts/prepare_disfor.py
PYTHONPATH=src .venv/bin/python -m orman_ssl.experiment --data data/processed/real_series.npz --out reports/real_experiment
.venv/bin/python scripts/analyze_real.py
PYTHONPATH=src .venv/bin/python -m orman_ssl.predict --checkpoint models/model.pt --data data/processed/test_inference.npz --out reports/inference_cli.json
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_real_report.py
```

Ham veriyi yeniden indirme: `scripts/download_disfor.py`. Veri lisansı `data/disfor/LICENSE`, hash kayıtları `data/disfor/downloads.json`. Kaynak kod, ham/işlenmiş veri, modeller ve raporlar pakette mevcuttur.
'''
(root/'docs/GERCEK_DENEY_RAPORU.md').write_text(md)
# Reuse the already-reviewed report typography; this is a portable local report.
legacy=root/'reports/demo_v1.html'
if not legacy.exists():legacy.write_text((root/'reports/demo.html').read_text())
css=re.search(r'<style>(.*?)</style>',legacy.read_text(),re.S).group(1)
css+=' select{width:100%;padding:12px;border:1px solid #a6b9aa;border-radius:8px;background:white;color:#17392f;font:inherit}#series{background:white;image-rendering:auto;height:310px;max-height:none}.tagrow{display:flex;gap:12px;flex-wrap:wrap}.tagrow b{background:#e8ede4;padding:5px 12px;border-radius:6px}'
page='''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Orman-SSL • Gerçek veri sonuçları</title><style>__CSS__</style>
<header><div class="eyebrow">Mehmet Oğuz Güneren · Sürüm 2 · Gerçek veri deneyi tamamlandı</div><h1>Gerçek veri.<br>Ölçülmüş sonuç.</h1><p>Sentinel-2 zaman serilerinden orman kesimi sınıflandırması. Eğitim, coğrafi test, hata incelemesi ve kullanılabilir model aynı pakette.</p><span class="badge">2.213 gerçek seri</span><span class="badge">En az 5 km ayrım</span><span class="badge">Çevrimdışı rapor</span></header>
<main><nav><a href="#sonuc">Sonuç</a><a href="#ornek">Modeli incele</a><a href="#deney">Karşılaştırma</a><a href="#yontem">Yöntem ve kullanım</a><a href="demo_v1.html">İlk CBS incelemesi</a></nav>
<section id="sonuc"><div class="num">01 / Tamamlanan gerçek deney</div><h2>Kesimi ayırabilen, sınırları ölçülmüş bir model.</h2><div class="cards"><div class="card"><strong>0,861</strong>Seçilen modelin test macro-F1'i<br><small>Transformer · sabit seed 7</small></div><div class="card"><strong>486</strong>Coğrafi test örneği<br><small>448 bozulmamış / 38 kesim</small></div><div class="card"><strong>36</strong>Gerçek veri deney koşulu<br><small>3 yöntem × 4 bütçe × 3 seed</small></div></div><p class="lead">Tam etiketle Transformer güçlü. Az etikette Random Forest önde. Bu kurulumda self-supervised ön eğitim üstünlük sağlamadı.</p><p class="note">Model yöntemini validation sonuçlarıyla seçtik; testte en iyi seed'i seçmedik. Üç seed'in tam etiketli Transformer ortalaması 0,877; dağıtılan tek checkpoint'in değeri 0,861. Bunlar farklı ölçümlerdir.</p><div class="split"><div><img src="__CM__" alt="Gerçek test confusion matrix"></div><div><h3>Hata sayıları</h3><p>26 kesim doğru bulundu; 12 kesim kaçırıldı. Bozulmamış 448 örneğin 6'sı yanlışlıkla kesim olarak işaretlendi.</p><p>Kesim precision: <b>%81,3</b><br>Kesim recall: <b>%68,4</b></p><p class="note caution">Bu bir 24 aylık geçmiş dönem sınıflandırmasıdır. Erken yangın uyarısı, Türkiye için doğrulanmış saha sistemi veya bütün bozulma türlerini ayıran ürün değildir.</p></div></div></section>
<section id="ornek"><div class="num">02 / Modeli örnek üzerinde incele</div><h2>Doğru kararları da, hataları da aç.</h2><p>Buradaki 486 örneğin tamamı test kümesindedir. Gösterilen sonuçlar kaydedilmiş model tahminleridir; seçimi değiştirmek modeli yeniden eğitmez.</p><div class="split"><div><label for="filter">Örnek filtresi</label><select id="filter"><option value="all">Tüm test örnekleri</option><option value="wrong">Yalnız hatalı tahminler</option><option value="missed">Kaçırılan kesimler</option><option value="cut">Gerçek kesim örnekleri</option></select><label for="sample" style="margin-top:18px">İncelenecek örnek</label><select id="sample"></select><p id="sampleInfo"></p><div class="tagrow"><b id="truth"></b><b id="prediction"></b></div><p id="score"></p><p class="muted">Skor, kalibre edilmiş güven değildir. Eğriler kaynağın DN birimindedir; eksik aylar çizgide boşluk olarak kalır.</p></div><div><canvas id="series" width="720" height="380" aria-label="24 aylık B04 B08 B12 uydu bandı eğrileri"></canvas><div class="legend"><i style="background:#c65338"></i>B04 <i style="background:#347a4c"></i>B08 <i style="background:#7755a0"></i>B12</div></div></div></section>
<section id="deney"><div class="num">03 / Saklanmayan karşılaştırma</div><span class="badge real">GERÇEK DISFOR VERİSİ</span><h2>Etiket bütçesi sonucu değiştiriyor.</h2><img src="__CURVE__" alt="Gerçek veride etiket verimliliği grafiği"><div class="table"><table><thead><tr><th>Eğitim etiketi</th><th>Random Forest</th><th>Transformer</th><th>SSL Transformer</th></tr></thead><tbody>__TABLE__</tbody></table></div><p class="muted">Macro-F1 ortalama ± seed standart sapması. 461 validation etiketi eğitim yüzdelerine ek maliyettir.</p><p class="note">%20 etikette SSL − supervised farkı −0,0057. 1.000 eşleştirilmiş mekânsal grup bootstrap tekrarında %95 aralık [−0,0245, +0,0030]. Bu koşulda SSL lehine tutarlı katkı gösterilemedi.</p><img src="__ROBUST__" alt="Ek gözlem kaybında modellerin başarımı"><p class="muted">Modeller yeniden ayarlanmadı. Yöntemlere aynı eksik-ay maskeleri uygulandı. Doğal bulut örüntüleri bu yapay silmeyle tamamen temsil edilmez.</p></section>
<section id="yontem"><div class="num">04 / Tekrar üret ve kullan</div><h2>Kod, veri, ağırlık ve çıktı hazır.</h2><div class="split"><div><h3>Veri sözleşmesi</h3><ul><li>24 aylık seri, 10 Sentinel-2 DN bandı.</li><li>Önceki yıl bozulmamış orman; ikinci yılda kesim.</li><li>Yüksek güvenli kaynak yorum etiketleri.</li><li>5 km komşuluk ve aynı olay grupları ayrılmaz.</li><li>Normalizasyon ve SSL yalnızca eğitim bölümünde.</li></ul></div><div><h3>Yeni girdide tahmin</h3><p><code>models/model.pt</code> kaydedilmiş modeldir. <code>orman_ssl.predict</code> komutu etiketsiz NPZ girdisinden sınıf ve skor üretir.</p><p>Hazır örnek: <code>data/processed/test_inference.npz</code>. Tam komutlar README'de. QGIS için <code>test_predictions.geojson</code> sağlandı.</p></div></div><h3>Açık sınırlılıklar</h3><p>Tek coğrafi ayrım; testte 38 kesim ve 20 pozitif mekânsal grup; yorumlanmış etiketler; sınıf dengesizliği; gözlem ve veri toplama kampanyalarının etkisi. Gerçek SAR füzyonu veya Türkiye dış doğrulaması yapılmış değildir. Yangın örnekleri yeterli bağımsız test desteği sağlamadığından ana göreve katılmadı.</p><p><a href="../docs/GERCEK_DENEY_RAPORU.md">Ayrıntılı deney raporu</a> · <a href="../output/pdf/Orman_SSL_Toplanti_Dosyasi.pdf">Güncel toplantı PDF'si</a> · <a href="real_experiment/test_predictions.geojson">Test tahminleri / GeoJSON</a></p></section>
<footer>Veri: <a href="https://huggingface.co/datasets/JR-DIGITAL/DISFOR">JR-DIGITAL DISFOR</a>, sabit revision 2562332 · EUPL-1.2. Yapay zekâ yardımıyla hazırlanmış araştırma MVP'si. Bu sayfa internetsiz çalışır.</footer></main>
<script>const examples=__EXAMPLES__;const filter=document.getElementById('filter'),select=document.getElementById('sample');const names=['Bozulmamış orman','Kesim'];function render(){const e=examples[Number(select.value)];document.getElementById('sampleInfo').textContent=e.id+' · hedef yıl '+e.year+' · '+e.lat.toFixed(4)+', '+e.lon.toFixed(4);document.getElementById('truth').textContent='Kaynak etiketi: '+names[e.truth];document.getElementById('prediction').textContent='Tahmin: '+names[e.prediction];document.getElementById('score').textContent='Kesim skoru: '+e.score.toFixed(3);const c=document.getElementById('series'),x=c.getContext('2d');x.clearRect(0,0,c.width,c.height);x.fillStyle='white';x.fillRect(0,0,c.width,c.height);const all=e.series.flat().filter(v=>v!==null),lo=0,hi=Math.max(1000,...all)*1.1,L=70,R=25,T=25,B=55;const w=c.width-L-R,h=c.height-T-B;x.font='16px system-ui';x.fillStyle='#53665b';x.strokeStyle='#d4ddd5';for(let i=0;i<=4;i++){const yy=T+h*i/4;x.beginPath();x.moveTo(L,yy);x.lineTo(L+w,yy);x.stroke();x.fillText(Math.round(hi*(1-i/4)),8,yy+5);}for(let i=0;i<24;i+=3)x.fillText(i+1,L+w*i/23-5,T+h+25);x.fillText('Ay (24 aylık pencere)',L+150,c.height-8);e.series.forEach((values,k)=>{x.strokeStyle=['#c65338','#347a4c','#7755a0'][k];x.lineWidth=2.5;x.beginPath();let active=false;values.forEach((v,i)=>{if(v===null){active=false;return;}const px=L+w*i/23,py=T+h*(1-v/hi);if(active)x.lineTo(px,py);else x.moveTo(px,py);active=true;});x.stroke();});}function refresh(){select.replaceChildren();examples.forEach((e,i)=>{const f=filter.value;if(f==='wrong'&&e.truth===e.prediction||f==='missed'&&!(e.truth===1&&e.prediction===0)||f==='cut'&&e.truth!==1)return;const o=document.createElement('option');o.value=i;o.textContent=e.id+' · '+(e.truth===e.prediction?'doğru':'HATA');select.append(o);});render();}filter.addEventListener('change',refresh);select.addEventListener('change',render);refresh();</script></html>'''
for key,val in {'__CSS__':css,'__CM__':image('figures/real_confusion.png'),'__CURVE__':image('reports/real_experiment/label_efficiency.png'),'__TABLE__':metric_rows,'__ROBUST__':image('figures/real_robustness.png'),'__EXAMPLES__':json.dumps(examples,separators=(',',':'))}.items():page=page.replace(key,val)
(root/'reports/demo.html').write_text(page)
print('Updated offline real-data demo and research report.')
