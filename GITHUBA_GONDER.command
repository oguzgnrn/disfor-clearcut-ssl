#!/bin/bash
# Projeyi GitHub'a (oguzgnrn/disfor-clearcut-ssl) gonderir. Cift tiklayinca Terminal'de calisir.
cd "$(dirname "$0")" || exit 1
rm -f .git/index.lock .git/HEAD.lock .git/objects/maintenance.lock 2>/dev/null
git remote get-url origin >/dev/null 2>&1 || git remote add origin https://github.com/oguzgnrn/disfor-clearcut-ssl.git
git branch -M main
echo "GitHub'a gonderiliyor (kullanici adi/sifre sorarsa GitHub kullanici adin ve bir Personal Access Token gir)..."
git push -u origin main && echo "TAMAM: https://github.com/oguzgnrn/disfor-clearcut-ssl" || echo "HATA: push basarisiz; yukaridaki mesaji Claude'a yapistir."
echo; read -r -p "Kapatmak icin Enter'a bas..." _
