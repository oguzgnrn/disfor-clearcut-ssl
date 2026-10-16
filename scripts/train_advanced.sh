#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
ORMAN_PYTHON=${ORMAN_PYTHON:-.venv/bin/python}
"$ORMAN_PYTHON" scripts/check_environment.py
PYTHONPATH=src "$ORMAN_PYTHON" -m orman_ssl.advanced --stage all
"$ORMAN_PYTHON" scripts/evaluate_advanced.py
"$ORMAN_PYTHON" scripts/run_advanced.py
"$ORMAN_PYTHON" scripts/verify_advanced.py
"$ORMAN_PYTHON" scripts/build_advanced_card.py
"$ORMAN_PYTHON" scripts/plot_advanced.py
"$ORMAN_PYTHON" -m unittest discover -s tests -v
