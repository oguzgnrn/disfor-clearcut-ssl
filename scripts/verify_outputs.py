"""Check geospatial grids, provenance hashes, maps and measured summaries."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import rasterio
root=Path(__file__).resolve().parents[1]
checks=[]
for row in json.loads((root/'data/metadata/downloads.json').read_text()):
    assert hashlib.sha256((root/row['path']).read_bytes()).hexdigest()==row['sha256']
checks.append('Figshare source hashes match saved download manifest')
for row in json.loads((root/'data/metadata/sentinel_manifest.json').read_text())['scenes']:
    assert hashlib.sha256((root/row['path']).read_bytes()).hexdigest()==row['sha256']
checks.append('Sentinel crop hashes match saved manifest')
grid=None
for name in ['sentinel_before','sentinel_after','dnbr','ndvi_before','ndvi_after']:
    with rasterio.open(root/f'data/processed/{name}.tif') as ds:
        current=(str(ds.crs),ds.transform,ds.width,ds.height)
        assert current[0]=='EPSG:32635'
        assert ds.res==(20,20)
        if grid is None:grid=current
        assert current==grid
checks.append('Sentinel bands and index outputs use identical 20 m UTM grid')
a=np.load(root/'data/processed/sentinel_indices.npz')
with rasterio.open(root/'data/processed/dnbr.tif') as ds:
    np.testing.assert_allclose(ds.read(1),a['dnbr'],equal_nan=True)
assert np.isnan(a['dnbr'][~a['valid']]).all()
s=json.loads((root/'reports/sentinel_summary.json').read_text())
assert s['valid_pixels']==int(a['valid'].sum())
for row in s['thresholds']:
    count=int((a['dnbr']>row['threshold']).sum())
    assert row['pixels']==count
    assert abs(row['screened_hectares']-count*.04)<1e-9
checks.append('All dNBR threshold counts, masks and hectare conversions recompute exactly')
for qml in (root/'data/processed').glob('*.qml'):ET.parse(qml)
for row in json.loads((root/'reports/gfd_audit.json').read_text()):
    assert sum(row['counts'].values())==row['shape'][0]*row['shape'][1]
    assert set(map(int,row['counts']))<={0,11,12,13,14,15,18,19,20,21,22}
checks.append('GFD exact counts cover every cell; QGIS styles are well-formed XML')
payload=dict(status='passed',checks=checks)
(root/'reports/output_verification.json').write_text(json.dumps(payload,indent=2))
print(json.dumps(payload,indent=2))
