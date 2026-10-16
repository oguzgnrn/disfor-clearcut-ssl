"""Stream original categorical raster values, retain unknown/zero semantics."""
import os
from pathlib import Path
root = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(root/'.cache/matplotlib'))
import json
from collections import Counter
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window
from rasterio.transform import array_bounds
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

# Figshare v1 definitions; zero is deliberately NOT called intact forest.
labels = {0:'0 / belirsiz',11:'Gezici tarım',12:'Yeniden ağaçlandırma',13:'Plantasyon yenileme',14:'Ormansızlaşma',15:'Yangın',18:'Yapılaşma',19:'Tarım genişlemesi',20:'Sel',21:'Yağ palmiyesi',22:'Yeni yapay orman'}
colors = ['#e5e7eb','#e9bd50','#247860','#65b788','#754c24','#e45339','#7e5fc4','#d89934','#378dbb','#9fb441','#3db9ad']
codes = list(labels)
rows=[]
for path in sorted((root/'data/raw').glob('GFC*.tif')):
    counts = Counter(); best_n = -1; best = None
    with rasterio.open(path) as ds:
        # Fixed 512 windows bound RAM even for unusually large native blocks.
        for row in range(0, ds.height, 512):
            for col in range(0, ds.width, 512):
                w = Window(col,row,min(512,ds.width-col),min(512,ds.height-row))
                a = ds.read(1,window=w,masked=True)
                values, n = np.unique(a.compressed(),return_counts=True)
                counts.update({int(v):int(c) for v,c in zip(values,n)})
                score = int(np.isin(a.filled(-32768),codes[1:]).sum())
                if score>best_n: best_n,best = score,w
        crop=ds.read(1,window=best); transform=ds.window_transform(best)
        profile=ds.profile.copy(); profile.update(height=crop.shape[0],width=crop.shape[1],transform=transform,compress='deflate')
        crop_path=root/'data/processed'/f'{path.stem}_inspection.tif'
        with rasterio.open(crop_path,'w',**profile) as dst:
            dst.write(crop,1); dst.update_tags(source='Figshare 28465178 v1',selection='densest 512px window by nonzero known codes; biased visualization sample')
        preview=ds.read(1,out_shape=(600,600),resampling=Resampling.nearest)
        info=dict(file=path.name,crs=str(ds.crs),bounds=list(ds.bounds),shape=[ds.height,ds.width],resolution=list(ds.res),
                  nodata=ds.nodata,counts=dict(sorted(counts.items())),mask_flags=str(ds.mask_flag_enums),
                  warning='0 semantics conflict between Figshare and paper. NoData is not declared. Pixel counts are not areas.',
                  crop=str(crop_path.relative_to(root)),crop_bounds=list(array_bounds(*crop.shape,transform)),crop_selection='Densest window, exploratory only')
        rows.append(info)
    mapped=np.full(crop.shape,len(codes))
    for i,code in enumerate(codes): mapped[crop==code]=i
    fig,ax=plt.subplots(figsize=(9,6))
    bounds=info['crop_bounds']
    im=ax.imshow(mapped,cmap=ListedColormap(colors+['#111827']),norm=BoundaryNorm(np.arange(len(codes)+2)-.5,len(codes)+1),extent=[bounds[0],bounds[2],bounds[1],bounds[3]],interpolation='nearest')
    ax.set(xlabel='Longitude (EPSG:4326)',ylabel='Latitude (EPSG:4326)',title=f'{path.stem} • gerçek veri / seçilmiş inceleme penceresi')
    present=[i for i,code in enumerate(codes) if (crop==code).any()]
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=colors[i],label=f'{codes[i]}: {labels[codes[i]]}') for i in present],loc='upper left',bbox_to_anchor=(1.01,1),fontsize=8)
    fig.tight_layout();fig.savefig(root/'figures'/f'{path.stem}_inspection.png',dpi=170);plt.close(fig)
    # QGIS companion style loads automatically beside each crop.
    entries=''.join(f'<paletteEntry value="{k}" color="{c}" alpha="255" label="{k}: {labels[k]}"/>' for k,c in zip(codes,colors))
    crop_path.with_suffix('.qml').write_text(f'<!DOCTYPE qgis PUBLIC "http://mrcc.com/qgis.dtd" "SYSTEM"><qgis version="3.40"><pipe><rasterrenderer type="paletted" band="1" opacity="1"><colorPalette>{entries}</colorPalette></rasterrenderer></pipe></qgis>')
(root/'reports/gfd_audit.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
print(json.dumps(rows,indent=2,ensure_ascii=False))
