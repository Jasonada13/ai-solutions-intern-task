import csv
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from package_submission import FILES, build_archive
from run import SUMMARY_COLUMNS, load_data, write_summary


class TestScaffold(unittest.TestCase):
    def test_fixtures_load(self):
        orders, refunds = load_data()
        self.assertTrue(orders)
        self.assertTrue(refunds)
        self.assertTrue(all(isinstance(row[2], int) for row in refunds))

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

    def test_package_requires_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in FILES:
                if name != "output/summary.csv":
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("test file", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing output/summary.csv"):
                build_archive(root)
            self.assertFalse((root / "submission.zip").exists())

    def test_package_uses_only_task_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in FILES:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("test file", encoding="utf-8")
            (root / ".env").write_text("dummy secret", encoding="utf-8")
            with ZipFile(build_archive(root)) as archive:
                self.assertEqual(set(archive.namelist()), set(FILES))


if __name__ == "__main__":
    unittest.main()
