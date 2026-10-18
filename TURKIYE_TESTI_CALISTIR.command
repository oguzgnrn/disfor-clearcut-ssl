#!/bin/bash
# Mac'te çift tıkla: Avrupa'da eğitilmiş modelleri hiç yeniden eğitmeden Türkiye noktalarında test eder.
# İnternet gerekir (Hansen GFC, Earth Search STAC ve Sentinel-2 COG arşivi). Süre: fetch aşaması 30-90 dk.
cd "$(dirname "$0")"
PY=.venv/bin/python
$PY scripts/turkiye_zero_shot.py prepare || exit 1
$PY scripts/turkiye_zero_shot.py fetch --workers 8 || exit 1
$PY scripts/turkiye_zero_shot.py build || exit 1
$PY scripts/turkiye_zero_shot.py predict --full-cohort-recipes || exit 1
$PY scripts/turkiye_zero_shot.py report
echo; echo "Bitti. Sonuç: experiments/turkiye_zero_shot/RESULTS.md ve analysis.json"
read -p "Kapatmak için Enter'a bas"
