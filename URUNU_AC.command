#!/bin/bash
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "Orman-SSL ortamı bulunamadı. Önce: bash scripts/setup.sh"
  echo "Ayrıntılar: docs/URUN_KILAVUZU.md"
  read -r -p "Kapatmak için Enter... "
  exit 1
fi
.venv/bin/python scripts/serve_product.py --open
