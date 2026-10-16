"""Inference from an unlabeled prepared NPZ using the frozen advanced ensemble."""
import argparse
from pathlib import Path
import numpy as np
from .advanced import ensemble_predict,write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True,type=Path)
    parser.add_argument('--data',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    try:
        with np.load(args.data,allow_pickle=False) as archive:
            data={k:archive[k] for k in archive.files}
        result=ensemble_predict(args.bundle,data)
    except (ValueError,KeyError,FileNotFoundError) as exc:
        parser.error(str(exc))
    write_json(args.out,result)
    print('Advanced ensemble predicted',len(result['ids']),'samples')

if __name__=='__main__':main()
