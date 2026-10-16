#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ -z "${PYTHON_BIN:-}" ]; then
  if command -v python3.11 >/dev/null 2>&1; then PYTHON_BIN=python3.11; else PYTHON_BIN=python3; fi
fi
"$PYTHON_BIN" -c 'import sys; assert sys.version_info[:2] == (3,11), "Python 3.11 gereklidir"'
if [ ! -x .venv/bin/python ]; then
  "$PYTHON_BIN" -m venv .venv
fi
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python scripts/check_environment.py
