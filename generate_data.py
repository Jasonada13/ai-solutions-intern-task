import argparse
import csv
import hashlib
from pathlib import Path

from models import Product, RawOrder, Refund


GENERATOR_VERSION = "v5"
DEFAULT_ORDERS = 200000
DEFAULT_SEED = 42
PERIODS = {
    "baseline": {"start": "2026-05-01", "end_inclusive": "2026-05-28", "refund_follow_up_days": 30},
    "current": {"start": "2026-06-01", "end_inclusive": "2026-06-28", "refund_follow_up_days": 30},
}


class RandomNumbers:
    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFF

    def below(self, limit: int) -> int:
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return (self.state >> 8) % limit


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generate_data(folder: Path, base_orders: int = DEFAULT_ORDERS, seed: int = DEFAULT_SEED) -> dict:
    if base_orders < 0:
        raise ValueError("--orders must be nonnegative")
    folder.mkdir(parents=True, exist_ok=True)
    categories = [("braking", 1200), ("filtration", 3500), ("sensors", 6000), ("electrical", 2200)]
    products = [Product(f"P{index * 4 + variant + 1:03d}", category, cost + variant * 150)
                for index, (category, cost) in enumerate(categories) for variant in range(4)]
    with (folder / "products.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(Product._fields)
        writer.writerows(products)

    rng = RandomNumbers(seed)
    order_rows = refund_rows = 0
    baseline_orders = base_orders * 45 // 100
    with (folder / "orders.csv").open("w", encoding="utf-8", newline="") as orders_file, \
            (folder / "refunds.csv").open("w", encoding="utf-8", newline="") as refunds_file:
        orders = csv.writer(orders_file, lineterminator="\n")
        refunds = csv.writer(refunds_file, lineterminator="\n")
        orders.writerow(RawOrder._fields)
        refunds.writerow(Refund._fields)
        for index in range(base_orders):
            period = "baseline" if index < baseline_orders else "current"
            choice = rng.below(100)
            if period == "baseline":
                category_index = choice // 25
            else:
                category_index = 0 if choice < 10 else 1 if choice < 40 else 2 if choice < 80 else 3
            product = products[category_index * 4 + rng.below(4)]
            channel_pick = rng.below(100)
            channel = "vehicle_manufacturer" if channel_pick < 45 else "parts_distributor" if channel_pick < 75 else "workshop_network"
            status = "cancelled" if rng.below(100) < 5 else "completed"
            quantity = 1 + rng.below(3)
            price_percent = 220 if period == "baseline" else 180
            if period == "current" and product.category == "electrical":
                price_percent = 205
            gross = quantity * product.unit_cost_pence * price_percent // 100 + rng.below(101)
            fulfilment = 350 + rng.below(151) + (250 if period == "current" else 0)
            if channel == "workshop_network":
                fulfilment += 150
            order_id = f"O{index + 1:08d}"
            raw = RawOrder(order_id, period,
                           f" {channel.upper()} " if index % 7 == 0 else channel,
                           f" {status.upper()} " if index % 11 == 0 else status,
                           product.product_id, str(quantity), str(gross), str(fulfilment))
            orders.writerow(raw)
            order_rows += 1
            if index % 100 == 0:
                orders.writerow(raw._replace(channel=channel, status=status))
                order_rows += 1
                if index % 200 == 0:
                    bad = ["0", "-2", "not-a-number", ""][rng.below(4)]
                    orders.writerow(raw._replace(quantity=bad))
                else:
                    orders.writerow(raw._replace(order_id=f"UNKNOWN{index:08d}", product_id="missing-product"))
                order_rows += 1

            probability = 10 if period == "baseline" else 22
            if period == "current" and product.category == "sensors" and channel == "workshop_network":
                probability = 44
            if rng.below(100) < probability:
                split = index % 5 == 0
                amount = gross // (4 if split else 2)
                refund = Refund(f"R{index + 1:08d}A", order_id, amount)
                refunds.writerow(refund)
                refund_rows += 1
                if split:
                    refunds.writerow(Refund(f"R{index + 1:08d}B", order_id, amount))
                    refund_rows += 1
                if index % 3 == 0:
                    refunds.writerow(refund)
                    refund_rows += 1
        if base_orders:
            refunds.writerow(Refund("R-ORPHAN", "missing-order", 500))
            refunds.writerow(Refund("R-REJECTED", "UNKNOWN00000100", 700))
            refund_rows += 2

    counts = {"orders.csv": order_rows, "products.csv": len(products), "refunds.csv": refund_rows}
    return {name: {"rows": count, "sha256": sha256(folder / name)} for name, count in counts.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the task's synthetic raw data offline.")
    parser.add_argument("--orders", type=int, default=DEFAULT_ORDERS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    counts = generate_data(Path(__file__).resolve().parent / "data", args.orders, args.seed)
    for name, info in counts.items():
        print(f"{name}: {info['rows']:,} rows")


if __name__ == "__main__":
    main()
