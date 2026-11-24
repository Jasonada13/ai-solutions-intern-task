from typing import NamedTuple


class OrderEvent(NamedTuple):
    order_id: str
    revision: int
    received_at: str
    ordered_at: str
    channel: str
    status: str
    gross_pence: int


class Order(NamedTuple):
    order_id: str
    ordered_at: str
    channel: str
    status: str
    gross_pence: int


class Snapshot(NamedTuple):
    orders: list[Order]
    conflicted_order_ids: list[str]


class Refund(NamedTuple):
    refund_id: str
    order_id: str
    refund_pence: int
    occurred_at: str
    received_at: str
