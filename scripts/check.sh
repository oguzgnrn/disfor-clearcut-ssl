#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
ORMAN_PYTHON=${ORMAN_PYTHON:-.venv/bin/python}
"$ORMAN_PYTHON" scripts/check_environment.py
"$ORMAN_PYTHON" -m unittest discover -s tests -v
"$ORMAN_PYTHON" scripts/run_mvp.py
"$ORMAN_PYTHON" scripts/verify_inference.py
