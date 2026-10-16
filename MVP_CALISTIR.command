#!/bin/zsh
set -eu
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo 'Önce bash scripts/setup.sh komutuyla proje ortamını kurun.'
  exit 1
fi
.venv/bin/python scripts/run_mvp.py "$@"
