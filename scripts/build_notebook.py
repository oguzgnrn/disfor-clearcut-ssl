"""Generate the end-to-end project notebook (Turkish explanations, every code path, executed outputs)."""
import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'TESLIM_2026-10-18'
OUT.mkdir(exist_ok=True)
nb = nbf.v4.new_notebook()
cells = []
def md(s): cells.append(nbf.v4.new_markdown_cell(s.strip()))
def code(s): cells.append(nbf.v4.new_code_cell(s.strip()))

md(r"""
# Orman-SSL: uçtan uca proje defteri

**Mehmet Oğuz Güneren · Danışman: Dr. Nida Kumbasar (TÜBİTAK BİLGEM) · 18 Ekim 2026**

Bu defter projenin **bütün kod yolunu** tek yerde, sırayla ve çalıştırılmış çıktılarıyla gösterir:

1. Veri: DISFOR kaynak tablolarından 24 ay × 10 bant model girdisine
2. Dürüst sınav: mekânsal bileşenler ve 5 coğrafi kat (spatial cross-validation)
3. Etiket bütçesi (label budget) alt kümeleri
4. Modeller: Random Forest, Temporal CNN, Transformer, masked-reconstruction SSL Transformer, step-matched kontrol
5. Canlı demo eğitimi (bir kat, bir seed) ve kayıtlı koşuyla karşılaştırma
6. Ana deney paper_v4: 180 koşunun tabloları, bootstrap aralıkları, şekiller
7. Uzantılar: paper_v5 (gruplama yarıçapı) ve paper_v6 (etiket eğrisi)
8. Keşif: Presto frozen probe
9. Ürün modeli advanced_v3: 10 üyeli ensemble ile gerçek çıkarım
10. Doğrulama (verify scripts, unit tests) ve tekrar üretim komutları

**Nasıl çalıştırılır:** Proje kökünde `.venv` kuruluysa `.venv/bin/python -m jupyter lab TESLIM_2026-10-18/Orman_SSL_Proje_Defteri.ipynb`. Bütün hücreler yukarıdan aşağı çalışır. Tam deneyi (180 + 75 + 225 koşu) yeniden eğitmek saatler sürer; bu defter kayıtlı koşuları okuyup **her tabloyu yeniden hesaplar**, eğitimi ise bir kat/seed için canlı gösterir. Tamamını yeniden koşmak için 10. bölümdeki komutlar kullanılır.

Projedeki asıl kod `src/orman_ssl/` ve `scripts/` altındadır; bu defter o kodu **içe aktarır ve kaynağını gösterir**, kopyalamaz. Böylece defterdeki kod ile deneyleri üreten kod birebir aynıdır.
""")

code(r"""
# 0. Ortam ve yollar
import sys, json, math, time, inspect, platform, textwrap
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.display import display, Image, Markdown

ROOT = Path.cwd().resolve()
if not (ROOT / 'src/orman_ssl').exists(): ROOT = ROOT.parent     # defter TESLIM klasöründen açıldıysa
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'scripts'))
import torch, sklearn
import orman_ssl.advanced as adv
from orman_ssl.experiment import subset, normalize, rf_features
pd.set_option('display.width', 160); pd.set_option('display.max_columns', 30); pd.set_option('display.precision', 4)
print('Proje kökü :', ROOT)
print('Python', platform.python_version(), '| torch', torch.__version__, '| sklearn', sklearn.__version__, '| numpy', np.__version__)
def show_source(obj, title=None):
    display(Markdown(f'**Kaynak: `{title or obj.__name__}`**'))
    print(inspect.getsource(obj))
""")

md(r"""
## 1. Veri: DISFOR'dan model girdisine

Kaynak: [JR-DIGITAL/DISFOR](https://huggingface.co/datasets/JR-DIGITAL/DISFOR), sabit revision `2562332e…`, EUPL-1.2. Ham tablolar `data/disfor/*.parquet`. Hazırlama kodu `scripts/prepare_disfor.py`; bu kod her konum için **iki tam takvim yılı** seçer, ay içindeki temiz gözlemlerin (kaynak `clear` bayrağı **ve** SCL 4/5) medyanını alır, boş ayları `observed=False` ile işaretler, her yılda ≥ 6 gözlenmiş ay ister ve 5 km + ortak olay bağlarıyla mekânsal bileşen kurar. Çıktı `data/processed/real_series.npz`.
""")
code(r"""
d = dict(np.load(ROOT / 'data/processed/real_series.npz', allow_pickle=False))
meta = json.loads(str(d['metadata']))
print({k: (v.shape, str(v.dtype)) for k, v in d.items() if k != 'metadata'})
print('Sınıflar:', meta['classes'], '| Bantlar:', meta['channels'])
print('Konum sayısı:', len(d['y']), '| orman:', int((d['y']==0).sum()), '| kesim:', int((d['y']==1).sum()), '| mekânsal bileşen:', len(np.unique(d['groups'])))
prep = json.loads((ROOT / 'reports/disfor_preparation.json').read_text())
tab1 = pd.DataFrame([
    ['Downloaded sample table', 3822],
    ['− not high-confidence', -prep['rejected']['not_high_confidence']],
    ['− no unambiguous two-year window', -prep['rejected']['no_unambiguous_two_year_window']],
    ['− insufficient clear months', -prep['rejected']['insufficient_clear_months']],
    ['− wildfire excluded from binary task', -prep['rejected']['wildfire_excluded_from_primary_task']],
    ['Retained locations', prep['n']],
], columns=['Aşama (Table 1)', 'Konum'])
display(tab1)
""")
code(r"""
# Örnek manifesti: her konumun kimliği, yılı, etiketi, koordinatı, kaynak kampanyası
manifest = pd.DataFrame(json.loads((ROOT / 'data/disfor/sample_manifest.json').read_text()))
display(manifest.head(8))
display(manifest.groupby(['dataset','label']).size().unstack(fill_value=0).rename(columns={0:'orman',1:'kesim'}).rename_axis('kampanya'))
print('Hedef yıl dağılımı:'); display(manifest.groupby(['year','label']).size().unstack(fill_value=0).rename(columns={0:'orman',1:'kesim'}))
""")
code(r"""
# Hazırlama betiğinin tamamı (deneyi üreten kod; burada yalnız gösteriliyor, çalıştırılmıyor)
print((ROOT / 'scripts/prepare_disfor.py').read_text())
""")
md("""
### 1.1 Bir orman ve bir kesim serisi
NDVI = (B08 − B04)/(B08 + B04). Gri dikey bantlar gözlem olmayan (bulutlu) aylardır; model bunları doldurmaz, maskeden görür.
""")
code(r"""
ids = list(d['ids'])
i_cut = ids.index('disfor-1733-2019') if 'disfor-1733-2019' in ids else int(np.where(d['y']==1)[0][0])
i_for = int(np.where(d['y']==0)[0][5])
fig, axes = plt.subplots(1, 2, figsize=(12, 3.6), sharey=True)
for ax, i, name in [(axes[0], i_for, 'Bozulmamış orman'), (axes[1], i_cut, 'Kesim (2. yılda)')]:
    x = d['x'][i]; m = d['observed'][i].any(-1)
    ndvi = (x[:,6]-x[:,2])/np.maximum(x[:,6]+x[:,2], 1)
    months = np.arange(1, 25)
    for t in np.where(~m)[0]: ax.axvspan(t+0.5, t+1.5, color='#cccccc', alpha=.5)
    ax.plot(months[m], ndvi[m], 'o-', color='#1a8fa6' if name.startswith('Boz') else '#c0583f')
    ax.axvline(12.5, color='k', lw=.8, ls='--'); ax.set_title(f'{name}: {ids[i]}'); ax.set_xlabel('ay'); ax.set_xticks([1,6,12,18,24])
axes[0].set_ylabel('NDVI'); plt.tight_layout(); plt.savefig(ROOT/'TESLIM_2026-10-18/figures/nb_ornek_seriler.png', dpi=150); plt.show()
""")

md(r"""
## 2. Dürüst sınav: mekânsal bileşenler ve 5 coğrafi kat

Komşu pikseller neredeyse aynı seridir; rastgele bölme yapılırsa model komşusunu ezberler ve skor şişer (**spatial leakage**). Çözüm: 5 km içindeki konumlar ve aynı kaynak olayı paylaşan konumlar (kampanya 1 ve 3) bir çizgede birleştirilir; **connected component**'lar bölünmez; `StratifiedGroupKFold(5, shuffle=True, random_state=4192026)` ile beş kata dağıtılır. Aşağıdaki fonksiyon paper_v5'teki `component_groups`; 5 km için donmuş `d['groups']` ile birebir aynı sonucu verdiği doğrulanır.
""")
code(r"""
from scientific_v5 import component_groups
show_source(component_groups)
raw_manifest = json.loads((ROOT / 'data/disfor/sample_manifest.json').read_text()); by_id = {r['id']: r for r in raw_manifest}
groups5 = component_groups([by_id[i] for i in ids], 5)   # konum sırası real_series.npz ile aynı olmalı
print('5 km bileşenleri donmuş gruplarla aynı mı?', bool(np.array_equal(groups5, d['groups'])), '| bileşen sayısı:', len(np.unique(groups5)))
sizes = np.unique(d['groups'], return_counts=True)[1]
print('Bileşen büyüklüğü: medyan', np.median(sizes), '| en büyük', sizes.max(), '| kesim içeren bileşen', len(np.unique(d['groups'][d['y']==1])))
""")
code(r"""
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.neighbors import BallTree
folds = json.loads((ROOT / 'experiments/paper_v4/folds.json').read_text())
coords = np.deg2rad(manifest.set_index('id').loc[ids, ['lat','lon']].values)
rows = []
for f in folds:
    tr, te = np.array(f['train_indices']), np.array(f['test_indices'])
    assert not (set(d['groups'][tr]) & set(d['groups'][te])), 'bileşen sızıntısı'
    nearest = BallTree(coords[tr], metric='haversine').query(coords[te], k=1)[0].min() * 6371.0088
    rows.append(dict(fold=f['fold']+1, train=len(tr), test=len(te), test_forest=int((d['y'][te]==0).sum()), test_cut=int((d['y'][te]==1).sum()),
                     test_components=len(np.unique(d['groups'][te])), nearest_train_km=round(float(nearest), 4)))
tab2 = pd.DataFrame(rows); display(tab2)
# Yeniden üret: aynı seed ile aynı katlar çıkıyor mu?
cv = StratifiedGroupKFold(5, shuffle=True, random_state=4192026)
same = all(list(te) == f['test_indices'] for (tr, te), f in zip(cv.split(d['x'], d['y'], d['groups']), folds))
print('Katlar aynı seed ile yeniden üretildi mi?', same)
""")

md(r"""
## 3. Etiket bütçesi (label budget)

Her katın eğitim bölümünde yalnız bir kısım etiketli sayılır. `subset(y, train, fraction, seed)` sınıf içinde sabit rastgele sıra kullanır, `ceil(oran × sınıf sayısı)` örnek alır; bütçeler iç içedir (%5 ⊂ %10 ⊂ %20 ⊂ %50). Bütün yöntemler aynı etiketli kimlikleri görür. Etiketsiz kalan serilerin görüntüleri normalizasyonda herkes, ön eğitimde yalnız SSL tarafından kullanılır.
""")
code(r"""
show_source(subset)
tr0 = np.array(folds[0]['train_indices'])
tab = []
for b in [.05, .1, .2, .5, 1.]:
    lab = subset(d['y'], tr0, b, 7)
    tab.append(dict(budget=f'{int(b*100)}%', n_labeled=len(lab), labeled_forest=int((d['y'][lab]==0).sum()), labeled_cut=int((d['y'][lab]==1).sum()),
                    step_matched_epochs=math.ceil((60*math.ceil(len(tr0)/64)+40*math.ceil(len(lab)/64))/math.ceil(len(lab)/64))))
display(pd.DataFrame(tab))
s5, s20 = set(subset(d['y'], tr0, .05, 7)), set(subset(d['y'], tr0, .2, 7)); print('%5 ⊂ %20 (seed 7, kat 1):', s5 <= s20)
""")

md(r"""
## 4. Modeller

Dört yarışmacı ve kontroller (`src/orman_ssl/advanced.py`):

* **rf_leaf4** – Random Forest, 500 ağaç, `min_samples_leaf=4`, `max_features=0.7`, `balanced_subsample`; girdi 60 özet özellik (`rf_features`).
* **cnn64** – Temporal CNN: width 64, 3 residual block, dilation 1/2/4, GroupNorm, GELU, dropout 0.2.
* **transformer48** – 2 encoder layer, 4 head, width 48, feed-forward 144, dropout 0.15; gözlenmemiş aylar key-padding ile maskelenir; observed-time mean pooling.
* **ssl_transformer48** – aynı Transformer; önce 60 epoch **masked reconstruction pretraining** (`block_mask`: 2–6 aylık blok + 2 bant gizlenir, Smooth L1 yalnız gizlenmiş-ama-gözlenmiş hücrelerde), sonra sınıflandırıcı başı başlangıç ağırlığına sıfırlanıp 40 epoch ince ayar.
* **step_matched** – transformer48, SSL'in toplam optimizer adımı kadar epoch (20% bütçede 320).

Ortak tarif: AdamW (wd 0.01), batch 64, class-weighted cross-entropy, label smoothing 0.02, grad-clip 1, ayları %10 silme (`augment`). Early stopping, validation seçimi, kalibrasyon, eşik ayarı **yok**; eşik 0.5.
""")
code(r"""
show_source(adv.ResidualBlock); show_source(adv.TemporalNet); show_source(adv.block_mask); show_source(adv.augment)
""")
code(r"""
show_source(adv.fit); show_source(rf_features); show_source(normalize)
""")
code(r"""
cfg = {c['name']: c for c in adv.CONFIGS}
for name in ['cnn64', 'transformer48']:
    net = adv.TemporalNet(cfg[name]); print(f'{name}: {sum(p.numel() for p in net.parameters()):,} parametre')
""")

md(r"""
## 5. Canlı demo eğitimi: kat 1, seed 7, %20 etiket

Aşağıda dört yöntem (+ step-matched) gerçekten eğitilir ve kat 1'in test noktalarında ölçülür; ardından `experiments/paper_v4/runs/` içindeki kayıtlı koşuyla karşılaştırılır. Kayıtlı koşular macOS'ta üretildi. Başka işletim sistemi / torch sürümünde kısa eğitimler (RF, CNN, 40 epoch Transformer) neredeyse birebir çıkar; uzun eğitimlerde (60 epoch ön eğitim, 320 epoch step-matched) float32 yuvarlama farkları yüzlerce adımda birikir ve tek noktalardaki olasılıklar belirgin sapabilir. Bu yüzden karşılaştırmayı tek kat/tek seed değil, 5 kat × 3 seed ortalamasıyla yapıyoruz; o ortalamalar 6. bölümde kayıtlarla 1e-9 hassasiyetle örtüşür. Süre: CPU'da ~2–3 dakika.
""")
code(r"""
from sklearn.metrics import f1_score, average_precision_score, roc_auc_score, brier_score_loss, confusion_matrix
def scores(y, p):
    q = p >= .5; cm = confusion_matrix(y, q, labels=[0,1])
    return dict(macro_f1=f1_score(y, q, average='macro'), AP=average_precision_score(y, p), roc_auc=roc_auc_score(y, p),
                brier=brier_score_loss(y, p), cut_recall=cm[1,1]/cm[1].sum(), tn=cm[0,0], fp=cm[0,1], fn=cm[1,0], tp=cm[1,1])
fold, seed, budget = 0, 7, .2
tr, te = np.array(folds[fold]['train_indices']), np.array(folds[fold]['test_indices'])
lab = subset(d['y'], tr, budget, seed)
steps = math.ceil((60*math.ceil(len(tr)/64)+40*math.ceil(len(lab)/64))/math.ceil(len(lab)/64))
plan = [('rf_leaf4','rf_leaf4',40), ('cnn64','cnn64',40), ('transformer48','transformer48',40), ('ssl_transformer48','ssl_transformer48',40), ('step_matched','transformer48',steps)]
demo = {}
for name, config_name, epochs in plan:
    t0 = time.time()
    state, log = adv.fit(cfg[config_name], d, tr, seed=seed, epochs=epochs, pre_epochs=60, labeled=lab, early_stop=False)
    p = adv.state_probability(state, adv.view(d, te))
    stored = json.loads((ROOT / f'experiments/paper_v4/runs/{name}_f{fold}_s{seed}_b{budget}.json').read_text())
    demo[name] = dict(**scores(d['y'][te], p), seconds=round(time.time()-t0,1), stored_macro_f1=stored['metrics']['macro_f1'],
                      max_prob_diff=float(np.max(np.abs(p - np.array(stored['probabilities'])))))
    print(f'{name:20s} macro-F1 {demo[name]["macro_f1"]:.4f}  (kayıtlı {stored["metrics"]["macro_f1"]:.4f})  {demo[name]["seconds"]} s')
display(pd.DataFrame(demo).T)
""")
code(r"""
# SSL ön eğitim kaybı ve ince ayar kaybı (kayıtlı koşudan)
r = json.loads((ROOT / 'experiments/paper_v4/runs/ssl_transformer48_f0_s7_b0.2.json').read_text())
fig, axes = plt.subplots(1, 2, figsize=(11, 3.2))
axes[0].plot(r['log']['pretrain_loss']); axes[0].set_title('SSL pretraining: Smooth L1 (60 epoch)'); axes[0].set_xlabel('epoch')
axes[1].plot([h['loss'] for h in r['log']['history']]); axes[1].set_title('Fine-tuning: weighted cross-entropy (40 epoch)'); axes[1].set_xlabel('epoch')
plt.tight_layout(); plt.show()
""")

md(r"""
## 6. Ana deney paper_v4: 180 koşu

Protokol deneyden önce donduruldu (`protocol.json`, `signature.json`). Aşağıda bütün koşu kayıtları okunur, her yöntem/bütçe/seed için beş katın test tahminleri 2.213 noktada **birleştirilir (pooled out-of-fold)**, metrikler yeniden hesaplanır ve `analysis.json` ile karşılaştırılır.
""")
code(r"""
runs = [json.loads(p.read_text()) for p in sorted((ROOT / 'experiments/paper_v4/runs').glob('*.json'))]
print('Koşu sayısı:', len(runs))
runs_df = pd.DataFrame([dict(method=r['method'], budget=r['budget'], seed=r['seed'], fold=r['fold'], n_labeled=r['n_labeled'], epochs=r['epochs'],
                             fold_macro_f1=r['metrics']['macro_f1'], seconds=r['seconds']) for r in runs])
display(runs_df.groupby(['method','budget']).agg(fits=('fold','size'), n_labeled=('n_labeled','min'), epochs=('epochs','max'), mean_fold_f1=('fold_macro_f1','mean'), total_sec=('seconds','sum')))
lookup = {v: i for i, v in enumerate(ids)}; n = len(ids); y = d['y']
pooled = {}
for (method, budget), grp in runs_df.groupby(['method','budget']):
    P = []
    for seed in [7,17,27]:
        p = np.full(n, np.nan)
        for r in runs:
            if r['method']==method and r['budget']==budget and r['seed']==seed:
                p[[lookup[i] for i in r['test_ids']]] = r['probabilities']
        assert np.isfinite(p).all(); P.append(p)
    pooled[(method, budget)] = np.stack(P)
NAMES = {'rf_leaf4':'Random forest','cnn64':'Temporal CNN','transformer48':'Transformer (40 ep.)','ssl_transformer48':'Block+band SSL','iid_ssl':'Independent-cell SSL','step_matched':'Step-matched Transformer','mask_only':'Observation mask only','metadata_only':'Location/year/campaign'}
def summary_table(keys):
    out = []
    for k in keys:
        s = [scores(y, p) for p in pooled[k]]
        out.append(dict(labels=f'{int(k[1]*100)}%', method=NAMES[k[0]], macro_f1=np.mean([v['macro_f1'] for v in s]), sd=np.std([v['macro_f1'] for v in s], ddof=1),
                        AP=np.mean([v['AP'] for v in s]), roc_auc=np.mean([v['roc_auc'] for v in s]), cut_recall=np.mean([v['cut_recall'] for v in s]), brier=np.mean([v['brier'] for v in s])))
    return pd.DataFrame(out)
display(Markdown('**Table 3 — Primary pooled out-of-fold results (mean over 3 seeds; SD = seed standard deviation)**'))
tab3 = summary_table([(m,b) for b in [.2,1.] for m in ['rf_leaf4','cnn64','transformer48','ssl_transformer48']]); display(tab3)
display(Markdown('**Table 4 — Controls at 20% labels**'))
tab4 = summary_table([(m,.2) for m in ['transformer48','ssl_transformer48','iid_ssl','step_matched','mask_only','metadata_only']]); display(tab4)
""")
code(r"""
# analysis.json ile çapraz kontrol (1e-9 toleransla aynı olmalı)
A = json.loads((ROOT / 'experiments/paper_v4/analysis.json').read_text())
ref = {(r['method'], r['budget']): r['macro_f1_mean'] for r in A['summary']}
mx = max(abs(ref[k] - np.mean([scores(y,p)['macro_f1'] for p in pooled[k]])) for k in ref)
print('Yeniden hesap ile analysis.json arasındaki en büyük fark:', f'{mx:.2e}')
""")
md(r"""
### 6.1 Paired spatial-component bootstrap
874 bileşen yerine koyarak 2.000 kez örneklenir; her çekimde aynı ağırlıklar iki yönteme de uygulanır, üç seed'in farkı ortalanır; %2.5–%97.5 yüzdelikleri aralıktır. Nokta değil **bileşen** örneklenir çünkü komşu noktalar bağımsız değildir.
""")
code(r"""
def macro(y, p, w):
    q = p >= .5
    tp = np.sum(w*(q&(y==1))); tn = np.sum(w*((~q)&(y==0))); fp = np.sum(w*(q&(y==0))); fn = np.sum(w*((~q)&(y==1)))
    return .5*((2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)+(2*tn/(2*tn+fp+fn) if 2*tn+fp+fn else 0))
uniq, gi = np.unique(d['groups'], return_inverse=True); rng = np.random.default_rng(120926)
comparators = ['transformer48','step_matched','iid_ssl','rf_leaf4','cnn64']; draws = {c: [] for c in comparators}
for _ in range(2000):
    w = np.bincount(rng.integers(0, len(uniq), len(uniq)), minlength=len(uniq))[gi]
    if not w[y==0].sum() or not w[y==1].sum(): continue
    ssl = np.mean([macro(y, p, w) for p in pooled[('ssl_transformer48', .2)]])
    for c in comparators: draws[c].append(ssl - np.mean([macro(y, p, w) for p in pooled[(c, .2)]]))
boot = pd.DataFrame([dict(comparison=f'SSL − {NAMES[c]}', mean_diff=np.mean([macro(y,a,np.ones(n))-macro(y,b,np.ones(n)) for a,b in zip(pooled[('ssl_transformer48',.2)], pooled[(c,.2)])]),
                          ci_low=np.quantile(draws[c], .025), ci_high=np.quantile(draws[c], .975), role='primary' if c=='transformer48' else 'exploratory') for c in comparators])
display(boot)
print('analysis.json kayıtlı aralıklar:'); display(pd.DataFrame(A['paired_comparisons'])[['comparator','mean_difference','paired_group_bootstrap_95_interval']])
""")
code(r"""
for name, cap in [('01_primary','Figure 2 — Primary comparisons at 20% and 100% labels'),('02_controls','Figure 3 — Controls and paired bootstrap intervals'),('03_data','Figure 1 — Locations and observed-month support')]:
    display(Markdown(f'**{cap}**')); display(Image(filename=str(ROOT/f'paper/figures/{name}.png'), width=900))
""")
code(r"""
# Karışıklık matrisleri (%20 etiket, seed ortalaması değil: üç seed'in toplamı)
rows = []
for m in ['rf_leaf4','cnn64','transformer48','ssl_transformer48','step_matched']:
    cm = sum(confusion_matrix(y, p>=.5, labels=[0,1]) for p in pooled[(m,.2)])
    rows.append(dict(method=NAMES[m], TN=cm[0,0], FP=cm[0,1], FN=cm[1,0], TP=cm[1,1], note='3 seed toplamı (3 × 2213 karar)'))
display(pd.DataFrame(rows))
# Kullanılmamış konum taraması (dış doğrulama için yeterli mi?)
probe = json.loads((ROOT / 'experiments/paper_v4/unused_probe_audit.json').read_text())
print(json.dumps({k: probe[k] for k in list(probe)[:8]}, indent=1, ensure_ascii=False)[:1500])
""")

md(r"""
## 7. Uzantılar

### 7.1 paper_v5 — gruplama yarıçapı duyarlılığı (tek seed)
Aynı kohort 5 / 10 / 20 km ile yeniden gruplanıp beş yöntem seed 7, %20 etiketle yeniden eğitildi (75 koşu, bütün checkpoint'ler saklı). 5 km koşuları paper_v4'ün seed-7 olasılıklarını 2e-16 hassasiyetle yeniden üretir.
""")
code(r"""
v5 = pd.read_csv(ROOT / 'experiments/paper_v5_exploratory/results.csv')
v5['method'] = v5['method'].map(NAMES)
display(Markdown('**Table 6 — Grouping-radius sensitivity, 20% labels, seed 7 (pooled OOF macro-F1)**'))
display(v5.pivot(index='radius_km', columns='method', values='macro_f1').round(4))
display(v5.pivot(index='radius_km', columns='method', values='average_precision').round(4).rename_axis(columns='AP'))
sup = json.loads((ROOT / 'experiments/paper_v5_exploratory/support_audit.json').read_text())
display(pd.DataFrame([{k: r[k] for k in ['radius_km','groups','positive_groups','largest_component']} for r in sup['radii']]))
display(Image(filename=str(ROOT/'paper/figures/05_radius.png'), width=850))
""")
md(r"""
### 7.2 paper_v6 — etiket bütçesi eğrisi
%5, %10, %50 bütçeleri paper_v4'ün aynı katları, seed'leri ve tarifleriyle (225 koşu). %20 ve %100 satırları paper_v4'ten gelir.
""")
code(r"""
v6 = json.loads((ROOT / 'experiments/paper_v6_label_curve/analysis.json').read_text())
curve = pd.DataFrame(v6['combined_curve']); curve['method'] = curve['method'].map(NAMES)
display(Markdown('**Table 5 — Label-budget curve (macro-F1 mean ± seed SD)**'))
piv = curve.pivot(index='budget', columns='method', values='macro_f1_mean').round(4); piv.index = [f'{int(b*100)}%' for b in piv.index]; display(piv)
pivsd = curve.pivot(index='budget', columns='method', values='macro_f1_std').round(4); pivsd.index = piv.index; display(pivsd.rename_axis(columns='seed SD'))
pc = pd.DataFrame(v6['paired_comparisons']); pc['comparator'] = pc['comparator'].map(NAMES)
pc['ci'] = pc['paired_group_bootstrap_95_interval'].apply(lambda v: f'[{v[0]:.4f}, {v[1]:.4f}]')
display(Markdown('**SSL minus comparator, per budget (paired component bootstrap)**')); display(pc[['budget','comparator','mean_difference','ci','role']])
display(Image(filename=str(ROOT/'paper/figures/04_label_curve.png'), width=850))
print('Eğitim ortamı:', {k: v6_exec[k] for k in ['platform','python','torch','workers','elapsed_wall_seconds']} if (v6_exec:=json.loads((ROOT/'experiments/paper_v6_label_curve/execution.json').read_text())) else '')
""")

md(r"""
## 8. Keşif: Presto frozen linear probe
Hazır Presto encoder dondurulup embedding üstünde lojistik regresyon (90 fit). Fine-tune yok; Presto'nun beklediği Sentinel-1, iklim ve yükseklik girdileri yok. Bu yüzden **karşılaştırma değil, sınırlı bir not**.
""")
code(r"""
pr = json.loads((ROOT / 'experiments/presto_v1_exploratory/analysis.json').read_text())
display(pd.DataFrame([dict(method=s['method'], budget=s['budget'], macro_f1=s['macro_f1_mean'], sd=s['macro_f1_std'], AP=s['average_precision_mean']) for s in pr['summary']]))
print('\n'.join(json.loads((ROOT / 'experiments/presto_v1_exploratory/protocol.json').read_text())['limitations']))
""")

md(r"""
## 9. Ürün modeli advanced_v3 ve gerçek çıkarım

Makaledeki deneyden **ayrı** bir mühendislik sürümü: 1.266 eğitim / 461 kalibrasyon / 486 test ayrımıyla eğitilmiş 5 CNN + 5 SSL Transformer ensemble'ı; olasılıklar ortalanıp kalibrasyon kümesinde Platt ölçeklenmiş, eşik oradan seçilmiş. Ağırlıklar `models/advanced_v3/*.pt`, hash'ler `bundle.json`. Aşağıda 486 örnekte gerçek çıkarım yapılır ve kayıtlı sonuçla karşılaştırılır. Ürün arayüzü: `URUNU_AC.command` → `scripts/serve_product.py` → `reports/product.html`.
""")
code(r"""
bundle = json.loads((ROOT / 'models/advanced_v3/bundle.json').read_text())
print('Üyeler:', [m['path'] for m in bundle['members']]); print('Kalibrasyon:', bundle['calibration'], '| eşik:', bundle['threshold'])
card = json.loads((ROOT / 'models/advanced_v3/model_card.json').read_text()); print(json.dumps(card, indent=1, ensure_ascii=False)[:1800])
inp = dict(np.load(ROOT / 'output/advanced_prediction/input.npz', allow_pickle=False))
t0 = time.time(); res = adv.ensemble_predict(ROOT / 'models/advanced_v3/bundle.json', inp); print(f'486 örnekte 10 üyeli çıkarım: {time.time()-t0:.1f} s')
saved = json.loads((ROOT / 'output/advanced_prediction/predictions.json').read_text())
print('Kayıtlı tahminle en büyük olasılık farkı:', float(np.max(np.abs(np.array(res['probabilities'])[:,1] - np.array(saved['probabilities'])[:,1]))))
ev = json.loads((ROOT / 'experiments/advanced_v3/evaluation.json').read_text())
labels486 = manifest.set_index('id').loc[res['ids'], 'label'].values
cm = confusion_matrix(labels486, np.array(res['predictions']), labels=[0,1])
display(pd.DataFrame(cm, index=['gerçek orman','gerçek kesim'], columns=['tahmin orman','tahmin kesim']))
print('macro-F1 (486 örnek):', round(f1_score(labels486, res['predictions'], average='macro'), 4), '| model_card kayıtlı:', round(card['metrics']['macro_f1'], 4))
""")
code(r"""
show_source(adv.ensemble_predict)
print((ROOT / 'scripts/run_advanced.py').read_text()[:3000])
""")

md(r"""
## 10. Doğrulama ve tekrar üretim

`verify_paper.py` 180 kaydı okuyup OOF vektörlerini yeniden kurar, metrikleri yeniden hesaplar, hash'leri ve "validation ile seçim yapılmadı" kuralını denetler. Testler `tests/` altındadır.
""")
code(r"""
import subprocess
r = subprocess.run([sys.executable, str(ROOT/'scripts/verify_paper.py')], cwd=ROOT, capture_output=True, text=True); print(r.stdout[-1500:], r.stderr[-500:])
r = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], cwd=ROOT, capture_output=True, text=True); print(r.stderr[-400:])
""")
md(r"""
### Tam tekrar üretim komutları (proje kökünde, `.venv` ile)

```bash
.venv/bin/python scripts/prepare_disfor.py                  # ham DISFOR → real_series.npz
.venv/bin/python scripts/train_paper.py --workers 3         # paper_v4: 180 fit (önbellek varsa atlar)
.venv/bin/python scripts/analyze_paper.py                   # tablolar + bootstrap → analysis.json
.venv/bin/python scripts/plot_paper.py                      # Figure 1–3
.venv/bin/python scripts/scientific_v5.py prepare|train|analyze ; scripts/verify_spatial_v5.py ; scripts/report_spatial_v5.py
.venv/bin/python scripts/label_curve_v6.py prepare|train|analyze ; scripts/plot_extensions.py
.venv/bin/python scripts/compose_paper.py && scripts/build_paper_docx.py   # makale
.venv/bin/python scripts/build_final_report.py              # Türkçe rapor
.venv/bin/python scripts/verify_paper.py ; scripts/verify_advanced.py ; scripts/verify_final_delivery.py
.venv/bin/python -m unittest discover -s tests -v
```

### Dosya haritası

| Ne | Nerede |
|---|---|
| Ham veri, lisans | `data/disfor/` |
| Model girdisi | `data/processed/real_series.npz` |
| Model kodu | `src/orman_ssl/advanced.py`, `experiment.py`, `inputs.py` |
| Ana deney kayıtları | `experiments/paper_v4/{protocol,folds,jobs,signature,analysis,verification}.json`, `runs/` |
| Uzantılar | `experiments/paper_v5_exploratory/`, `experiments/paper_v6_label_curve/` |
| Ürün modeli | `models/advanced_v3/` |
| Makale | `paper/manuscript.md`, `output/pdf/Orman_SSL_Manuscript.pdf` |
| Türkçe rapor | `output/final/` |
| Ürün arayüzü | `URUNU_AC.command`, `scripts/serve_product.py`, `reports/product.html` |
""")

nb['cells'] = cells
nb.metadata['kernelspec'] = dict(name='python3', display_name='Python 3', language='python')
(OUT / 'figures').mkdir(exist_ok=True)
nbf.write(nb, OUT / 'Orman_SSL_Proje_Defteri.ipynb')
print('written', OUT / 'Orman_SSL_Proje_Defteri.ipynb', len(cells), 'cells')
