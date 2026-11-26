"""Tests for the supplied pipeline. Candidate tests cover the business calculations."""
import contextlib
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import run
from generate_data import generate_data, sha256
from models import Order, Product, RawOrder, Refund
from package_submission import FILES, build_archive
from report import business_notes, render_report

ROOT = Path(__file__).resolve().parents[1]
EMPTY_QUERY = "SELECT " + ", ".join(
    ("'baseline'" if i == 0 else "'web'" if i == 1 else "'home'" if i == 2 else "0")
    + f" AS {name}" for i, name in enumerate(run.COLUMNS)) + " WHERE 0"


def copy_task(folder):
    root = Path(folder)
    for name in FILES:
        if not name.startswith("output/"):
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
    return root


class TestScaffold(unittest.TestCase):
    def test_generator_repeatable_with_manifest_counts(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = generate_data(Path(first), 200, 7)
            two = generate_data(Path(second), 200, 7)
            self.assertEqual(one, two)
            for name, meta in one.items():
                path = Path(first) / name
                with path.open(newline="", encoding="utf-8") as source:
                    self.assertEqual(sum(1 for _ in csv.reader(source)) - 1, meta["rows"])
                self.assertEqual(meta["sha256"], sha256(path))
            self.assertEqual(len(list(run.iter_orders(Path(first) / "orders.csv"))), one["orders.csv"]["rows"])
            self.assertTrue(all(isinstance(p, Product) for p in run.load_products(Path(first) / "products.csv")))
            self.assertTrue(all(isinstance(r, Refund) for r in run.iter_refunds(Path(first) / "refunds.csv")))

    def test_generator_empty_and_negative(self):
        with tempfile.TemporaryDirectory() as folder:
            result = generate_data(Path(folder), 0, 42)
            self.assertEqual(result["orders.csv"]["rows"], 0)
            self.assertEqual(result["refunds.csv"]["rows"], 0)
            with self.assertRaises(ValueError):
                generate_data(Path(folder), -1, 42)

    def test_reader_rejects_wrong_header_or_width(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "orders.csv"
            path.write_text("incorrect\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                list(run.iter_orders(path))
            path.write_text(",".join(RawOrder._fields) + "\nonly,three,values\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                list(run.iter_orders(path))

    def test_query_helper_empty_schema_and_file_database(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "nested/task.sqlite"
            for _ in range(2):
                self.assertEqual(run.query_summary([], [], [], EMPTY_QUERY, db_path=database), [])
                self.assertTrue(database.is_file())

    def test_query_helper_rejects_wrong_columns_or_types(self):
        with self.assertRaises(ValueError):
            run.query_summary([], [], [], "SELECT 1")
        wrong_type = EMPTY_QUERY.removesuffix(" WHERE 0").replace("0 AS gross_pence", "0.5 AS gross_pence")
        with self.assertRaises(ValueError):
            run.query_summary([], [], [], wrong_type)

    def test_business_notes_excludes_prompts_and_technical_section(self):
        notes = "## Business recommendation\n<!-- Guidance -->\nA business action.\n## Method and scale\nPrivate technical method"
        self.assertEqual(business_notes(notes), "A business action.")

    def test_report_empty_zero_negative_and_escaping(self):
        quality = dict.fromkeys(("input_rows", "accepted_orders", "duplicate_rows", "rejected_rows", "invalid_values", "unknown_product"), 0)
        empty = render_report(run.COLUMNS, [], quality, "")
        self.assertIn("Recommendation not supplied.", empty)
        self.assertIn("The query returned no completed orders", empty)
        self.assertIn("n/a", empty)
        rows = [("current", "<script>alert(1)</script>", "home&away", 1, 100, 100, 0, 100, 50, -150, 1)]
        html = render_report(run.COLUMNS, rows, quality,
                             "## Business recommendation\n<img src=x onerror=alert(2)>\n## Method and scale\nSECRET METHOD")
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("SECRET METHOD", html)
        self.assertIn("&lt;img", html)
        self.assertIn("home&amp;away", html)
        self.assertIn("−£1.50", html)

    def test_pipeline_proof_manifest_and_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = copy_task(folder)
            with patch.object(run, "ROOT", root), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run.main(["--orders", "0", "--check-repro"]), 0)
            output = root / "output"
            proof = json.loads((output / "reproducibility.json").read_text())
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertIs(proof["matched"], True)
            self.assertEqual(proof["hashes"], {name: sha256(output / name) for name in run.COMPARED_FILES})
            self.assertEqual(manifest["base_orders"], 0)
            self.assertEqual(set(manifest["candidate_files"]), set(run.CANDIDATE_FILES))
            self.assertEqual((output / "summary.csv").read_text().splitlines(), [",".join(run.COLUMNS)])
            with ZipFile(build_archive(root)) as archive:
                self.assertEqual(set(archive.namelist()), set(FILES))
                self.assertFalse(any(name.startswith("data/") and name.endswith(".csv") for name in archive.namelist()))
            (root / "NOTES.md").write_text("changed notes", encoding="utf-8")
            with self.assertRaises(ValueError):
                build_archive(root)
            self.assertFalse((root / "submission.zip").exists())

    def test_failure_and_single_run_remove_stale_proof(self):
        with tempfile.TemporaryDirectory() as folder:
            root = copy_task(folder)
            with patch.object(run, "ROOT", root), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(run.main(["--orders", "0", "--check-repro"]), 0)
                self.assertEqual(run.main(["--orders", "0"]), 0)
                self.assertFalse((root / "output/reproducibility.json").exists())
                (root / "analysis.sql").write_text("invalid SQL", encoding="utf-8")
                self.assertEqual(run.main(["--orders", "0"]), 1)
                self.assertFalse(any((root / "output" / name).exists() for name in run.OUTPUT_FILES))
                self.assertEqual(run.main(["--orders", "-1"]), 1)

    def test_repro_mismatch_does_not_leave_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = copy_task(folder)
            with patch.object(run, "ROOT", root), patch.object(run, "run_once", side_effect=[{"a": "one"}, {"a": "two"}]), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(run.main(["--orders", "0", "--check-repro"]), 1)
                self.assertFalse(any((root / "output" / name).exists() for name in run.OUTPUT_FILES))

    def test_archive_missing_file_and_symlink_remove_stale_zip(self):
        with tempfile.TemporaryDirectory() as folder:
            root = copy_task(folder)
            (root / "submission.zip").write_bytes(b"stale")
            with self.assertRaises(ValueError):
                build_archive(root)
            self.assertFalse((root / "submission.zip").exists())
            (root / "README.md").unlink()
            try:
                (root / "README.md").symlink_to(ROOT / "README.md")
            except (NotImplementedError, OSError):
                self.skipTest("Creating symlinks is unavailable in this environment")
            with self.assertRaisesRegex(ValueError, "regular file"):
                build_archive(root)

    def test_cli_reports_preserve_bytes_and_extracted_pipeline(self):
        with tempfile.TemporaryDirectory() as folder:
            root = copy_task(Path(folder).resolve() / "task")
            with patch.object(run, "ROOT", root), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run.main(["--orders", "0", "--check-repro"]), 0)
            command = [sys.executable, str(root / "package_submission.py")]
            result = subprocess.run(command, cwd=root.parent, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            with ZipFile(root / "submission.zip") as archive:
                self.assertEqual(set(archive.namelist()), set(FILES))

            reports = root / "chosen reports"
            reports.mkdir()
            primary = reports / "Business story.boardpack"
            preview = reports / "Readable preview.pdf"
            primary.write_bytes(b"\x00Arbitrary report format\xff\n")
            preview.write_bytes(b"%PDF-1.4\nCandidate-provided preview bytes\n")
            expected_hashes = {name: sha256(root / "output" / name) for name in run.OUTPUT_FILES}
            result = subprocess.run(command + [
                "--business-report", "chosen reports/Business story.boardpack",
                "--report-preview", str(preview),
            ], cwd=root.parent, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            extracted = root.parent / "extracted"
            with ZipFile(root / "submission.zip") as archive:
                self.assertEqual(set(archive.namelist()), set(FILES) | {
                    "business-report/Business story.boardpack", "business-report/preview/Readable preview.pdf",
                })
                self.assertEqual(archive.read("business-report/Business story.boardpack"), primary.read_bytes())
                self.assertEqual(archive.read("business-report/preview/Readable preview.pdf"), preview.read_bytes())
                archive.extractall(extracted)
            result = subprocess.run([sys.executable, str(extracted / "run.py"), "--orders", "0", "--check-repro"],
                                    cwd=extracted, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual({name: sha256(extracted / "output" / name) for name in run.OUTPUT_FILES}, expected_hashes)
            self.assertEqual((extracted / "business-report/Business story.boardpack").read_bytes(), primary.read_bytes())
            self.assertEqual((extracted / "business-report/preview/Readable preview.pdf").read_bytes(), preview.read_bytes())

    def test_report_roles_allow_equal_basenames_and_primary_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = copy_task(Path(folder).resolve())
            with patch.object(run, "ROOT", root), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run.main(["--orders", "0", "--check-repro"]), 0)
            primary = root / "primary/report.pptx"
            preview = root / "preview/report.pptx"
            primary.parent.mkdir()
            preview.parent.mkdir()
            primary.write_bytes(b"Primary report bytes")
            preview.write_bytes(b"Separate preview bytes")
            with ZipFile(build_archive(root, business_report=primary)) as archive:
                self.assertEqual(set(archive.namelist()), set(FILES) | {"business-report/report.pptx"})
            with ZipFile(build_archive(root, business_report=primary, report_preview=preview)) as archive:
                self.assertEqual(archive.read("business-report/report.pptx"), primary.read_bytes())
                self.assertEqual(archive.read("business-report/preview/report.pptx"), preview.read_bytes())
                self.assertEqual(len(archive.namelist()), len(FILES) + 2)

    def test_invalid_report_cli_removes_stale_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = copy_task(Path(folder).resolve())
            with patch.object(run, "ROOT", root), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run.main(["--orders", "0", "--check-repro"]), 0)
            valid = root / "valid.pbix"
            valid.write_bytes(b"Report bytes")
            (root / "empty.pdf").touch()
            (root / "directory").mkdir()
            (root / "directory/report.pdf").write_bytes(b"Preview bytes")
            (root / "preview").write_bytes(b"Would conflict with the preview directory")
            cases = [
                ["--business-report", "missing.pbix"],
                ["--business-report", "empty.pdf"],
                ["--business-report", "directory"],
                ["--business-report", "submission.zip"],
                ["--business-report", "valid.pbix", "--report-preview", "missing.pdf"],
                ["--report-preview", "valid.pbix"],
                ["--business-report", "preview", "--report-preview", "valid.pbix"],
            ]
            if os.name != "nt":
                (root / "unsafe\\name.pdf").write_bytes(b"Unsafe filename")
                cases.append(["--business-report", "unsafe\\name.pdf"])
            try:
                (root / "symlink.pbix").symlink_to(valid)
                (root / "linked-directory").symlink_to(root / "directory", target_is_directory=True)
            except (NotImplementedError, OSError):
                pass
            else:
                cases.extend((["--business-report", "symlink.pbix"],
                              ["--business-report", "linked-directory/report.pdf"]))
            for arguments in cases:
                with self.subTest(arguments=arguments):
                    archive = root / "submission.zip"
                    archive.write_bytes(b"stale archive")
                    result = subprocess.run([sys.executable, str(root / "package_submission.py"), *arguments],
                                            cwd=root, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertIn("Unable to package submission:", result.stderr)
                    self.assertFalse(archive.exists())


if __name__ == "__main__":
    unittest.main()
