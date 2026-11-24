"""Supplied plumbing checks. These do not certify the candidate's business logic."""
import contextlib
import csv
import io
import json
import shutil
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
        self.assertIn("No completed orders were returned", empty)
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
            (root / "README.md").symlink_to(ROOT / "README.md")
            with self.assertRaisesRegex(ValueError, "regular file"):
                build_archive(root)


if __name__ == "__main__":
    unittest.main()
