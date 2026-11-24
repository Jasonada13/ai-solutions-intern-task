import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from models import OrderEvent, Refund
from package_submission import FILES, build_archive
from run import SUMMARY_COLUMNS, load_data, main, query_summary, write_quality, write_summary


def make_package_files(root):
    for name in FILES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("test file", encoding="utf-8")


class TestScaffold(unittest.TestCase):
    def test_fixtures_load_as_typed_records(self):
        events, refunds = load_data()
        self.assertTrue(events)
        self.assertTrue(refunds)
        self.assertTrue(all(isinstance(row, OrderEvent) for row in events))
        self.assertTrue(all(isinstance(row.revision, int) for row in events))
        self.assertTrue(all(isinstance(row.gross_pence, int) for row in events))
        self.assertTrue(all(isinstance(row, Refund) for row in refunds))
        self.assertTrue(all(isinstance(row.refund_pence, int) for row in refunds))

    def test_empty_summary_has_header(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "summary.csv"
            write_summary(path, [])
            with path.open(newline="") as handle:
                self.assertEqual(list(csv.reader(handle)), [list(SUMMARY_COLUMNS)])

    def test_summary_formats_rate(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "summary.csv"
            write_summary(path, [("web", 3, 900, 100, 800, 1, 1 / 3)])
            with path.open(newline="") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows[1], ["web", "3", "900", "100", "800", "1", "0.3333"])

    def test_summary_rejects_fractional_money(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "summary.csv"
            with self.assertRaisesRegex(ValueError, "must be integers"):
                write_summary(path, [("web", 3, 900.5, 100, 800.5, 1, 1 / 3)])

    def test_quality_writes_supplied_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "quality.json"
            write_quality(path, ["example"])
            self.assertEqual(json.loads(path.read_text()), {"conflicted_order_ids": ["example"]})

    def test_query_helper_binds_context(self):
        query = """
            SELECT :as_of AS channel, 0 AS completed_orders, 0 AS gross_pence,
                   0 AS refund_pence, 0 AS net_pence, 0 AS refunded_orders,
                   0.0 AS refund_rate
            WHERE :period_start = 'start' AND :period_end = 'end'
        """
        self.assertEqual(
            query_summary([], [], query, as_of="cutoff", period_start="start", period_end="end"),
            [("cutoff", 0, 0, 0, 0, 0, 0.0)],
        )

    def test_query_helper_rejects_wrong_columns(self):
        with self.assertRaisesRegex(ValueError, "must return these columns"):
            query_summary([], [], "SELECT 1")

    def test_failed_run_removes_both_stale_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = [root / "output/summary.csv", root / "output/quality.json"]
            paths[0].parent.mkdir()
            for path in paths:
                path.write_text("stale", encoding="utf-8")
            with patch("run.ROOT", root), patch("sys.argv", ["run.py", "--as-of", "invalid"]):
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(main(), 1)
            self.assertTrue(all(not path.exists() for path in paths))

    def test_package_requires_both_outputs(self):
        for missing in ("output/summary.csv", "output/quality.json"):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                make_package_files(root)
                (root / missing).unlink()
                (root / "submission.zip").write_text("stale", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, f"Missing {missing}"):
                    build_archive(root)
                self.assertFalse((root / "submission.zip").exists())

    def test_package_uses_only_task_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            make_package_files(root)
            (root / ".env").write_text("dummy secret", encoding="utf-8")
            with ZipFile(build_archive(root)) as archive:
                self.assertEqual(set(archive.namelist()), set(FILES))

    def test_package_removes_partial_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            make_package_files(root)
            with patch.object(ZipFile, "write", side_effect=OSError("write failed")):
                with self.assertRaisesRegex(OSError, "write failed"):
                    build_archive(root)
            self.assertFalse((root / "submission.zip").exists())


if __name__ == "__main__":
    unittest.main()
