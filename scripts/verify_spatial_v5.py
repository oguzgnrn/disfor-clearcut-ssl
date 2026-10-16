"""Reload every newly trained radius-sensitivity checkpoint and check its predictions."""
import argparse
import json
import platform
from pathlib import Path

import numpy as np
import torch

from scientific_v5 import OUT, ROOT, adv, analyze, context, digest, read, verify_signature, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tolerance', type=float, default=1e-7,
                        help='Maximum allowed reloaded-probability difference. 1e-7 expects the original training '
                             'environment; a cross-platform reload (different OS/torch build) needs about 1e-5.')
    args = parser.parse_args()
    verify_signature()
    # This also reconstructs every OOF vector and checks all fixed identifiers and metrics.
    analysis = analyze()
    data, _ = context()
    lookup = {identifier: i for i, identifier in enumerate(data['ids'])}
    results = []
    for file in sorted((OUT / 'runs').glob('*.json')):
        row = read(file)
        checkpoint = ROOT / row['checkpoint']
        if digest(checkpoint) != row['checkpoint_sha256']:
            raise ValueError('Checkpoint hash mismatch: ' + row['name'])
        test = np.array([lookup[i] for i in row['test_ids']])
        state = adv.load_state(checkpoint)
        actual = adv.state_probability(state, adv.view(data, test))
        expected = np.asarray(row['probabilities'])
        error = float(np.max(np.abs(actual - expected)))
        if error > args.tolerance:
            raise ValueError('Reloaded probability mismatch: ' + row['name'])
        results.append(dict(name=row['name'], samples=len(test), maximum_probability_difference=error))
    result = dict(status='passed', checked_checkpoints=len(results),
                  prediction_values=sum(r['samples'] for r in results),
                  maximum_probability_difference=max(r['maximum_probability_difference'] for r in results),
                  exact_prediction_runs=sum(r['maximum_probability_difference'] == 0 for r in results),
                  v4_and_v5_signatures='unchanged', tolerance=args.tolerance,
                  environment=dict(platform=platform.platform(), python=platform.python_version(), torch=torch.__version__),
                  results=results,
                  scope="Serialization/inference reload check in the recorded environment; cross-platform reloads differ at float32 noise level. Not new external validation or an additional training repetition.")
    write(OUT / 'checkpoint_verification.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'results'}, indent=2))


if __name__ == '__main__':
    main()
