"""Download two small genuine Figshare members via HTTP ranges, verifying ZIP CRC."""
from pathlib import Path
import hashlib
import json
import requests
from remotezip import RemoteZip

root = Path(__file__).resolve().parents[1]
(root/'data/metadata').mkdir(parents=True, exist_ok=True)
(root/'data/raw').mkdir(parents=True, exist_ok=True)
r = requests.get('https://api.figshare.com/v2/articles/28465178/versions/1', timeout=60)
r.raise_for_status(); article = r.json()
(root/'data/metadata/figshare_28465178.json').write_text(json.dumps(article, indent=2))
file = next(f for f in article['files'] if f['id'] == 52545710)
rows = []
with RemoteZip(file['download_url'], initial_buffer_size=131072, timeout=60) as z:
    for member in ['GFC0/GFC22.tif', 'GFC0/GFC30.tif']:
        path = root/'data/raw'/Path(member).name
        content = z.read(member)  # zipfile verifies CRC before returning.
        path.write_bytes(content)
        rows.append(dict(path=str(path.relative_to(root)), member=member, url=file['download_url'],
                         sha256=hashlib.sha256(content).hexdigest(), zip_crc32=z.getinfo(member).CRC,
                         article_version=1, license=article['license']))
(root/'data/metadata/downloads.json').write_text(json.dumps(rows, indent=2))
print('Downloaded and CRC-checked two members; whole 1.42 GB archive was not downloaded.')
