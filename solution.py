from collections.abc import Iterable

from models import Order, OrderEvent, Snapshot


def reconcile_orders(events: Iterable[OrderEvent], as_of: str) -> Snapshot:
    """Repair this starter to follow the snapshot rules in DATA.md."""
    latest = {}
    for event in events:
        latest[event.order_id] = Order(
            event.order_id,
            event.ordered_at,
            event.channel,
            event.status,
            event.gross_pence,
        )
    return Snapshot(list(latest.values()), [])
