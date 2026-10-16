"""Run the complete label-free local inference workflow, without retraining."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from orman_ssl.inputs import prepare_observations
from orman_ssl.predict import predict


def run(observations, windows_path, source, out, checkpoint):
    windows = json.loads(windows_path.read_text())
    if not isinstance(windows,list) or not windows or not all(isinstance(w,dict) for w in windows):
        raise ValueError('Windows must be a nonempty list of objects')
    for w in windows:
        if 'lon' in w or 'lat' in w:
            if not {'lon','lat'}.issubset(w) or not all(type(w[k]) in [int,float] for k in ['lon','lat']):
                raise ValueError('Coordinates require numeric lon and lat together')
            if not (-180 <= w['lon'] <= 180 and -90 <= w['lat'] <= 90):
                raise ValueError('Coordinates must be finite WGS84 lon/lat')
    data, details = prepare_observations(pd.read_parquet(observations), windows, source)
    if checkpoint.suffix == '.json':
        from orman_ssl.advanced import ensemble_predict
        predictions = ensemble_predict(checkpoint, data)
    else:
        predictions = predict(checkpoint, data)
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out/'input.npz', **data)
    (out/'predictions.json').write_text(json.dumps(predictions,indent=2))
    geo = []
    for i, window in enumerate(windows):
        if 'lon' not in window:
            continue
        cls = predictions['predictions'][i]
        geo.append(dict(type='Feature',geometry=dict(type='Point',coordinates=[window['lon'],window['lat']]),
                        properties=dict(id=window['id'],target_year=window['target_year'],
                            prediction=predictions['classes'][cls],clear_cut_score=predictions['probabilities'][i][1],
                            quality_eligible=predictions['quality_eligible'][i])))
    # Always write the current collection: reruns cannot leave stale map features.
    (out/'predictions.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=geo),indent=2))
    def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = dict(source=source, observations_sha256=digest(observations), windows_sha256=digest(windows_path),
                    checkpoint_sha256=digest(checkpoint), samples=details, n=len(details),
                    quality_eligible=sum(predictions['quality_eligible']), mapped_samples=len(geo),
                    input_sha256=digest(out/'input.npz'), predictions_sha256=digest(out/'predictions.json'))
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    return manifest


def main(default_checkpoint=None, default_output=None):
    parser = argparse.ArgumentParser(description='Raw observations -> monthly input -> trained model -> JSON + GeoJSON')
    parser.add_argument('--observations',type=Path,default=ROOT/'data/disfor/pixel_data.parquet')
    parser.add_argument('--windows',type=Path,default=ROOT/'data/examples/inference_windows.json')
    parser.add_argument('--checkpoint',type=Path,default=default_checkpoint or ROOT/'models/model.pt')
    parser.add_argument('--source',default=None)
    parser.add_argument('--out',type=Path,default=default_output or ROOT/'output/prediction')
    args = parser.parse_args()
    if args.source is None and args.observations.resolve() != (ROOT/'data/disfor/pixel_data.parquet').resolve():
        parser.error('Custom observations require --source describing source and DN processing history')
    source = args.source or 'JR-DIGITAL/DISFOR pinned revision 2562332e35c94c2339aeb341ffaed2a99faae7d6; source DN'
    try:
        result = run(args.observations,args.windows,source,args.out,args.checkpoint)
    except (ValueError,KeyError,FileNotFoundError) as exc:
        parser.error(str(exc))
    print(f'Tamamlandı: {result["n"]} örnek, {result["quality_eligible"]} kalite koşuluna uygun, {result["mapped_samples"]} harita noktası.')
    print('Çıktılar:',args.out.resolve())
    if args.windows.resolve() == (ROOT/'data/examples/inference_windows.json').resolve():
        print('Bu örnek mevcut test verisini tekrar işler; yeni bağımsız saha doğrulaması değildir.')
    else:
        print('Çıktılar model tahminidir; bağımsız doğruluk ölçümü yapılmadı.')

if __name__ == '__main__':
    main()
