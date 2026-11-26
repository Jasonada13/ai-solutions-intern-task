"""Generate data and run the analysis. Keep business calculations in analysis.sql."""
import argparse
import csv
import json
import platform
import sqlite3
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path

from generate_data import DEFAULT_ORDERS, DEFAULT_SEED, GENERATOR_VERSION, PERIODS, generate_data, sha256
from models import Order, Product, RawOrder, Refund
from report import render_report

ROOT = Path(__file__).resolve().parent
COLUMNS = (
    "period", "channel", "category", "completed_orders", "gross_pence", "refund_pence",
    "net_revenue_pence", "product_cost_pence", "fulfilment_cost_pence",
    "contribution_pence", "refunded_orders",
)
CANDIDATE_FILES = ("solution.py", "analysis.sql", "tests/test_candidate.py", "NOTES.md")
COMPARED_FILES = ("summary.csv", "quality.json", "report.html", "manifest.json")
OUTPUT_FILES = (*COMPARED_FILES, "reproducibility.json")
SCHEMA = """
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY, period TEXT NOT NULL, channel TEXT NOT NULL,
    status TEXT NOT NULL, product_id TEXT NOT NULL, quantity INTEGER NOT NULL,
    gross_pence INTEGER NOT NULL, fulfilment_cost_pence INTEGER NOT NULL
);
CREATE TABLE products (
    product_id TEXT PRIMARY KEY, category TEXT NOT NULL, unit_cost_pence INTEGER NOT NULL
);
CREATE TABLE refunds (
    refund_id TEXT NOT NULL, order_id TEXT NOT NULL, refund_pence INTEGER NOT NULL
);
CREATE INDEX refunds_order_id ON refunds(order_id);
"""


def iter_csv(path: Path, fields: tuple[str, ...]):
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.reader(source)
        if next(reader, None) != list(fields):
            raise ValueError(f"Unexpected columns in {path.name}")
        for line, row in enumerate(reader, 2):
            if len(row) != len(fields):
                raise ValueError(f"Unexpected field count in {path.name}, line {line}")
            yield row


def iter_orders(path: Path) -> Iterable[RawOrder]:
    return (RawOrder(*row) for row in iter_csv(path, RawOrder._fields))


def load_products(path: Path) -> list[Product]:
    return [Product(row[0], row[1], int(row[2])) for row in iter_csv(path, Product._fields)]


def iter_refunds(path: Path) -> Iterable[Refund]:
    return (Refund(row[0], row[1], int(row[2])) for row in iter_csv(path, Refund._fields))


def query_summary(orders: Iterable[Order], refunds: Iterable[Refund],
                  products: Iterable[Product], query: str, *, db_path: Path | None = None) -> list[tuple]:
    """Run candidate SQL using the full pipeline's database schema."""
    if db_path is not None:
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.unlink(missing_ok=True)
    connection = sqlite3.connect(":memory:" if db_path is None else str(db_path))
    try:
        connection.executescript(SCHEMA)
        with connection:
            connection.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)", orders)
            connection.executemany("INSERT INTO products VALUES (?, ?, ?)", products)
            connection.executemany("INSERT INTO refunds VALUES (?, ?, ?)", refunds)
        cursor = connection.execute(query)
        if cursor.description is None or tuple(col[0] for col in cursor.description) != COLUMNS:
            raise ValueError("SQL must return the exact columns listed in DATA.md")
        rows = cursor.fetchall()
        for row in rows:
            if any(not isinstance(value, str) for value in row[:3]):
                raise ValueError("SQL period, channel and category must be text")
            if any(type(value) is not int for value in row[3:]):
                raise ValueError("SQL counts and money must be integers, not NULL or decimals")
        return rows
    finally:
        connection.close()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clear_outputs(root: Path) -> None:
    for name in OUTPUT_FILES:
        (root / "output" / name).unlink(missing_ok=True)


def run_once(root: Path, *, base_orders: int, seed: int) -> dict[str, str]:
    from solution import prepare_orders

    inputs = generate_data(root / "data", base_orders, seed)
    products = load_products(root / "data/products.csv")
    prepared = prepare_orders(iter_orders(root / "data/orders.csv"), {p.product_id for p in products})
    query = (root / "analysis.sql").read_text(encoding="utf-8")
    rows = query_summary(prepared.orders, iter_refunds(root / "data/refunds.csv"), products,
                         query, db_path=root / "output/analysis.sqlite")
    output = root / "output"
    output.mkdir(exist_ok=True)
    with (output / "summary.csv").open("w", encoding="utf-8", newline="") as destination:
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    quality = prepared.quality._asdict()
    write_json(output / "quality.json", quality)
    notes = (root / "NOTES.md").read_text(encoding="utf-8")
    (output / "report.html").write_text(render_report(COLUMNS, rows, quality, notes), encoding="utf-8")
    manifest = {
        "generator_version": GENERATOR_VERSION, "seed": seed, "base_orders": base_orders,
        "periods": PERIODS, "inputs": inputs,
        "environment": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version},
        "candidate_files": {name: sha256(root / name) for name in CANDIDATE_FILES},
        "outputs": {name: sha256(output / name) for name in COMPARED_FILES[:3]},
    }
    write_json(output / "manifest.json", manifest)
    return {name: sha256(output / name) for name in COMPARED_FILES}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate data and rebuild the task's output files offline.")
    parser.add_argument("--orders", type=int, default=DEFAULT_ORDERS, help="number of base orders, default 200000")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check-setup", action="store_true", help="check environment and generator only")
    mode.add_argument("--check-repro", action="store_true", help="run twice and compare output files")
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        if error.code:
            clear_outputs(ROOT)
        raise
    if not args.check_setup:
        clear_outputs(ROOT)
    try:
        if sys.version_info < (3, 10):
            raise ValueError("Python 3.10 or newer is required")
        if args.orders < 0:
            raise ValueError("--orders must be zero or positive")
        if args.check_setup:
            with tempfile.TemporaryDirectory() as folder:
                generated = generate_data(Path(folder), 200, args.seed)
                if generated["orders.csv"]["rows"] != 204:
                    raise ValueError("Generator setup check failed")
            print(f"Setup ready. Python {platform.python_version()}, SQLite {sqlite3.sqlite_version}. No extra packages needed.")
            print("Setup checks do not validate your calculations.")
            return 0
        first = run_once(ROOT, base_orders=args.orders, seed=args.seed)
        if args.check_repro:
            second = run_once(ROOT, base_orders=args.orders, seed=args.seed)
            if first != second:
                raise ValueError("The two runs produced different files. No reproducibility record was saved.")
            write_json(ROOT / "output/reproducibility.json", {"matched": True, "hashes": second})
            print("Two runs produced identical summary, quality, report and manifest bytes.")
        print("Files are in output/. Open output/report.html to view the report. Matching runs can still contain calculation errors.")
        return 0
    except Exception as error:
        clear_outputs(ROOT)
        print(f"Pipeline failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
