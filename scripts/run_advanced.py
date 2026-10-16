"""Use the final advanced ensemble on label-free raw observations."""
from pathlib import Path
from run_mvp import main
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    main(default_checkpoint=ROOT/'models/advanced_v3/bundle.json',default_output=ROOT/'output/advanced_prediction')
