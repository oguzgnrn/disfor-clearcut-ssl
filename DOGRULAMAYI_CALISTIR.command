#!/bin/bash
# Mac'te çift tıkla: proje ortamıyla bütün doğrulamaları çalıştırır ve sonucu reports/ altına yazar.
cd "$(dirname "$0")"
PY=.venv/bin/python
echo "== Testler =="; $PY -m unittest discover -s tests 2>&1 | tail -4
echo "== paper_v4 kayıt doğrulaması =="; $PY scripts/verify_paper.py | tail -3
echo "== paper_v5 checkpoint doğrulaması (aynı ortam, 1e-7) =="; $PY scripts/verify_spatial_v5.py | head -8
echo "== paper_v6 analiz tekrar hesabı =="; $PY scripts/label_curve_v6.py analyze | head -3
echo "== Nihai teslim doğrulaması =="; $PY scripts/verify_final_delivery.py | head -12
echo "== Arşiv doğrulaması =="; $PY scripts/verify_final_delivery.py --archives | head -12
echo; echo "Bitti. Kayıtlar: reports/final_delivery_verification.json, experiments/paper_v5_exploratory/checkpoint_verification.json"
read -p "Kapatmak için Enter'a bas"
