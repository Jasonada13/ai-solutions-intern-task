"""Repair this runnable starter using the rules in DATA.md."""
from collections.abc import Iterable

from models import Order, PreparedOrders, QualityCounts, RawOrder


def prepare_orders(rows: Iterable[RawOrder], product_ids: set[str]) -> PreparedOrders:
    latest = {}
    input_rows = 0
    invalid_values = 0
    for row in rows:
        input_rows += 1
        try:
            order = Order(*row[:5], int(row.quantity), int(row.gross_pence),
                          int(row.fulfilment_cost_pence))
        except ValueError:
            invalid_values += 1
            continue
        latest[row.order_id] = order
    orders = sorted(latest.values(), key=lambda order: order.order_id)
    return PreparedOrders(orders, QualityCounts(
        input_rows, len(orders), input_rows - len(orders) - invalid_values,
        invalid_values, invalid_values, 0,
    ))
