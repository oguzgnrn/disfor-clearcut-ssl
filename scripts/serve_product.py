"""Offline Orman-SSL product. Fixed local routes and label-free demo inference."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import parse_qs, unquote, urlsplit
import webbrowser

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PRODUCT_VERSION = "1.1"
sys.path.insert(0, str(ROOT / "scripts"))
from product_data import MAX_UPLOAD_BYTES, MAX_EXPANDED_BYTES, MAX_SAMPLES, OUTPUT_NAMES, validate_upload, finish_uploaded_output


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_dataset(root, output):
    """Join frozen predictions to real geometry and observed-only bands by ID."""
    root, output = Path(root), Path(output)
    predictions = read_json(output / "predictions.json")
    manifest = read_json(output / "manifest.json")
    bundle_path = root / "models/advanced_v3/bundle.json"
    bundle = read_json(bundle_path)
    if manifest["checkpoint_sha256"] != digest(bundle_path):
        raise ValueError("Tahmin çıktısı ile model sürümü eşleşmiyor. Örnek analizi yeniden çalıştırın.")
    for key, name in (("predictions_sha256", "predictions.json"), ("input_sha256", "input.npz")):
        if manifest[key] != digest(output / name):
            raise ValueError("Çıktı bütünlük kontrolü başarısız: " + name)
    windows_path = root / "data/examples/inference_windows.json"
    if manifest["windows_sha256"] != digest(windows_path):
        raise ValueError("Örnek konumları ile tahmin çıktısı eşleşmiyor.")
    windows = {w["id"]: w for w in read_json(windows_path)}
    details = {d["id"]: d for d in manifest["samples"]}
    with np.load(output / "input.npz", allow_pickle=False) as archive:
        ids = archive["ids"].tolist()
        x, observed = archive["x"], archive["observed"]
        metadata = json.loads(str(archive["metadata"]))
    if ids != predictions["ids"] or len(set(ids)) != len(ids):
        raise ValueError("Girdi ve tahmin kimlikleri eşleşmiyor.")
    channels = metadata["channels"]
    records, series = [], {}
    for i, identifier in enumerate(ids):
        window = windows[identifier]
        detail = details[identifier]
        record = {
            "id": identifier, "sample_id": str(window["sample_id"]),
            "year": int(window["target_year"]), "lon": window.get("lon"), "lat": window.get("lat"),
            "prediction": predictions["classes"][predictions["predictions"][i]],
            "score": float(predictions["probabilities"][i][1]),
            "spread": float(predictions["member_std"][i]),
            "quality": bool(predictions["quality_eligible"][i]),
            "months": detail["observed_months"],
        }
        records.append(record)
        monthly = []
        for m in range(24):
            row = {"month": f"{record['year'] - 1 + m // 12}-{m % 12 + 1:02d}"}
            for band in ("B04", "B08", "B12"):
                c = channels.index(band)
                row[band] = float(x[i, m, c]) if observed[i, m, c] and np.isfinite(x[i, m, c]) else None
            row["observed_bands"] = int(observed[i, m].sum())
            monthly.append(row)
        series[identifier] = {"id": identifier, "months": monthly, "units": "Kaynak DN; yansıtım dönüşümü yapılmadı."}
    return {
        "product_version": PRODUCT_VERSION, "dataset_kind": "demo", "model_version": bundle["version"],
        "research_version": "paper_v4", "members": len(bundle["members"]),
        "threshold": bundle["threshold"], "data_revision": "2562332e35c94c2339aeb341ffaed2a99faae7d6",
        "source": manifest["source"], "source_license": "EUPL-1.2",
        "checkpoint_sha256": manifest["checkpoint_sha256"],
        "predictions_sha256": manifest["predictions_sha256"],
        "records": records,
    }, series


class ProductState:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.output = self.root / "output/product_demo"
        self.active_output = self.root / "output/advanced_prediction"
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.upload_lock = threading.Lock()
        self.job = {"state": "idle", "message": "Kayıtlı model çıktısı incelemeye hazır.", "started_at": None, "finished_at": None}
        self.payload, self.series = load_dataset(self.root, self.active_output)
        self.active_dataset = "demo"
        self.datasets = {"demo": (self.active_output, self.payload, self.series)}

    def snapshot(self):
        with self.lock:
            return {"product": "Orman-SSL", **self.job}

    def bootstrap(self):
        with self.lock:
            return {**self.payload, "token": self.token, "job": self.snapshot(),
                    "active_dataset": self.active_dataset,
                    "datasets": [{"id": key, "name": "Paketli demo" if key == "demo" else "Son yüklenen veri",
                                  "count": len(value[1]["records"])} for key, value in self.datasets.items()],
                    "upload_limits": {"bytes": MAX_UPLOAD_BYTES, "expanded_bytes": MAX_EXPANDED_BYTES, "samples": MAX_SAMPLES}}

    def activate(self, dataset):
        with self.lock:
            if self.job["state"] == "running":
                return False
            if dataset not in self.datasets:
                raise ValueError("Bu veri kümesi henüz yüklenmedi.")
            self.active_output, self.payload, self.series = self.datasets[dataset]
            self.active_dataset = dataset
            return True

    def start_upload(self, blob, declared_source=""):
        data, source = validate_upload(blob, declared_source)
        count = len(data["ids"])
        del data
        with self.lock:
            if self.job["state"] == "running":
                return False
            directory = self.root / "output/product_uploads"
            if directory.resolve() != directory or (directory.exists() and not directory.is_dir()):
                raise ValueError("Yükleme klasörü güvenli bir yerel klasör olmalıdır.")
            directory.mkdir(parents=True, exist_ok=True)
            self.job = {"state": "running", "kind": "upload", "message": f"Yüklenen {count} örnek için kayıtlı model çalışıyor.",
                        "started_at": datetime.now(timezone.utc).isoformat(), "finished_at": None}
            threading.Thread(target=self._run_upload, args=(blob, source, directory), daemon=True).start()
            return True

    def _run_upload(self, blob, source, directory):
        started = time.monotonic()
        try:
            environment = dict(os.environ, OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", PYTHONPATH=str(self.root / "src"))
            with tempfile.TemporaryDirectory(prefix=".working-", dir=directory) as temporary:
                staged = Path(temporary)
                (staged / "input.npz").write_bytes(blob)
                with (staged / "inference.log").open("w", encoding="utf-8") as log:
                    result = subprocess.run(
                        [sys.executable, "-m", "orman_ssl.predict_advanced", "--bundle", str(self.root / "models/advanced_v3/bundle.json"),
                         "--data", str(staged / "input.npz"), "--out", str(staged / "predictions.json")],
                        cwd=self.root, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=600, check=False)
                if result.returncode:
                    raise ValueError("Yüklenen veriyle analiz tamamlanamadı. Girdi sözleşmesini ve yerel model ortamını kontrol edin.")
                payload, series = finish_uploaded_output(self.root, staged, source)
                final = directory / ("run-" + secrets.token_hex(12))
                # One rename commits the complete generation. Existing outputs are immutable.
                with self.lock:
                    os.replace(staged, final)
                    self.datasets["upload"] = (final, payload, series)
                    self.active_output, self.payload, self.series = final, payload, series
                    self.active_dataset = "upload"
                    self.job.update(state="completed", message=f"Yüklenen {len(payload['records'])} örnek için tahmin üretildi; doğruluk ölçümü yapılmadı.",
                                    elapsed_seconds=round(time.monotonic() - started, 2))
        except subprocess.TimeoutExpired:
            with self.lock:
                self.job.update(state="failed", message="Yüklenen veri analizi 10 dakika içinde tamamlanamadı. Önceki sonuçlar korundu.")
        except Exception as exc:
            with self.lock:
                self.job.update(state="failed", message=str(exc))
        finally:
            with self.lock:
                self.job["finished_at"] = datetime.now(timezone.utc).isoformat()

    def start(self):
        with self.lock:
            if self.job["state"] == "running":
                return False
            # This fixed output is the only directory the application can modify.
            if self.output.resolve() != self.output or (self.output.exists() and not self.output.is_dir()):
                raise ValueError("Demo çıktı klasörü güvenli bir yerel klasör olmalıdır.")
            if self.output.exists() and any(p.is_symlink() for p in self.output.iterdir()):
                raise ValueError("Demo çıktı klasöründe sembolik bağlantı kullanılamaz.")
            self.output.mkdir(parents=True, exist_ok=True)
            self.job = {"state": "running", "kind": "demo", "message": "Ham gözlemler işleniyor; 10 eğitimli model tahmin üretiyor.",
                        "started_at": datetime.now(timezone.utc).isoformat(), "finished_at": None}
            threading.Thread(target=self._run, daemon=True).start()
            return True

    def _run(self):
        started = time.monotonic()
        try:
            environment = dict(os.environ, OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
            # Validate a complete generation before replacing the downloadable
            # snapshot. A failed or concurrent rerun cannot expose mixed files.
            with tempfile.TemporaryDirectory(prefix=".working-", dir=self.output) as temporary:
                staged = Path(temporary)
                with (self.output / "inference.log").open("w", encoding="utf-8") as log:
                    result = subprocess.run(
                        [sys.executable, str(self.root / "scripts/run_advanced.py"), "--out", str(staged)],
                        cwd=self.root, env=environment, stdout=log, stderr=subprocess.STDOUT,
                        timeout=600, check=False,
                    )
                if result.returncode:
                    raise RuntimeError("Analiz tamamlanamadı. output/product_demo/inference.log dosyasını inceleyin.")
                payload, series = load_dataset(self.root, staged)
                names = ["input.npz", "predictions.json", "predictions.geojson", "manifest.json"]
                for name in names:
                    if not (staged / name).is_file():
                        raise ValueError("Analiz çıktısı eksik: " + name)
                geography = read_json(staged / "predictions.geojson")
                if geography.get("type") != "FeatureCollection" or not isinstance(geography.get("features"), list):
                    raise ValueError("GeoJSON çıktısı geçerli bir nokta koleksiyonu değil.")
                with self.lock:
                    for name in names:
                        os.replace(staged / name, self.output / name)
                    self.active_output, self.payload, self.series = self.output, payload, series
                    self.datasets["demo"] = (self.output, payload, series)
                    self.active_dataset = "demo"
                    self.job.update(state="completed", message=f"{len(payload['records'])} örnek ham veriden yeniden işlendi.",
                                    elapsed_seconds=round(time.monotonic() - started, 2))
        except subprocess.TimeoutExpired:
            with self.lock:
                self.job.update(state="failed", message="Analiz 10 dakika içinde tamamlanamadı. Yerel kaynakları kontrol edin.")
        except Exception as exc:
            with self.lock:
                self.job.update(state="failed", message=str(exc))
        finally:
            with self.lock:
                self.job["finished_at"] = datetime.now(timezone.utc).isoformat()


class ProductServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, state):
        if address[0] != "127.0.0.1":
            raise ValueError("Ürün yalnızca 127.0.0.1 adresinde çalışır.")
        self.state = state
        super().__init__(address, ProductHandler)


class ProductHandler(BaseHTTPRequestHandler):
    server_version = "OrmanSSL/1.0"

    def log_message(self, fmt, *args):
        return  # Keep the launch terminal focused on instructions and errors.

    def _host_ok(self):
        port = self.server.server_port
        return self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def _send(self, body, status=200, content_type="application/json; charset=utf-8", filename=None):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self._host_ok():
            return self._send({"error": "Yalnızca yerel erişim desteklenir."}, 403)
        route = urlsplit(self.path)
        state = self.server.state
        try:
            if route.path in ("/", "/product.html"):
                return self._send((state.root / "reports/product.html").read_bytes(), content_type="text/html; charset=utf-8")
            if route.path == "/favicon.ico":
                return self._send(b"", 204, "image/x-icon")
            if route.path == "/api/bootstrap":
                return self._send(state.bootstrap())
            if route.path == "/api/status":
                return self._send(state.snapshot())
            if route.path == "/api/series":
                params = parse_qs(route.query)
                if set(params) != {"id"} or len(params["id"]) != 1:
                    return self._send({"error": "Tek bir örnek kimliği gerekli."}, 400)
                with state.lock:
                    series = state.series.get(params["id"][0])
                return self._send(series or {"error": "Örnek bulunamadı."}, 200 if series else 404)
            if route.path == "/api/evaluation":
                card = read_json(state.root / "models/advanced_v3/model_card.json")
                references = {r["id"]: r["label"] for r in read_json(state.root / "data/disfor/sample_manifest.json")}
                with state.lock:
                    errors = [{"id": r["id"], "reference": int(references[r["id"]]),
                               "prediction": r["prediction"], "score": r["score"]}
                              for r in state.datasets["demo"][1]["records"]
                              if int(references[r["id"]]) != int(r["prediction"] == "clear_cut")]
                return self._send({"model": "advanced_v3", "n": card["benchmark_points"],
                                   "positive_n": card["benchmark_positive_points"], "metrics": card["metrics"],
                                   "interval": card["paired_comparison"]["macro_f1_95_interval"], "errors": errors,
                                   "status": "Önceden incelenmiş tarihsel test; bağımsız dış saha doğrulaması değildir."})
            if route.path == "/download/example.npz":
                return self._send((state.root / "data/processed/test_inference.npz").read_bytes(), content_type="application/octet-stream", filename="orman_ssl_example.npz")
            downloads = {"/download/predictions.json": "predictions.json", "/download/predictions.geojson": "predictions.geojson",
                         "/download/manifest.json": "manifest.json"}
            if route.path in downloads:
                name = downloads[route.path]
                with state.lock:
                    data = (state.active_output / name).read_bytes()
                return self._send(data, filename="orman_ssl_" + name)
            if route.path == "/guide":
                return self._send((state.root / "docs/URUN_KILAVUZU.md").read_bytes(), content_type="text/plain; charset=utf-8")
            if route.path == "/research":
                return self._send((state.root / "reports/paper_v4.html").read_bytes(), content_type="text/html; charset=utf-8")
            # Exact routes keep links in the offline research page usable without
            # turning the server into a general filesystem browser.
            public = {
                "/output/pdf/Orman_SSL_Manuscript.pdf": "application/pdf",
                "/output/paper/Orman_SSL_Manuscript.docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "/output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf": "application/pdf",
                "/output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "/paper/HOCAYA_NOT.md": "text/plain; charset=utf-8",
                "/paper/SUPPLEMENT.md": "text/plain; charset=utf-8",
                "/paper/ERROR_AUDIT.md": "text/plain; charset=utf-8",
                "/paper/figures/02_controls.png": "image/png",
                "/experiments/paper_v4/analysis.json": "application/json",
                "/experiments/paper_v4/review_candidates.geojson": "application/geo+json",
                "/docs/GORUSME_AKISI_VE_SORULAR.md": "text/plain; charset=utf-8",
            }
            if route.path in public:
                return self._send((state.root / route.path.lstrip('/')).read_bytes(), content_type=public[route.path])
            return self._send({"error": "Sayfa bulunamadı."}, 404)
        except (OSError, ValueError, KeyError):
            return self._send({"error": "Yerel veri okunamadı. Ürün kılavuzundaki kurulum adımlarını kontrol edin."}, 500)

    def do_POST(self):
        if not self._host_ok():
            return self._send({"error": "Yalnızca yerel erişim desteklenir."}, 403)
        expected = f"http://{self.headers.get('Host')}"
        if self.headers.get("Origin") != expected or self.headers.get("X-Orman-Token") != self.server.state.token:
            return self._send({"error": "İstek doğrulanamadı. Ürün sayfasını yenileyin."}, 403)
        state = self.server.state
        if self.path == "/api/upload":
            self.close_connection = True
            if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Type") != "application/octet-stream":
                return self._send({"error": "Yükleme standart NPZ dosyası olmalıdır."}, 400)
            lengths = self.headers.get_all("Content-Length", [])
            try:
                length = int(lengths[0]) if len(lengths) == 1 else -1
            except ValueError:
                length = -1
            if not 0 < length <= MAX_UPLOAD_BYTES:
                return self._send({"error": "Dosya boş olamaz; en fazla 16 MiB yüklenebilir."}, 413)
            if not state.upload_lock.acquire(blocking=False):
                return self._send({"error": "Başka bir yükleme işleniyor; tamamlanmasını bekleyin."}, 409)
            try:
                if state.snapshot()["state"] == "running":
                    return self._send({"error": "Devam eden analiz tamamlandıktan sonra yükleyin."}, 409)
                encoded_source = self.headers.get("X-Orman-Source", "")
                if len(encoded_source) > 12000:
                    raise ValueError("Kaynak açıklaması çok uzun.")
                source = unquote(encoded_source, errors="strict")
                self.connection.settimeout(20)
                blob = self.rfile.read(length)
                if len(blob) != length:
                    raise ValueError("Dosya eksik ulaştı; tekrar seçin.")
                started = state.start_upload(blob, source)
                return self._send(state.snapshot(), 202 if started else 409)
            except (ValueError, UnicodeError, OSError) as exc:
                return self._send({"error": str(exc)}, 400)
            finally:
                state.upload_lock.release()
        if self.path not in ("/api/run", "/api/activate/demo", "/api/activate/upload"):
            return self._send({"error": "İşlem bulunamadı."}, 404)
        if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Length", "0") != "0":
            return self._send({"error": "Bu işlem ek girdi kabul etmez."}, 400)
        try:
            if self.path.startswith("/api/activate/"):
                changed = state.activate(self.path.rsplit("/", 1)[1])
                return self._send(state.bootstrap() if changed else {"error": "Devam eden analizin tamamlanmasını bekleyin."}, 200 if changed else 409)
            started = state.start()
            return self._send(state.snapshot(), 202 if started else 409)
        except ValueError as exc:
            return self._send({"error": str(exc)}, 400)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Tarayıcıyı aç")
    args = parser.parse_args()
    try:
        state = ProductState()
        server = ProductServer(("127.0.0.1", args.port), state)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Ürün başlatılamadı: {exc}\nKurulum: docs/URUN_KILAVUZU.md\n")
    address = f"http://127.0.0.1:{server.server_port}"
    print(f"Orman-SSL · Yerel araştırma ürünü\n{address}\nBu pencere açık kalsın. Durdurmak için Ctrl+C.", flush=True)
    if args.open:
        threading.Timer(0.4, lambda: webbrowser.open(address)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nÜrün kapatıldı.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
