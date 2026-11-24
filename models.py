from typing import NamedTuple


class RawOrder(NamedTuple):
    order_id: str
    period: str
    channel: str
    status: str
    product_id: str
    quantity: str
    gross_pence: str
    fulfilment_cost_pence: str


class Order(NamedTuple):
    order_id: str
    period: str
    channel: str
    status: str
    product_id: str
    quantity: int
    gross_pence: int
    fulfilment_cost_pence: int


class Product(NamedTuple):
    product_id: str
    category: str
    unit_cost_pence: int


class Refund(NamedTuple):
    refund_id: str
    order_id: str
    refund_pence: int


class QualityCounts(NamedTuple):
    input_rows: int
    accepted_orders: int
    duplicate_rows: int
    rejected_rows: int
    invalid_values: int
    unknown_product: int


class PreparedOrders(NamedTuple):
    orders: list[Order]
    quality: QualityCounts
