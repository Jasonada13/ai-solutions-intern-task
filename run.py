import argparse
import csv
import json
import sqlite3
import sys
from collections.abc import Iterable
from contextlib import closing
from datetime import datetime
from pathlib import Path

from models import Order, OrderEvent, Refund


ROOT = Path(__file__).resolve().parent
PERIOD_START = "2026-05-01T00:00:00Z"
PERIOD_END = "2026-06-01T00:00:00Z"
AS_OF = "2026-06-05T00:00:00Z"
SUMMARY_COLUMNS = (
    "channel", "completed_orders", "gross_pence", "refund_pence",
    "net_pence", "refunded_orders", "refund_rate",
)


def load_csv(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not set(columns).issubset(reader.fieldnames or []):
            raise ValueError(f"{path.name} is missing required headers: {', '.join(columns)}")
        return list(reader)


def load_data() -> tuple[list[OrderEvent], list[Refund]]:
    rows = load_csv(ROOT / "data/order_events.csv", OrderEvent._fields)
    events = [OrderEvent(
        row["order_id"], int(row["revision"]), row["received_at"],
        row["ordered_at"], row["channel"], row["status"], int(row["gross_pence"]),
    ) for row in rows]
    rows = load_csv(ROOT / "data/refunds.csv", Refund._fields)
    refunds = [Refund(
        row["refund_id"], row["order_id"], int(row["refund_pence"]),
        row["occurred_at"], row["received_at"],
    ) for row in rows]
    return events, refunds


def query_summary(
    orders: Iterable[Order],
    refunds: Iterable[Refund],
    query: str,
    *,
    as_of: str = AS_OF,
    period_start: str = PERIOD_START,
    period_end: str = PERIOD_END,
) -> list[tuple]:
    with closing(sqlite3.connect(":memory:")) as database:
        database.executescript("""
            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY,
                ordered_at TEXT,
                channel TEXT,
                status TEXT,
                gross_pence INTEGER
            );
            CREATE TABLE refunds (
                refund_id TEXT,
                order_id TEXT,
                refund_pence INTEGER,
                occurred_at TEXT,
                received_at TEXT
            );
        """)
        database.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)
        database.executemany("INSERT INTO refunds VALUES (?, ?, ?, ?, ?)", refunds)
        cursor = database.execute(query, {
            "as_of": as_of, "period_start": period_start, "period_end": period_end,
        })
        if cursor.description is None:
            raise ValueError("analysis.sql must contain one SELECT query. See DATA.md.")
        columns = tuple(column[0] for column in cursor.description)
        if columns != SUMMARY_COLUMNS:
            raise ValueError(f"analysis.sql must return these columns in order: {', '.join(SUMMARY_COLUMNS)}")
        return cursor.fetchall()


def write_summary(path: Path, rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(SUMMARY_COLUMNS)
        for row in rows:
            integers = [int(value) for value in row[1:6]]
            if any(integer != value for integer, value in zip(integers, row[1:6])):
                raise ValueError("Counts and money in the SQL result must be integers.")
            writer.writerow([row[0], *integers, f"{row[6]:.4f}"])


def write_quality(path: Path, conflicted_order_ids: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"conflicted_order_ids": conflicted_order_ids}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the channel report at a knowledge cutoff.")
    parser.add_argument("--check-setup", action="store_true", help="Check Python, SQLite, and fixture loading without running your solution.")
    parser.add_argument("--as-of", default=AS_OF, help="Knowledge cutoff in YYYY-MM-DDTHH:MM:SSZ format.")
    args = parser.parse_args()
    summary_path = ROOT / "output/summary.csv"
    quality_path = ROOT / "output/quality.json"
    try:
        if not args.check_setup:
            for path in (summary_path, quality_path):
                path.unlink(missing_ok=True)
        timestamp_format = "%Y-%m-%dT%H:%M:%SZ"
        if datetime.strptime(args.as_of, timestamp_format).strftime(timestamp_format) != args.as_of:
            raise ValueError("--as-of must use YYYY-MM-DDTHH:MM:SSZ format.")
        events, refunds = load_data()
        if args.check_setup:
            with closing(sqlite3.connect(":memory:")) as database:
                database.execute("SELECT 1").fetchone()
            print("Setup OK. Fixtures and SQLite are available. This does not check your answer.")
            return 0

        from solution import reconcile_orders

        snapshot = reconcile_orders(iter(events), args.as_of)
        query = (ROOT / "analysis.sql").read_text(encoding="utf-8")
        rows = query_summary(snapshot.orders, refunds, query, as_of=args.as_of)
        write_summary(summary_path, rows)
        write_quality(quality_path, snapshot.conflicted_order_ids)
    except Exception as error:
        if not args.check_setup:
            for path in (summary_path, quality_path):
                path.unlink(missing_ok=True)
        print(f"Unable to create report: {error}", file=sys.stderr)
        return 1
    print("Created output/summary.csv and output/quality.json. Check both before submitting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
