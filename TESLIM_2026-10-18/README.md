# TESLİM — 18 Ekim 2026

Bu klasör, Nida Hoca görüşmesi öncesi istenen üç şeyi içerir. Hepsi proje kökündeki kod ve kayıtlardan üretildi; sayılar elle yazılmadı.

| # | Dosya | Ne |
|---|---|---|
| 1 | `Orman_SSL_Proje_Defteri.ipynb` / `.html` | Bütün kod yolu tek defterde, açıklamalı ve **çalıştırılmış çıktılarıyla**: veri hazırlama, mekânsal katlar, etiket bütçesi, model kaynak kodları, canlı demo eğitimi, 180+75+225 koşunun bütün tabloları, bootstrap, şekiller, ürün modeliyle gerçek çıkarım, doğrulama. HTML'i tarayıcıda aç; kodu çalıştırmak için `.venv/bin/python -m jupyter lab TESLIM_2026-10-18/Orman_SSL_Proje_Defteri.ipynb` |
| 2 | `Orman_SSL_Makale_Guneren_Kumbasar.pdf` / `.docx` | Yazarlı makale taslağı (M. O. Güneren, N. Kumbasar): 7 bölüm, 6 tablo, 5 şekil, 26 kaynak, katkı ve yapay zekâ beyanı. **Nida Hoca'nın yazarlığı onayı alınmadan dışarı gönderilmez.** |
| 3a | `Orman_SSL_Tablolar_ve_Sonuclar_Rehberi.pdf` / `.docx` | Her tablo + altında "ne söylüyor" yorumu (Türkçe) |
| 3b | `Orman_SSL_Yontem_Sozlugu_ve_Dosya_Haritasi.pdf` / `.docx` | Bütün terimler (İngilizce) ve açıklamaları, veri akışı, hangi dosya ne için |
| — | `figures/` | Makaledeki 5 şekil + defterin örnek seri grafiği |

Üretim kodu: `scripts/build_notebook.py`, `scripts/compose_paper.py` (`ORMAN_AUTHORED=1`), `scripts/build_paper_docx.py`, `scripts/build_understanding_docs.py`. PDF'ler LibreOffice ile DOCX'ten alındı.
