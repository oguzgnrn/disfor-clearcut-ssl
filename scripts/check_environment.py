"""Check runtime, pinned dependencies and files required for local inference."""
import importlib.metadata
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
errors=[]
if sys.version_info[:2] != (3,11): errors.append('Python 3.11 required')
for line in (ROOT/'requirements.txt').read_text().splitlines():
    if '==' not in line: continue
    name, expected = line.split('==')
    try: actual=importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError: actual='missing'
    if actual.split('+')[0]!=expected: errors.append(f'{name}: expected {expected}, found {actual}')
for name in ['models/model.pt','data/disfor/pixel_data.parquet','data/examples/inference_windows.json']:
    if not (ROOT/name).is_file(): errors.append('Missing '+name)
if errors:
    print('\n'.join(errors),file=sys.stderr);sys.exit(1)
print('Environment and inference assets: OK')
