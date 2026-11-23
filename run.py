import argparse
import csv
import sqlite3
import sys
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).resolve().parent
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


def load_data():
    orders = load_csv(
        ROOT / "data/orders.csv", ("order_id", "channel", "status", "gross_pence")
    )
    rows = load_csv(
        ROOT / "data/refunds.csv", ("refund_id", "order_id", "refund_pence")
    )
    refunds = [(row["refund_id"], row["order_id"], int(row["refund_pence"])) for row in rows]
    return orders, refunds


def query_summary(orders, refunds, query: str) -> list[tuple]:
    with closing(sqlite3.connect(":memory:")) as database:
        database.executescript("""
            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY,
                channel TEXT,
                status TEXT,
                gross_pence INTEGER
            );
            CREATE TABLE refunds (
                refund_id TEXT PRIMARY KEY,
                order_id TEXT,
                refund_pence INTEGER
            );
        """)
        database.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", orders)
        database.executemany("INSERT INTO refunds VALUES (?, ?, ?)", refunds)
        cursor = database.execute(query)
        if cursor.description is None:
            raise ValueError("analysis.sql is incomplete. Add one SELECT query. See DATA.md.")
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the channel summary from the supplied CSV files.")
    parser.add_argument("--check-setup", action="store_true", help="Check Python, SQLite, and fixture loading without running your solution.")
    args = parser.parse_args()
    output = ROOT / "output/summary.csv"
    try:
        if not args.check_setup:
            output.unlink(missing_ok=True)
        orders, refunds = load_data()
        if args.check_setup:
            with closing(sqlite3.connect(":memory:")) as database:
                database.execute("SELECT 1").fetchone()
            print("Setup OK. Fixtures and SQLite are available. The task may still be incomplete.")
            return 0

        from solution import clean_orders

        query = (ROOT / "analysis.sql").read_text(encoding="utf-8")
        rows = query_summary(clean_orders(orders), refunds, query)
        write_summary(output, rows)
    except Exception as error:
        if not args.check_setup:
            output.unlink(missing_ok=True)
        print(f"Unable to create summary: {error}", file=sys.stderr)
        return 1
    print("Created output/summary.csv. Check the results before submitting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
