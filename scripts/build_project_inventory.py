"""List every durable project file, with absolute locations, for the owner."""

from __future__ import annotations

from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "docs" / "TUM_DOSYALAR_ENVANTERI.md"
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    ".venv-repro",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "tmp",
    "node_modules",
}
EXCLUDE_FILES = {".DS_Store"}
HEADINGS = {
    "assets": "Fontlar ve diğer varlıklar",
    "data": "Kaynak ve işlenmiş veri",
    "docs": "Belgeler ve rehberler",
    "experiments": "Deneyler ve eğitim kayıtları",
    "external_validation": "Bağımsız değerlendirme hazırlığı",
    "figures": "Şekiller",
    "models": "Eğitilmiş modeller",
    "output": "Üretilmiş sonuçlar ve teslim paketleri",
    "paper": "Makale kaynakları",
    "reports": "Doğrulama, analiz ve HTML raporları",
    "scripts": "Çalıştırma, analiz ve üretim betikleri",
    "src": "Model ve çıkarım kaynak kodu",
    "tests": "Otomatik testler",
    "third_party": "Üçüncü taraf kaynaklar",
}


def fmt_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024**2:
        return f"{size / 1024:.1f} KiB"
    return f"{size / 1024**2:.1f} MiB"


def files() -> list[Path]:
    result = []
    for top in ROOT.iterdir():
        if top.name in EXCLUDE_DIRS or top.name in EXCLUDE_FILES:
            continue
        if top.is_file():
            result.append(top)
            continue
        if not top.is_dir():
            continue
        for candidate in top.rglob("*"):
            if any(part in EXCLUDE_DIRS for part in candidate.relative_to(ROOT).parts):
                continue
            if candidate.is_file() and candidate.name not in EXCLUDE_FILES:
                result.append(candidate)
    return sorted(result, key=lambda p: str(p.relative_to(ROOT)).casefold())


def main() -> None:
    paths = files()
    groups: dict[str, list[Path]] = {}
    for path in paths:
        parts = path.relative_to(ROOT).parts
        group = parts[0] if len(parts) > 1 else "_root"
        groups.setdefault(group, []).append(path)

    lines = [
        "# Orman-SSL — bütün kalıcı proje dosyaları",
        "",
        "Bu liste proje ana klasöründeki her kalıcı dosyanın **tam konumunu** verir. "
        "Dosya adını tıklayarak açabilirsin. Sayı ve boyutlar envanter oluşturulduğu andaki durumdur.",
        "",
        f"**Proje kökü:** `{ROOT}`",
        "",
        "**Kapsam:** Kaynak kodu, veriler, eğitilmiş ağırlıklar, her deney kaydı, "
        "raporlar, MD dosyaları, PDF/DOCX belgeleri, görseller ve ZIP teslimleri. "
        "`.git`, `.venv`, `tmp`, `__pycache__`, `node_modules` gibi sürüm geçmişi, "
        "kurulum ortamı veya geçici üretim klasörleri ile macOS `.DS_Store` dosyaları dahil değildir. "
        "Bunlar bilimsel teslimin kaynak dosyaları değildir.",
        "",
        "**Güncel okuma sırası:** [proje açıklaması](PROJENIN_TAM_HARITASI.md) → "
        "[15 sayfalık öğrenme rehberi](../output/egitim/Orman_SSL_15_Sayfada_Proje_Rehberi.pdf) → "
        "[Türkçe sonuç raporu](../output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf) → "
        "[İngilizce makale](../output/pdf/Orman_SSL_Manuscript.pdf).",
        "",
        f"**Toplam:** {len(paths)} dosya.",
        "",
        "| Klasör | Dosya |",
        "|---|---:|",
    ]
    for group, entries in sorted(groups.items()):
        label = "Proje kökü" if group == "_root" else group
        lines.append(f"| {label} | {len(entries)} |")
    lines += ["", "Her bölümde dosyalar alfabetiktir. Aynı dosyanın `output/Orman_SSL/` "
              "içindeki kopyası ayrıca listelenir. Tarihsel deneyler de saklandığı için "
              "**listede bulunmak, dosyanın güncel ana sonuç olduğu anlamına gelmez**.", ""]

    for group, entries in sorted(groups.items()):
        title = "Proje kökündeki dosyalar" if group == "_root" else HEADINGS.get(group, group)
        lines += [f"## {title} — {len(entries)} dosya", "", "| Dosya ve tam bağlantı | Boyut |", "|---|---:|"]
        for path in entries:
            rel = path.relative_to(ROOT).as_posix()
            target = path.as_posix().replace("%", "%25").replace("(", "%28").replace(")", "%29")
            size = "—" if path == DESTINATION else fmt_size(path.stat().st_size)
            lines.append(f"| [{rel}](<{target}>) | {size} |")
        lines.append("")
    DESTINATION.write_text("\n".join(lines), encoding="utf-8")
    suffix = Counter(p.suffix.lower() or "[uzantısız]" for p in paths)
    print(f"{DESTINATION}: {len(paths)} files; " + ", ".join(f"{s}={n}" for s, n in suffix.most_common(10)))


if __name__ == "__main__":
    main()
