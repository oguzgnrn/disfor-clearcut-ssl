#!/bin/sh
# Rebuild technical results. Document generation is explicit and optional.
set -eu
cd "$(dirname "$0")/.."
WITH_REPORTS=0
case "${1:-}" in
  '') ;;
  --with-reports) WITH_REPORTS=1 ;;
  *) echo 'Usage: bash scripts/reproduce.sh [--with-reports]' >&2; exit 2 ;;
esac
ORMAN_PYTHON=${ORMAN_PYTHON:-.venv/bin/python}
"$ORMAN_PYTHON" scripts/check_environment.py
if [ "$WITH_REPORTS" -eq 1 ]; then
  "$ORMAN_PYTHON" -c 'import reportlab, pypdf' || { echo 'Install requirements-report.txt first.' >&2; exit 1; }
fi
"$ORMAN_PYTHON" scripts/prepare_disfor.py
PYTHONPATH=src "$ORMAN_PYTHON" -m orman_ssl.experiment --data data/processed/real_series.npz --out reports/real_experiment
"$ORMAN_PYTHON" scripts/analyze_real.py
"$ORMAN_PYTHON" scripts/export_test_input.py
PYTHONPATH=src "$ORMAN_PYTHON" -m orman_ssl.predict --checkpoint models/model.pt --data data/processed/test_inference.npz --out reports/inference_cli.json
"$ORMAN_PYTHON" -m unittest discover -s tests -v
"$ORMAN_PYTHON" scripts/run_mvp.py
"$ORMAN_PYTHON" scripts/verify_inference.py
"$ORMAN_PYTHON" scripts/verify_outputs.py
if [ "$WITH_REPORTS" -eq 1 ]; then
  "$ORMAN_PYTHON" scripts/build_real_report.py
  "$ORMAN_PYTHON" scripts/build_final_pdf.py
  "$ORMAN_PYTHON" scripts/verify_final.py
fi
