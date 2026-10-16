"""Bounded, pickle-free NPZ uploads and presentation data for the local product."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from orman_ssl.inputs import BANDS, monthly_days, validate_input

MAX_UPLOAD_BYTES = 16 * 1024 * 1024
MAX_EXPANDED_BYTES = 64 * 1024 * 1024
MAX_SAMPLES = 5000
REQUIRED = {"x", "observed", "days", "ids", "metadata"}
OPTIONAL = {"lon", "lat", "target_year"}
OUTPUT_NAMES = ("input.npz", "predictions.json", "predictions.geojson", "manifest.json")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_upload(blob, declared_source=""):
    """Inspect all array headers before NumPy allocates any untrusted arrays."""
    if not blob or len(blob) > MAX_UPLOAD_BYTES:
        raise ValueError("NPZ dosyası boş olamaz ve 16 MiB sınırını aşamaz.")
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            allowed = {key + ".npy" for key in REQUIRED | OPTIONAL}
            if len(names) != len(set(names)) or not set(names).issubset(allowed):
                raise ValueError("Yalnız x, observed, days, ids, metadata ve isteğe bağlı lon, lat, target_year alanları kabul edilir. Etiket alanlarını yüklemeyin.")
            if not {key + ".npy" for key in REQUIRED}.issubset(names):
                raise ValueError("NPZ içinde x, observed, days, ids ve metadata alanları gerekli.")
            if sum(entry.file_size for entry in entries) > MAX_EXPANDED_BYTES:
                raise ValueError("Açılmış NPZ boyutu 64 MiB sınırını aşıyor.")
            for entry in entries:
                if entry.flag_bits & 1 or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    raise ValueError("Şifrelenmemiş standart NPZ dosyası gerekli.")
                with archive.open(entry) as stream:
                    version = np.lib.format.read_magic(stream)
                    if version == (1, 0):
                        shape, _, dtype = np.lib.format.read_array_header_1_0(stream)
                    elif version == (2, 0):
                        shape, _, dtype = np.lib.format.read_array_header_2_0(stream)
                    else:
                        raise ValueError("Desteklenmeyen NPY biçimi; standart NumPy NPZ kullanın.")
                    if dtype.hasobject or dtype.fields is not None:
                        raise ValueError("Nesne dizileri kabul edilmez; pickle kullanılmaz.")
                    array_bytes = math.prod(shape) * dtype.itemsize
                    if array_bytes > MAX_EXPANDED_BYTES or array_bytes != entry.file_size - stream.tell():
                        raise ValueError("Dizi boyutu ile dosya içeriği uyuşmuyor.")
                    key = entry.filename[:-4]
                    if key == "x" and (len(shape) != 3 or not 1 <= shape[0] <= MAX_SAMPLES or shape[1:] != (24, 10)):
                        raise ValueError("x biçimi [N,24,10] ve örnek sayısı 1–5000 olmalıdır.")
                    if key == "ids" and (len(shape) != 1 or dtype.kind != "U" or dtype.itemsize > 512):
                        raise ValueError("ids, en fazla 128 karakterlik Unicode kimliklerden oluşmalıdır.")
                    if key == "metadata" and (shape != () or dtype.kind != "U" or dtype.itemsize > 65536):
                        raise ValueError("metadata, en fazla 16.384 karakterlik tek bir JSON metni olmalıdır.")
        with np.load(io.BytesIO(blob), allow_pickle=False) as archive:
            data = {key: archive[key] for key in archive.files}
        metadata = validate_input(data)
    except (OSError, EOFError, zipfile.BadZipFile, KeyError, TypeError, OverflowError) as exc:
        raise ValueError("Geçerli, etiketsiz bir NumPy NPZ dosyası seçin.") from exc
    except ValueError as exc:
        # Existing model validation remains the authoritative band/time/unit contract.
        translations = {
            "Channel order differs from training": "Bant sırası eğitimdeki B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12 sırasıyla aynı olmalı.",
            "Explicit source DN units are required; reflectance/SAR values are incompatible": "metadata.units kaynak DN sözleşmesiyle aynı olmalı; yansıtım veya SAR değerleri kabul edilmez.",
            "IDs must be unique": "Her örneğin ids kimliği farklı olmalı.",
            "observed must be bool and match x": "observed, x ile aynı boyutta doğru/yanlış değerlerinden oluşmalı.",
            "Observed values must be finite; all-missing samples are invalid": "Her örnekte gözlem bulunmalı; gözlenen hücrelerde NaN veya sonsuz değer olamaz.",
            "days must encode the 15th of each month in two full calendar years": "days, iki tam takvim yılındaki her ayın 15. gününü kodlamalı.",
        }
        raise ValueError("Girdi sözleşmesi: " + translations.get(str(exc), str(exc))) from exc
    n = len(data["ids"])
    if any(any(ord(char) < 32 for char in identifier) for identifier in data["ids"].tolist()):
        raise ValueError("Kimliklerde kontrol karakteri kullanılamaz.")
    source = declared_source.strip() or metadata.get("source", "")
    if not isinstance(source, str) or not source.strip() or len(source) > 1000 or any(ord(c) < 32 for c in source):
        raise ValueError("Verinin kaynağını ve DN işleme geçmişini en fazla 1000 karakterle belirtin.")
    if ("lon" in data) != ("lat" in data):
        raise ValueError("Konum için lon ve lat birlikte verilmelidir.")
    for key, limit in (("lon", 180), ("lat", 90)):
        if key in data:
            array = data[key]
            if array.shape != (n,) or array.dtype.kind not in "fiu" or not np.isfinite(array).all() or ((array < -limit) | (array > limit)).any():
                raise ValueError(f"{key}, N uzunluğunda sonlu WGS84 koordinat dizisi olmalıdır.")
    if "target_year" in data:
        years = data["target_year"]
        if years.shape != (n,) or years.dtype.kind not in "iu" or (years < 1901).any() or (years > 9998).any():
            raise ValueError("target_year, N uzunluğunda 1901–9998 arası tam sayı dizisi olmalıdır.")
        for year in np.unique(years):
            if not np.isclose(data["days"][years == year], monthly_days(int(year)), atol=.001, rtol=0).all():
                raise ValueError("target_year ile days takvimi uyuşmuyor.")
    return data, source.strip()


def finish_uploaded_output(root, staged, declared_source):
    """Build geometry/manifest and label-free view from a completed inference."""
    root, staged = Path(root), Path(staged)
    data, source = validate_upload((staged / "input.npz").read_bytes(), declared_source)
    predictions = json.loads((staged / "predictions.json").read_text())
    bundle_path = root / "models/advanced_v3/bundle.json"
    bundle = json.loads(bundle_path.read_text())
    ids = data["ids"].tolist()
    if predictions.get("ids") != ids or predictions.get("classes") != ["undisturbed_forest", "clear_cut"]:
        raise ValueError("Tahmin kimlikleri veya sınıflar girdiyle eşleşmiyor.")
    for key in ("predictions", "probabilities", "member_std", "quality_eligible"):
        if len(predictions.get(key, [])) != len(ids):
            raise ValueError("Tahmin çıktısının örnek sayısı uyuşmuyor.")
    records, series, features = [], {}, []
    for i, identifier in enumerate(ids):
        probability = predictions["probabilities"][i]
        if len(probability) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 1 for v in probability) or not math.isclose(sum(probability), 1, abs_tol=1e-5):
            raise ValueError("Model skorları geçerli değil.")
        prediction, spread = predictions["predictions"][i], predictions["member_std"][i]
        if type(prediction) is not int or prediction not in (0, 1) or not isinstance(spread, (int, float)) or not math.isfinite(spread) or spread < 0:
            raise ValueError("Tahmin sınıfı veya üye farkı geçerli değil.")
        year = int(data["target_year"][i]) if "target_year" in data else None
        lon, lat = (float(data[k][i]) if k in data else None for k in ("lon", "lat"))
        months = [int(data["observed"][i, start:start + 12].any(-1).sum()) for start in (0, 12)]
        eligible = min(months) >= 6
        if predictions["quality_eligible"][i] is not eligible:
            raise ValueError("Tahmin kalite bayrağı girdi maskesiyle eşleşmiyor.")
        record = dict(id=identifier, sample_id=identifier, year=year, lon=lon, lat=lat,
                      prediction=predictions["classes"][prediction], score=float(probability[1]),
                      spread=float(spread), quality=eligible, months=months)
        records.append(record)
        monthly = []
        for month in range(24):
            row = {"month": f"{year - 1 + month // 12}-{month % 12 + 1:02d}" if year else f"Ay {month + 1:02d}",
                   "label": f"{(year - 1 + month // 12) % 100:02d}/{month % 12 + 1:02d}" if year else f"{month + 1}. ay",
                   "observed_bands": int(data["observed"][i, month].sum())}
            for band in ("B04", "B08", "B12"):
                channel = BANDS.index(band)
                row[band] = float(data["x"][i, month, channel]) if data["observed"][i, month, channel] else None
            monthly.append(row)
        series[identifier] = dict(id=identifier, months=monthly, units="Kullanıcının beyan ettiği kaynak DN; fiziksel uyum ayrıca doğrulanmalıdır.")
        if lon is not None:
            properties = dict(id=identifier, prediction=record["prediction"], clear_cut_score=record["score"], quality_eligible=eligible)
            if year is not None:
                properties["target_year"] = year
            features.append(dict(type="Feature", geometry=dict(type="Point", coordinates=[lon, lat]), properties=properties))
    geography = dict(type="FeatureCollection", features=features)
    (staged / "predictions.geojson").write_text(json.dumps(geography, ensure_ascii=False, indent=2, allow_nan=False))
    manifest = dict(kind="user_upload", source=source, created_at=datetime.now(timezone.utc).isoformat(),
                    n=len(ids), quality_eligible=sum(r["quality"] for r in records), mapped_samples=len(features),
                    checkpoint_sha256=sha256(bundle_path), input_sha256=sha256(staged / "input.npz"),
                    predictions_sha256=sha256(staged / "predictions.json"),
                    geojson_sha256=sha256(staged / "predictions.geojson"),
                    note="User-provided unlabeled NPZ inference. Source/DN compatibility is a declaration, not field validation.")
    (staged / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False))
    payload = dict(product_version="1.1", model_version=bundle["version"], research_version="paper_v4",
                   members=len(bundle["members"]), threshold=bundle["threshold"], dataset_kind="upload",
                   data_revision=None, source=source, source_license="Kullanıcının kendi veri kaynağı",
                   checkpoint_sha256=manifest["checkpoint_sha256"], predictions_sha256=manifest["predictions_sha256"], records=records)
    return payload, series
