"""Verify the final local research/product delivery; check ZIPs after packaging."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
import zipfile

import numpy as np

from verify_package import verify

ROOT = Path(__file__).resolve().parents[1]
REPORT = "output/final/Orman_SSL_Arastirma_ve_Urun_Raporu"
ARCHIVES = ["Orman_SSL_Paper_Paketi.zip", "Orman_SSL_Nihai_Model.zip",
            "Orman_SSL_Hocaya_Sunum.zip", "Orman_SSL_Proje_Paketi.zip"]


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write(name, result):
    (ROOT / name).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(arguments):
    result = subprocess.run([sys.executable, *arguments], cwd=ROOT, text=True, capture_output=True, timeout=600)
    require(result.returncode == 0, "Command failed: " + " ".join(arguments) + "\n" + result.stdout + result.stderr)
    return result


def core():
    result = {"status": "passed", "checked_at": datetime.now(timezone.utc).isoformat()}
    tests = run(["-m", "unittest", "discover", "-s", "tests", "-v"])
    log = tests.stdout + tests.stderr
    (ROOT / "reports/final_delivery_tests.log").write_text(log, encoding="utf-8")
    count = re.search(r"Ran (\d+) tests? in ([\d.]+)s", log)
    require(count is not None and "\nOK\n" in log, "Missing successful unittest summary")
    result["tests"] = {"count": int(count[1]), "failures": 0, "seconds": float(count[2]),
                       "log": "reports/final_delivery_tests.log"}
    result["environment"] = {"status": "passed", "message": run(["scripts/check_environment.py"]).stdout.strip()}
    result["scientific_records"] = json.loads(run(["scripts/verify_paper.py"]).stdout)
    result["trained_model"] = json.loads(run(["scripts/verify_advanced.py"]).stdout)

    from serve_product import load_dataset
    payload, series = load_dataset(ROOT, ROOT / "output/product_demo")
    saved = read("output/advanced_prediction/predictions.json")
    actual = read("output/product_demo/predictions.json")
    require(actual["ids"] == saved["ids"] and actual["predictions"] == saved["predictions"], "Product IDs/classes differ")
    difference = float(np.max(np.abs(np.asarray(actual["probabilities"]) - np.asarray(saved["probabilities"]))))
    require(difference == 0, "Product probability mismatch")
    with np.load(ROOT / "output/product_demo/input.npz", allow_pickle=False) as fresh, np.load(ROOT / "output/advanced_prediction/input.npz", allow_pickle=False) as old:
        for key in ["x", "observed", "days", "ids"]:
            np.testing.assert_array_equal(fresh[key], old[key], err_msg=key)
    require(read("output/product_demo/predictions.geojson") == read("output/advanced_prediction/predictions.geojson"), "Product GeoJSON mismatch")
    require(len(series) == len(payload["records"]) == 486, "Unexpected product cohort")
    result["real_product_run"] = {"samples": len(series), "maximum_probability_difference": difference,
                                   "raw_inputs_and_geojson": "identical to frozen reference",
                                   "provenance": "output/product_demo/manifest.json",
                                   "note": "Browser-triggered real inference on previously examined data; not new validation or retraining."}

    qa = read("reports/final_report_document_qa.json")
    for extension in ["pdf", "docx"]:
        require(sha(ROOT / (REPORT + "." + extension)) == qa[extension + "_sha256"], "Document changed after visual QA")
    from pypdf import PdfReader
    actual_pages = len(PdfReader(str(ROOT / (REPORT + ".pdf"))).pages)
    require(qa["status"] == "passed" and qa["pages"] == actual_pages, "Document QA incomplete or page count drifted")
    result["document"] = qa
    ui = read("reports/product_ui_verification.json")
    require(ui["status"] == "passed", "UI verification incomplete")
    # The 1 October upload feature re-verified the UI sources; its record supersedes the 30 September hashes.
    upload = read("reports/product_upload_verification.json")
    require(upload["status"] == "passed", "Upload verification incomplete")
    for name, expected in upload["source_sha256"].items():
        require(sha(ROOT / name) == expected, "UI code changed after upload verification: " + name)
    result["browser"] = {"ui_verification": ui, "upload_verification": upload,
                         "note": "Source hashes checked against the later upload verification record."}
    required = ["README.md", "URUNU_AC.command", "docs/GORUSME_AKISI_VE_SORULAR.md",
                "docs/URUN_KILAVUZU.md", "docs/ARASTIRMA_VE_URUN_RAPORU.md",
                "docs/NIHAI_BILIMSEL_DENETIM.md", "docs/NIHAI_TEKNIK_DENETIM.md",
                "reports/final_science_review.json", "reports/final_engineering_review.json",
                "output/paper/Orman_SSL_Manuscript.docx", "output/pdf/Orman_SSL_Manuscript.pdf"]
    require(all((ROOT / name).is_file() for name in required), "Required delivery file missing")
    result["delivery_files"] = {name: sha(ROOT / name) for name in required}
    result["scope"] = "Local macOS CPU checks; 180 existing fits audited, one fit freshly reproduced in the archive smoke check; no external field validation."
    write("reports/final_delivery_verification.json", result)
    return result


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attributes):
        for key, value in attributes:
            if key in {"href", "src"} and value:
                self.links.append(value)


def archives():
    result = {"status": "passed", "checked_at": datetime.now(timezone.utc).isoformat(), "archives": {}}
    for filename in ARCHIVES:
        path = ROOT / "output" / filename
        checked = verify(path)
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            manifest = json.loads(z.read("Orman_SSL/PACKAGE_MANIFEST.json"))
            for row in manifest:
                # Compact archives intentionally have their own entry document.
                if row["path"] == "README.md" and filename != "Orman_SSL_Proje_Paketi.zip":
                    continue
                if row["path"] == "SUNUM_PAKETI.txt" and filename == "Orman_SSL_Hocaya_Sunum.zip":
                    continue
                current = ROOT / row["path"]
                require(current.is_file() and sha(current) == row["sha256"], filename + " stale file: " + row["path"])
            checked["matches_current_workspace"] = True
            if "Orman_SSL/reports/paper_v4.html" in names:
                parser = Links()
                parser.feed(z.read("Orman_SSL/reports/paper_v4.html").decode())
                for link in parser.links:
                    url = urlsplit(link)
                    if not url.scheme and not url.netloc and url.path:
                        target = posixpath.normpath(posixpath.join("Orman_SSL/reports", unquote(url.path)))
                        require(target in names, filename + " broken paper link: " + link)
                checked["paper_hub_links"] = "passed"
            if filename in {"Orman_SSL_Hocaya_Sunum.zip", "Orman_SSL_Proje_Paketi.zip"}:
                for item in [REPORT + ".pdf", REPORT + ".docx", "docs/GORUSME_AKISI_VE_SORULAR.md", "reports/final_delivery_verification.json"]:
                    require("Orman_SSL/" + item in names, filename + " missing final artifact: " + item)
            if filename == "Orman_SSL_Proje_Paketi.zip":
                for item in ["URUNU_AC.command", "scripts/serve_product.py", "reports/product.html", "tests/test_product.py", "models/advanced_v3/bundle.json", "output/product_demo/predictions.json"]:
                    require("Orman_SSL/" + item in names, "Full archive missing product file: " + item)
            checked.update(bytes=path.stat().st_size, sha256=sha(path))
        result["archives"][filename] = checked
    smoke = read("output/paper_package_smoke.json")
    require(smoke["status"] == "passed" and smoke["archive_sha256"] == result["archives"][ARCHIVES[0]]["sha256"], "Fresh fit smoke test is for an older paper archive")
    result["isolated_archive_training"] = smoke
    result["core_evidence_sha256"] = sha(ROOT / "reports/final_delivery_verification.json")
    # Keep this outside the archives to avoid self-referential hashes.
    write("output/final_release_verification.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archives", action="store_true", help="Validate packaged artifacts after core verification and packaging")
    args = parser.parse_args()
    print(json.dumps(archives() if args.archives else core(), ensure_ascii=False, indent=2))
