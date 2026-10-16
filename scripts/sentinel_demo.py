"""Small real Sentinel-2 two-date screening demo; NOT a trained classifier."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(root/'.cache/matplotlib'))
import numpy as np
import requests
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform_bounds
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling

BBOX=[28.30,36.88,28.34,36.92]
BANDS=['red','nir','swir22','scl']

def normalized_difference(a,b):
    den=a+b
    return np.divide(a-b,den,out=np.full_like(a,np.nan,dtype='float32'),where=np.isfinite(den)&(np.abs(den)>1e-6))

def search(period):
    interval={'before':'2021-07-10T00:00:00Z/2021-07-25T23:59:59Z','after':'2021-08-10T00:00:00Z/2021-08-25T23:59:59Z'}[period]
    query=dict(collections=['sentinel-2-l2a'],bbox=BBOX,datetime=interval,limit=100)
    r=requests.post('https://earth-search.aws.element84.com/v1/search',json=query,timeout=60);r.raise_for_status()
    j=r.json()
    # Restrict to the same tile and original pre-offset products for a transparent demo.
    candidates=[f for f in j['features'] if f['properties'].get('grid:code')=='MGRS-35SPA' and float(f['properties']['s2:processing_baseline'])<4]
    if not candidates: raise RuntimeError('No baseline<4 scene for fixed grid in first 100 results; revise query explicitly.')
    scene=min(candidates,key=lambda f:(f['properties']['eo:cloud_cover'],f['id']))
    (root/f'data/metadata/stac_{period}_search.json').write_text(json.dumps(j,indent=2))
    (root/f'data/metadata/scene_{period}.json').write_text(json.dumps(scene,indent=2))
    return scene

def acquire():
    west,south,east,north=transform_bounds('EPSG:4326','EPSG:32635',*BBOX)
    west=math.floor(west/20)*20; north=math.ceil(north/20)*20
    width=math.ceil((east-west)/20);height=math.ceil((north-south)/20)
    transform=from_origin(west,north,20,20)
    manifest=[]
    for period in ['before','after']:
        p=root/f'data/metadata/scene_{period}.json'
        scene=json.loads(p.read_text()) if p.exists() else search(period)
        arrays=[];assets=[]
        for key in BANDS:
            asset=scene['assets'][key]; meta=asset['raster:bands'][0]
            href=asset['href']
            if not href.startswith('https://'): raise ValueError('Only public HTTPS assets are accepted')
            with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_TIMEOUT='60',GDAL_HTTP_MAX_RETRY='2'):
                with rasterio.open(href) as src:
                    with WarpedVRT(src,crs='EPSG:32635',transform=transform,width=width,height=height,
                                   resampling=Resampling.nearest if key=='scl' else Resampling.average,
                                   src_nodata=meta.get('nodata',0),nodata=np.nan,dtype='float32') as vrt:
                        a=vrt.read(1)
            if key!='scl': a=a*meta.get('scale',1)+meta.get('offset',0)
            arrays.append(a);assets.append(dict(band=key,href=href,scale=meta.get('scale',1),offset=meta.get('offset',0)))
            print(period,key,'valid fraction',np.isfinite(a).mean(),flush=True)
        path=root/f'data/processed/sentinel_{period}.tif'
        with rasterio.open(path,'w',driver='GTiff',height=height,width=width,count=4,dtype='float32',crs='EPSG:32635',transform=transform,nodata=np.nan,compress='deflate') as dst:
            dst.write(np.stack(arrays));dst.descriptions=tuple(BANDS)
        manifest.append(dict(period=period,id=scene['id'],datetime=scene['properties']['datetime'],scene_cloud_percent=scene['properties']['eo:cloud_cover'],
                             assets=assets,path=str(path.relative_to(root)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (root/'data/metadata/sentinel_manifest.json').write_text(json.dumps(dict(bbox=BBOX,crs='EPSG:32635',resolution_m=20,scenes=manifest,
         attribution='Contains modified Copernicus Sentinel data (2021); accessed through Element 84 Earth Search',
         selection='Same tile 35SPA, original baseline<4; minimum scene cloud among first 100 results in each fixed interval'),indent=2))

def analyze():
    arrays=[]
    for period in ['before','after']:
        with rasterio.open(root/f'data/processed/sentinel_{period}.tif') as ds:
            arrays.append(ds.read());profile=ds.profile.copy();bounds=list(ds.bounds)
    before,after=arrays
    # Keep only confident vegetation / bare land; water, cloud, shadow excluded.
    valid=np.isin(before[3],[4,5])&np.isin(after[3],[4,5])&np.isfinite(before[:3]).all(0)&np.isfinite(after[:3]).all(0)
    ndvi0=normalized_difference(before[1],before[0]);ndvi1=normalized_difference(after[1],after[0])
    nbr0=normalized_difference(before[1],before[2]);nbr1=normalized_difference(after[1],after[2])
    dnbr=np.where(valid,nbr0-nbr1,np.nan)
    if not np.isfinite(dnbr).any(): raise RuntimeError('No jointly valid land pixels')
    profile.update(count=1)
    for name,array in [('dnbr',dnbr),('ndvi_before',np.where(valid,ndvi0,np.nan)),('ndvi_after',np.where(valid,ndvi1,np.nan))]:
        with rasterio.open(root/f'data/processed/{name}.tif','w',**profile) as dst: dst.write(array.astype('float32'),1)
    np.savez_compressed(root/'data/processed/sentinel_indices.npz',dnbr=dnbr,ndvi_before=ndvi0,ndvi_after=ndvi1,valid=valid)
    summary=dict(kind='real_satellite_screening',shape=list(dnbr.shape),valid_pixels=int(valid.sum()),total_pixels=int(valid.size),
                 jointly_valid_fraction=float(valid.mean()),mean_dnbr=float(np.nanmean(dnbr)),median_dnbr=float(np.nanmedian(dnbr)),
                 thresholds=[dict(threshold=t,pixels=int((dnbr>t).sum()),screened_hectares=float((dnbr>t).sum()*.04)) for t in [.1,.2,.3,.4]],
                 note='Exploratory thresholds, not calibrated severity classes or verified burned/forest area. No forest mask. Two-date seasonal/soil/moisture effects remain.',bounds_utm=bounds)
    (root/'reports/sentinel_summary.json').write_text(json.dumps(summary,indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,3,figsize=(13,4.6))
    scenes=json.loads((root/'data/metadata/sentinel_manifest.json').read_text())['scenes']
    for ax,array,title,cmap,lo,hi in zip(axs,[np.where(valid,nbr0,np.nan),np.where(valid,nbr1,np.nan),dnbr],
        [scenes[0]['datetime'][:10]+' / NBR',scenes[1]['datetime'][:10]+' / NBR','dNBR = önce - sonra'],['YlGn','YlGn','RdYlGn_r'],[-.3,-.3,-.6],[.8,.8,.6]):
        im=ax.imshow(array,extent=[bounds[0],bounds[2],bounds[1],bounds[3]],cmap=cmap,vmin=lo,vmax=hi)
        ax.set(title=title,xlabel='UTM 35N easting (m)');ax.ticklabel_format(style='plain',useOffset=False);ax.tick_params(axis='x',rotation=45)
        fig.colorbar(im,ax=ax,shrink=.65)
    axs[0].set_ylabel('Northing (m)')
    fig.suptitle('Marmaris çevresi • gerçek Sentinel-2 • değişim taraması / sınıflandırma değil',fontsize=12)
    fig.tight_layout();fig.savefig(root/'figures/sentinel_change.png',dpi=170);plt.close(fig)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--download',action='store_true');a=p.parse_args()
    if a.download: acquire()
    analyze()
