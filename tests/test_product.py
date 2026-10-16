"""Data provenance, local HTTP boundary, and real-job lifecycle contracts."""
import http.client
import io
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("orman_product", ROOT / "scripts/serve_product.py")
product = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(product)


def fixture(root):
    """Small valid files, with a missing month that must never appear as zero."""
    out = root / "output/advanced_prediction"
    out.mkdir(parents=True)
    model = root / "models/advanced_v3"
    model.mkdir(parents=True)
    examples = root / "data/examples"
    examples.mkdir(parents=True)
    (root / "reports").mkdir()
    (root / "reports/product.html").write_text("<!doctype html><title>Local fixture</title>")
    (root / "docs").mkdir()
    (root / "docs/URUN_KILAVUZU.md").write_text("Yerel ürün kılavuzu")
    bundle = model / "bundle.json"
    bundle.write_text(json.dumps({"version": "advanced_v3", "members": [{"path": "a.pt"}], "threshold": .5}))
    identifiers = ["disfor-1-2020", "disfor-2-2021"]
    windows = [{"id": value, "sample_id": i + 1, "target_year": 2020 + i, "lon": 15 + i, "lat": 48 + i}
               for i, value in enumerate(identifiers)]
    windows_path = examples / "inference_windows.json"
    windows_path.write_text(json.dumps(windows))
    channels = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]
    x = np.full((2, 24, 10), 1500, dtype=np.float32)
    observed = np.ones(x.shape, dtype=bool)
    observed[0, 2] = False
    x[0, 2] = np.nan
    np.savez_compressed(out / "input.npz", x=x, observed=observed, ids=np.array(identifiers),
                        metadata=json.dumps({"channels": channels}))
    predictions = {"ids": identifiers, "predictions": [1, 0], "probabilities": [[.1, .9], [.8, .2]],
                   "member_std": [.1, .03], "quality_eligible": [True, True],
                   "classes": ["undisturbed_forest", "clear_cut"]}
    (out / "predictions.json").write_text(json.dumps(predictions))
    (out / "predictions.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": []}))
    manifest = {"checkpoint_sha256": product.digest(bundle), "input_sha256": product.digest(out / "input.npz"),
                "predictions_sha256": product.digest(out / "predictions.json"), "windows_sha256": product.digest(windows_path),
                "source": "Local fixture", "samples": [{"id": i, "observed_months": [11, 12]} for i in identifiers]}
    (out / "manifest.json").write_text(json.dumps(manifest))
    return out


class ProductDataContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.out = fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_missing_months_are_null_and_prediction_view_contains_no_labels(self):
        payload, series = product.load_dataset(self.root, self.out)
        self.assertEqual(payload["records"][0]["lon"], 15)
        self.assertEqual(payload["records"][0]["score"], .9)
        self.assertEqual(len(series["disfor-1-2020"]["months"]), 24)
        self.assertEqual(series["disfor-1-2020"]["months"][2]["B08"], None)
        self.assertEqual(series["disfor-1-2020"]["months"][2]["observed_bands"], 0)
        self.assertEqual(series["disfor-1-2020"]["months"][0]["month"], "2019-01")
        self.assertEqual(series["disfor-1-2020"]["months"][-1]["month"], "2020-12")
        for row in payload["records"]:
            self.assertNotIn("label", row)
            self.assertNotIn("target", row)
            self.assertNotIn("true_class", row)
        json.dumps(payload, allow_nan=False)
        json.dumps(series, allow_nan=False)

    def test_changed_model_or_output_is_rejected(self):
        for relative in ["models/advanced_v3/bundle.json", "output/advanced_prediction/predictions.json",
                         "output/advanced_prediction/input.npz", "data/examples/inference_windows.json"]:
            with self.subTest(file=relative):
                path = self.root / relative
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                try:
                    with self.assertRaises(ValueError):
                        product.load_dataset(self.root, self.out)
                finally:
                    path.write_bytes(original)

    def test_reordered_prediction_ids_rejected_even_with_valid_hash(self):
        path = self.out / "predictions.json"
        predictions = json.loads(path.read_text())
        predictions["ids"].reverse()
        path.write_text(json.dumps(predictions))
        manifest = product.read_json(self.out / "manifest.json")
        manifest["predictions_sha256"] = product.digest(path)
        (self.out / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            product.load_dataset(self.root, self.out)

    def test_frozen_real_data_has_486_label_free_aligned_records(self):
        if not (ROOT / "output/advanced_prediction/input.npz").exists():
            self.skipTest("Full project data is not installed")
        payload, series = product.load_dataset(ROOT, ROOT / "output/advanced_prediction")
        self.assertEqual(len(payload["records"]), 486)
        self.assertEqual(set(series), {r["id"] for r in payload["records"]})
        self.assertEqual(sum(r["prediction"] == "clear_cut" for r in payload["records"]), 28)
        self.assertTrue(all(0 <= r["score"] <= 1 for r in payload["records"]))
        self.assertTrue(all(-180 <= r["lon"] <= 180 and -90 <= r["lat"] <= 90 for r in payload["records"]))


class ProductHTTPContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        fixture(self.root)
        self.state = product.ProductState(self.root)
        self.server = product.ProductServer(("127.0.0.1", 0), self.state)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.host = f"127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def request(self, path, method="GET", body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def authorized(self):
        return {"Origin": "http://" + self.host, "X-Orman-Token": self.state.token}

    def test_bootstrap_and_series_respond_without_private_labels(self):
        status, headers, body = self.request("/api/bootstrap")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(len(payload["records"]), 2)
        self.assertEqual(payload["token"], self.state.token)
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertEqual(headers["Cache-Control"], "no-store")
        status, _, body = self.request("/api/series?id=disfor-1-2020")
        self.assertEqual(status, 200)
        self.assertIsNone(json.loads(body)["months"][2]["B04"])
        self.assertEqual(self.request("/api/series?id=missing")[0], 404)
        self.assertEqual(self.request("/api/series?id=a&id=b")[0], 400)

    def test_route_allowlist_blocks_paths_and_directory_listing(self):
        for path in ["/../README.md", "/%2e%2e/README.md", "/data/disfor/", "/.git/config",
                     "/download/../../README.md", "/api/series?id=../../README.md"]:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)
        self.assertEqual(self.request("/guide")[0], 200)
        status, headers, _ = self.request("/download/predictions.json")
        self.assertEqual(status, 200)
        self.assertIn("attachment", headers["Content-Disposition"])

    def test_foreign_host_origin_and_missing_token_cannot_start_job(self):
        with patch.object(self.state, "start") as start:
            self.assertEqual(self.request("/api/bootstrap", headers={"Host": "attacker.example"})[0], 403)
            self.assertEqual(self.request("/api/run", "POST")[0], 403)
            self.assertEqual(self.request("/api/run", "POST", headers={"Origin": "https://foreign.example", "X-Orman-Token": self.state.token})[0], 403)
            self.assertEqual(self.request("/api/run", "POST", headers={"Origin": "http://" + self.host, "X-Orman-Token": "wrong"})[0], 403)
            start.assert_not_called()

    def test_fixed_run_accepts_authorized_empty_post_only(self):
        with patch.object(self.state, "start", return_value=True) as start:
            self.assertEqual(self.request("/api/run", "POST", body="", headers=self.authorized())[0], 202)
            start.assert_called_once_with()
            self.assertEqual(self.request("/api/run", "POST", body='{"out":"/tmp/elsewhere"}', headers=self.authorized())[0], 400)
            self.assertEqual(self.request("/api/other", "POST", headers=self.authorized())[0], 404)
            self.assertEqual(start.call_count, 1)
        with patch.object(self.state, "start", return_value=False):
            self.assertEqual(self.request("/api/run", "POST", headers=self.authorized())[0], 409)

    def test_server_rejects_non_loopback_binding(self):
        with self.assertRaises(ValueError):
            product.ProductServer(("0.0.0.0", 0), self.state)


class ProductLifecycleContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.original_output = fixture(self.root)
        self.state = product.ProductState(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_only_one_job_can_run_and_no_symbolic_output_is_allowed(self):
        release = threading.Event()
        finished = threading.Event()
        def blocked():
            release.wait(3)
            finished.set()
        with patch.object(self.state, "_run", side_effect=blocked):
            try:
                self.assertTrue(self.state.start())
                self.assertFalse(self.state.start())
                self.assertEqual(self.state.snapshot()["state"], "running")
            finally:
                release.set()
                self.assertTrue(finished.wait(2))
        self.state.output.rmdir()
        self.state.output.symlink_to(self.original_output, target_is_directory=True)
        self.state.job["state"] = "idle"
        with self.assertRaises(ValueError):
            self.state.start()

    def _write_staged_fixture(self, command, **kwargs):
        staged = Path(command[command.index("--out") + 1])
        self.assertEqual(staged.parent, self.state.output)
        self.assertTrue(staged.name.startswith(".working-"))
        self.assertTrue(staged.is_dir())
        shutil.copytree(self.original_output, staged, dirs_exist_ok=True)
        return subprocess.CompletedProcess(command, 0)

    def test_success_uses_fixed_command_and_switches_to_verified_outputs(self):
        self.state.output.mkdir()
        with patch.object(product.subprocess, "run", side_effect=self._write_staged_fixture) as run:
            self.state._run()
        call = run.call_args
        self.assertEqual(call.args[0][:3], [sys.executable, str(self.root / "scripts/run_advanced.py"), "--out"])
        staged = Path(call.args[0][3])
        self.assertEqual(staged.parent, self.state.output)
        self.assertFalse(staged.exists())
        self.assertEqual(call.kwargs["cwd"], self.root)
        self.assertEqual(call.kwargs["timeout"], 600)
        self.assertEqual(self.state.snapshot()["state"], "completed")
        self.assertEqual(self.state.active_output, self.state.output)
        self.assertIsNotNone(self.state.snapshot()["finished_at"])
        for name in ("input.npz", "predictions.json", "predictions.geojson", "manifest.json"):
            self.assertEqual(product.digest(self.state.output / name), product.digest(self.original_output / name))

    def test_partial_failed_rerun_preserves_all_active_snapshot_hashes(self):
        self.state.output.mkdir()
        with patch.object(product.subprocess, "run", side_effect=self._write_staged_fixture):
            self.state._run()
        self.assertEqual(self.state.snapshot()["state"], "completed")
        active = self.state.active_output
        names = ("input.npz", "predictions.json", "predictions.geojson", "manifest.json")
        before = {name: product.digest(active / name) for name in names}
        original_records = self.state.bootstrap()["records"]
        for failure in ("nonzero_exit", "timeout", "invalid_success", "missing_geojson_success"):
            with self.subTest(failure=failure):
                def partial_failure(command, **kwargs):
                    staged = Path(command[command.index("--out") + 1])
                    self.assertNotEqual(staged, active)
                    if failure in ("invalid_success", "missing_geojson_success"):
                        shutil.copytree(self.original_output, staged, dirs_exist_ok=True)
                    if failure == "missing_geojson_success":
                        # Valid hashed input/predictions/manifest are insufficient:
                        # every downloadable output must exist before committing.
                        predictions = product.read_json(staged / "predictions.json")
                        predictions["probabilities"][0] = [.3, .7]
                        (staged / "predictions.json").write_text(json.dumps(predictions))
                        manifest = product.read_json(staged / "manifest.json")
                        manifest["predictions_sha256"] = product.digest(staged / "predictions.json")
                        (staged / "manifest.json").write_text(json.dumps(manifest))
                        self.assertNotEqual(manifest["predictions_sha256"], before["predictions.json"])
                        (staged / "predictions.geojson").unlink()
                        return subprocess.CompletedProcess(command, 0)
                    # A rerun can write some corrupt files before exiting; none
                    # may replace the last complete generation shown to users.
                    (staged / "predictions.json").write_text('{"ids": ["corrupt-partial-record"]}')
                    (staged / "predictions.geojson").write_text("unfinished")
                    if failure == "timeout":
                        raise subprocess.TimeoutExpired(command, 600)
                    return subprocess.CompletedProcess(command, 0 if failure == "invalid_success" else 1)
                with patch.object(product.subprocess, "run", side_effect=partial_failure):
                    self.state._run()
                self.assertEqual(self.state.snapshot()["state"], "failed")
                self.assertEqual(self.state.active_output, active)
                self.assertEqual({name: product.digest(active / name) for name in names}, before)
                self.assertEqual(self.state.bootstrap()["records"], original_records)
                self.assertEqual(list(self.state.output.glob(".working-*")), [])

    def test_failed_or_timed_out_job_preserves_previous_valid_results(self):
        self.state.output.mkdir()
        for result in [subprocess.CompletedProcess([], 1), subprocess.TimeoutExpired("inference", 600)]:
            with self.subTest(result=type(result).__name__):
                kwargs = {"side_effect": result} if isinstance(result, Exception) else {"return_value": result}
                with patch.object(product.subprocess, "run", **kwargs):
                    self.state._run()
                self.assertEqual(self.state.snapshot()["state"], "failed")
                self.assertEqual(self.state.active_output, self.original_output)
                self.assertEqual(len(self.state.bootstrap()["records"]), 2)


def upload_arrays():
    from orman_ssl.inputs import BANDS, UNITS, monthly_days
    observed = np.ones((2, 24, 10), dtype=bool)
    observed[0, 2] = False
    x = np.full((2, 24, 10), 1500, dtype=np.float32)
    x[0, 2] = np.nan
    return dict(x=x, observed=observed, days=np.stack([monthly_days(2020)] * 2),
                ids=np.array(["new-point-a", "new-point-b"]),
                metadata=np.array(json.dumps(dict(channels=BANDS, units=UNITS, source="Test DN source"))))


def upload_bytes(data=None):
    stream = io.BytesIO()
    np.savez_compressed(stream, **(upload_arrays() if data is None else data))
    return stream.getvalue()


class ProductUploadContracts(unittest.TestCase):
    def test_compatible_upload_without_coordinates_does_not_invent_them(self):
        data, source = product.validate_upload(upload_bytes())
        self.assertEqual(source, "Test DN source")
        self.assertNotIn("lon", data)
        self.assertNotIn("target_year", data)
        self.assertEqual(data["x"].shape, (2, 24, 10))

    def test_upload_rejects_model_contract_and_optional_metadata_errors(self):
        invalid = []
        data = upload_arrays(); data["ids"] = np.array(["same", "same"]); invalid.append(data)
        data = upload_arrays(); data["days"][0, 0] = 0; invalid.append(data)
        data = upload_arrays(); data["observed"] = data["observed"].astype(np.int8); invalid.append(data)
        data = upload_arrays(); data["y"] = np.array([0, 1]); invalid.append(data)
        data = upload_arrays(); data["ids"] = np.array(["object-a", "object-b"], dtype=object); invalid.append(data)
        data = upload_arrays(); metadata = json.loads(str(data["metadata"])); metadata["units"] = "reflectance"; data["metadata"] = np.array(json.dumps(metadata)); invalid.append(data)
        data = upload_arrays(); data["lon"] = np.array([3., 4.]); invalid.append(data)
        data = upload_arrays(); data["lon"] = np.array([3., 4.]); data["lat"] = np.array([95., 30.]); invalid.append(data)
        data = upload_arrays(); data["target_year"] = np.array([2019, 2019]); invalid.append(data)
        for i, data in enumerate(invalid):
            with self.subTest(case=i), self.assertRaises(ValueError):
                product.validate_upload(upload_bytes(data))

    def test_upload_checks_declared_array_allocation_before_loading(self):
        fake = io.BytesIO()
        np.lib.format.write_array_header_1_0(fake, {"descr": "<f4", "fortran_order": False, "shape": (10**12, 24, 10)})
        original = zipfile.ZipFile(io.BytesIO(upload_bytes()))
        malicious = io.BytesIO()
        with zipfile.ZipFile(malicious, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in original.namelist():
                archive.writestr(name, fake.getvalue() if name == "x.npy" else original.read(name))
        with patch.object(np, "load", side_effect=AssertionError("Array allocation must not run")):
            with self.assertRaises(ValueError):
                product.validate_upload(malicious.getvalue())

    def test_upload_rejects_duplicate_members_and_compressed_size_limits(self):
        original = zipfile.ZipFile(io.BytesIO(upload_bytes()))
        duplicate = io.BytesIO()
        with zipfile.ZipFile(duplicate, "w") as archive:
            for name in original.namelist():
                archive.writestr(name, original.read(name))
            with self.assertWarns(UserWarning):
                archive.writestr("x.npy", original.read("x.npy"))
        with self.assertRaises(ValueError):
            product.validate_upload(duplicate.getvalue())
        with patch("product_data.MAX_UPLOAD_BYTES", 100):
            with self.assertRaises(ValueError):
                product.validate_upload(upload_bytes())
        with patch("product_data.MAX_EXPANDED_BYTES", 100):
            with self.assertRaises(ValueError):
                product.validate_upload(upload_bytes())


class ProductUploadLifecycleContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.original = fixture(self.root)
        self.state = product.ProductState(self.root)
        self.directory = self.root / "output/product_uploads"
        self.directory.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def write_predictions(self, command, **kwargs):
        data_path = Path(command[command.index("--data") + 1])
        output = Path(command[command.index("--out") + 1])
        self.assertEqual(output.parent, data_path.parent)
        self.assertEqual(output.parent.parent, self.directory)
        with np.load(data_path, allow_pickle=False) as data:
            ids = data["ids"].tolist()
        output.write_text(json.dumps(dict(ids=ids, predictions=[1, 0], probabilities=[[.1, .9], [.8, .2]],
            member_std=[.1, .03], quality_eligible=[True, True], classes=["undisturbed_forest", "clear_cut"])))
        return subprocess.CompletedProcess(command, 0)

    def run_upload(self, blob=None):
        with patch.object(product.subprocess, "run", side_effect=self.write_predictions):
            self.state._run_upload(upload_bytes() if blob is None else blob, "Declared source DN", self.directory)
        self.assertEqual(self.state.snapshot()["state"], "completed")

    def test_real_state_commit_switch_and_missing_coordinates_dates(self):
        before = {name: product.digest(self.original / name) for name in product.OUTPUT_NAMES}
        self.run_upload()
        uploaded = self.state.active_output
        self.assertEqual(self.state.active_dataset, "upload")
        self.assertEqual(self.state.payload["source"], "Declared source DN")
        self.assertTrue(all(r["year"] is None and r["lon"] is None and r["lat"] is None for r in self.state.payload["records"]))
        self.assertEqual(self.state.series["new-point-a"]["months"][0]["month"], "Ay 01")
        self.assertIsNone(self.state.series["new-point-a"]["months"][2]["B08"])
        self.assertEqual(product.read_json(uploaded / "predictions.geojson")["features"], [])
        self.assertEqual({name: product.digest(self.original / name) for name in product.OUTPUT_NAMES}, before)
        self.assertTrue(self.state.activate("demo"))
        self.assertEqual(self.state.active_output, self.original)
        self.assertTrue(self.state.activate("upload"))
        self.assertEqual(self.state.active_output, uploaded)
        self.assertEqual({d["id"] for d in self.state.bootstrap()["datasets"]}, {"demo", "upload"})

    def test_optional_wgs84_years_generate_only_provided_geography(self):
        data = upload_arrays()
        data.update(lon=np.array([25.5, 25.6]), lat=np.array([39.5, 39.6]), target_year=np.array([2020, 2020]))
        self.run_upload(upload_bytes(data))
        geography = product.read_json(self.state.active_output / "predictions.geojson")
        self.assertEqual(geography["features"][0]["geometry"]["coordinates"], [25.5, 39.5])
        self.assertEqual(self.state.series["new-point-a"]["months"][0]["month"], "2019-01")
        self.assertEqual(geography["features"][0]["properties"]["target_year"], 2020)

    def test_failed_upload_cannot_damage_last_valid_upload_or_demo(self):
        self.run_upload()
        active = self.state.active_output
        before = {name: product.digest(active / name) for name in product.OUTPUT_NAMES}
        original_before = {name: product.digest(self.original / name) for name in product.OUTPUT_NAMES}
        def failed(command, **kwargs):
            Path(command[command.index("--out") + 1]).write_text("broken partial predictions")
            return subprocess.CompletedProcess(command, 1)
        with patch.object(product.subprocess, "run", side_effect=failed):
            self.state._run_upload(upload_bytes(), "Source", self.directory)
        self.assertEqual(self.state.snapshot()["state"], "failed")
        self.assertEqual(self.state.active_output, active)
        self.assertEqual({name: product.digest(active / name) for name in product.OUTPUT_NAMES}, before)
        self.assertEqual({name: product.digest(self.original / name) for name in product.OUTPUT_NAMES}, original_before)
        self.assertFalse(list(self.directory.glob(".working-*")))

    def test_switching_and_upload_start_are_blocked_while_job_runs(self):
        self.state.job["state"] = "running"
        self.assertFalse(self.state.activate("demo"))
        self.assertFalse(self.state.start_upload(upload_bytes()))
        self.state.job["state"] = "idle"
        with self.assertRaises(ValueError):
            self.state.activate("upload")
        self.directory.rmdir()
        self.directory.symlink_to(self.original, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.state.start_upload(upload_bytes())


class ProductUploadHTTPContracts(unittest.TestCase):
    setUp = ProductHTTPContracts.setUp
    tearDown = ProductHTTPContracts.tearDown
    request = ProductHTTPContracts.request
    authorized = ProductHTTPContracts.authorized

    def test_upload_rejects_foreign_origin_body_types_and_oversize_before_job(self):
        body = upload_bytes()
        headers = {**self.authorized(), "Content-Type": "application/octet-stream"}
        with patch.object(self.state, "start_upload") as start:
            self.assertEqual(self.request("/api/upload", "POST", body, {"Content-Type": "application/octet-stream"})[0], 403)
            self.assertEqual(self.request("/api/upload", "POST", body, {**headers, "Content-Type": "text/plain"})[0], 400)
            self.assertEqual(self.request("/api/upload", "POST", b"", headers)[0], 413)
            self.assertEqual(self.request("/api/upload", "POST", body, {**headers, "Content-Length": str(product.MAX_UPLOAD_BYTES + 1)})[0], 413)
            start.assert_not_called()
        with patch.object(self.state, "start_upload", return_value=True) as start:
            self.assertEqual(self.request("/api/upload", "POST", body, headers)[0], 202)
            self.assertEqual(start.call_args.args[0], body)
        self.assertEqual(self.request("/api/activate/demo", "POST", headers=self.authorized())[0], 200)
        self.assertEqual(self.request("/api/activate/upload", "POST", headers=self.authorized())[0], 400)

    def test_historical_evaluation_uses_demo_even_when_custom_ids_are_active(self):
        card = dict(benchmark_points=2, benchmark_positive_points=1, metrics={"macro_f1": .5},
                    paired_comparison={"macro_f1_95_interval": [.1, .9]})
        (self.root / "models/advanced_v3/model_card.json").write_text(json.dumps(card))
        (self.root / "data/disfor").mkdir()
        (self.root / "data/disfor/sample_manifest.json").write_text(json.dumps([
            {"id": "disfor-1-2020", "label": 1}, {"id": "disfor-2-2021", "label": 1}]))
        self.state.payload = {"records": [{"id": "user-record-not-in-benchmark", "prediction": "clear_cut", "score": .9}]}
        self.state.active_dataset = "upload"
        status, _, body = self.request("/api/evaluation")
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertEqual(result["n"], 2)
        self.assertEqual(result["errors"][0]["id"], "disfor-2-2021")



if __name__ == "__main__":
    unittest.main()
