#!/bin/zsh
set -eu
cd "$(dirname "$0")"
if [[ -x .venv-repro/bin/python ]]; then
  ORMAN_PYTHON=.venv-repro/bin/python
elif [[ -x .venv/bin/python ]]; then
  ORMAN_PYTHON=.venv/bin/python
else
  echo 'Önce bash scripts/setup.sh ile Python ortamını kurun.'
  exit 1
fi
"$ORMAN_PYTHON" scripts/run_advanced.py "$@"
