from typing import NamedTuple


class Order(NamedTuple):
    order_id: str
    channel: str
    status: str
    gross_pence: int


def clean_orders(rows: list[dict[str, str]]) -> list[Order]:
    """Return valid, normalized orders in input order. See DATA.md."""
    raise NotImplementedError("Implement clean_orders() in solution.py. See DATA.md.")
