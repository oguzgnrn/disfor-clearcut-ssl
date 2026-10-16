"""Label-free monthly Sentinel-2 input preparation and validation."""
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

BANDS = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12']
UNITS = 'Source-provided DN, no added offset; per-channel standardization fitted on training only'


def monthly_days(target_year):
    start = date(target_year - 1, 1, 1)
    return np.array([(date(y, m, 15) - start).days
                     for y in [target_year - 1, target_year]
                     for m in range(1, 13)], dtype='float32')


def validate_input(data, channels=BANDS, timesteps=24):
    required = {'x', 'observed', 'days', 'ids', 'metadata'}
    if not required.issubset(data):
        raise ValueError('Missing fields: ' + ', '.join(sorted(required - set(data))))
    x, mask, days, ids = (np.asarray(data[k]) for k in ['x', 'observed', 'days', 'ids'])
    if x.ndim != 3 or x.shape[0] == 0 or x.shape[1:] != (timesteps, len(channels)):
        raise ValueError(f'x must be nonempty [N,{timesteps},{len(channels)}]')
    if not np.issubdtype(x.dtype, np.number) or np.iscomplexobj(x):
        raise ValueError('x must contain real numeric DN values')
    if mask.shape != x.shape or mask.dtype != bool:
        raise ValueError('observed must be bool and match x')
    if ids.shape != (len(x),) or ids.dtype.kind not in 'US' or any(not str(i).strip() for i in ids):
        raise ValueError('ids must be a nonempty string vector with N entries')
    if len(np.unique(ids)) != len(x):
        raise ValueError('IDs must be unique')
    if not np.isfinite(x[mask]).all() or not mask.any(axis=(1, 2)).all():
        raise ValueError('Observed values must be finite; all-missing samples are invalid')
    if days.shape != x.shape[:2] or not np.issubdtype(days.dtype, np.number) or np.iscomplexobj(days) or not np.isfinite(days).all():
        raise ValueError('days must be finite numeric [N,24]')
    # Two calendar years can have leap day in either year or neither year.
    templates = np.stack([monthly_days(y) for y in [2018, 2020, 2021]])
    if not np.isclose(days[:, None, :], templates[None, :, :], atol=.001, rtol=0).all(-1).any(-1).all():
        raise ValueError('days must encode the 15th of each month in two full calendar years')
    try:
        metadata = json.loads(str(data['metadata']))
    except (ValueError, TypeError) as exc:
        raise ValueError('metadata must be a scalar JSON object') from exc
    if not isinstance(metadata, dict) or metadata.get('channels') != list(channels):
        raise ValueError('Channel order differs from training')
    if metadata.get('units') != UNITS:
        raise ValueError('Explicit source DN units are required; reflectance/SAR values are incompatible')
    return metadata


def prepare_observations(observations, windows, source):
    """Use only bands, timestamps, clear/SCL and requested windows; never labels."""
    required = {'sample_id', 'timestamps', 'clear', 'SCL', *BANDS}
    if not required.issubset(observations.columns):
        raise ValueError('Missing observation columns: ' + ', '.join(sorted(required - set(observations.columns))))
    if not source or not isinstance(windows, list) or not windows:
        raise ValueError('A source description and nonempty windows list are required')
    # Explicit projection prevents source label or other outcome columns entering features.
    obs = observations[list(sorted(required))].copy()
    if obs.sample_id.isna().any():
        raise ValueError('sample_id cannot be missing')
    if obs['clear'].isna().any() or not obs['clear'].isin([True, False, 0, 1]).all():
        raise ValueError('clear must contain booleans or 0/1, not strings')
    obs['sample_id'] = obs.sample_id.astype(str)
    obs['date'] = pd.to_datetime(obs['timestamps'], utc=True, errors='raise')
    if obs['date'].isna().any():
        raise ValueError('timestamps cannot be missing')
    for band in BANDS:
        if not pd.api.types.is_numeric_dtype(obs[band]):
            raise ValueError('Bands must be numeric: ' + band)
        if np.isinf(obs[band].to_numpy()).any():
            raise ValueError('Infinite band values are invalid')
    if not pd.api.types.is_numeric_dtype(obs.SCL) or not obs.SCL.isin(range(12)).all():
        raise ValueError('SCL must use integer codes 0 through 11')
    grouped = {key: g for key, g in obs.groupby('sample_id')}
    xs, masks, times, ids, details = [], [], [], [], []
    for window in windows:
        if not isinstance(window, dict) or not {'id','sample_id','target_year'}.issubset(window):
            raise ValueError('Each window requires id, sample_id, target_year')
        year, identifier = window['target_year'], window['id']
        if type(year) is not int or not 1901 <= year <= 9998:
            raise ValueError('target_year must be an integer calendar year')
        if not isinstance(identifier, str) or not identifier.strip() or identifier in ids:
            raise ValueError('Window IDs must be unique nonempty strings')
        sid = str(window['sample_id'])
        if sid not in grouped:
            raise ValueError('No source observations for sample ' + sid)
        start = pd.Timestamp(f'{year-1}-01-01', tz='UTC')
        end = pd.Timestamp(f'{year+1}-01-01', tz='UTC')
        g = grouped[sid]
        g = g[(g.date >= start) & (g.date < end) & g.clear.astype(bool) & g.SCL.isin([4,5])].copy()
        g['slot'] = (g.date.dt.year - year + 1) * 12 + g.date.dt.month - 1
        x = g.groupby('slot')[BANDS].median().reindex(range(24)).to_numpy(dtype='float32')
        mask = np.isfinite(x)
        if not mask.any():
            raise ValueError('No usable observation in requested window: ' + identifier)
        xs.append(x); masks.append(mask); times.append(monthly_days(year)); ids.append(identifier)
        counts = [int(mask.any(-1)[i:i+12].sum()) for i in [0,12]]
        details.append(dict(id=identifier,sample_id=sid,target_year=year,observed_months=counts,quality_eligible=min(counts)>=6))
    metadata = dict(kind='real', channels=BANDS, units=UNITS, source=source,
                    temporal_alignment='Monthly medians in two full calendar years; month-15 day offsets',
                    preparation='clear AND SCL 4/5; no event dates or labels used')
    data = dict(x=np.stack(xs), observed=np.stack(masks), days=np.stack(times),
                ids=np.array(ids), metadata=json.dumps(metadata))
    validate_input(data)
    return data, details


def main():
    parser = argparse.ArgumentParser(description='Prepare label-free 24-month input from Sentinel-2 observation Parquet')
    parser.add_argument('--observations', required=True, type=Path)
    parser.add_argument('--windows', required=True, type=Path)
    parser.add_argument('--source', required=True, help='Source and processing history; DN compatibility must be established')
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.suffix != '.npz':
        parser.error('--out must end in .npz')
    try:
        windows = json.loads(args.windows.read_text())
        data, details = prepare_observations(pd.read_parquet(args.observations), windows, args.source)
    except (ValueError, KeyError) as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out, **data)
    manifest = dict(observations_sha256=hashlib.sha256(args.observations.read_bytes()).hexdigest(),
                    windows_sha256=hashlib.sha256(args.windows.read_bytes()).hexdigest(),
                    metadata=json.loads(str(data['metadata'])), samples=details)
    args.out.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2))
    print(f'Prepared {len(details)} samples; {sum(r["quality_eligible"] for r in details)} pass monthly quality criteria')

if __name__ == '__main__':
    main()
