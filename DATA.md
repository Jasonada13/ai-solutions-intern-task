# Data reference

The fixtures are a small synthetic snapshot of one month. All money is GBP in integer pence. There are no dates to process.

## Raw orders

`data/orders.csv` has one attempted exported order per row. The required fields are `order_id`, `channel`, `status`, and `gross_pence`.

`clean_orders(rows)` receives a list of string-valued dictionaries and returns a list of the supplied `Order` named tuples. These rules apply in order.

1. Strip surrounding whitespace from all four fields. Lowercase `channel` and `status` only.
2. Accept a nonempty `order_id`, a channel of `web`, `app`, or `partner`, and a status of `completed` or `cancelled`.
3. Accept `gross_pence` only when it contains ASCII digits `0` through `9` and converts to an integer greater than zero. Leading zeros are allowed. Signs, decimal points, internal spaces, and non-ASCII digits are invalid.
4. Reject any invalid row. For each normalized `order_id`, retain the first valid row in input order. An invalid earlier row must not block a later valid row.

Order IDs are case sensitive. `CaseA` and `casea` are different IDs. Keep valid cancelled orders in this Python result. Do not change the input dictionaries. Ignore extra columns. Required headers and rectangular string-valued rows are guaranteed, so malformed CSV handling is outside the task.

## Refunds

`data/refunds.csv` is already clean. Each row is one refund event with a unique `refund_id`, an `order_id`, and positive integer `refund_pence`.

Every refund refers to a retained completed order. An order can have no refunds or several refunds. Different refund IDs with equal amounts are distinct events. Total refunds for an order never exceed its gross amount. There is no refund cleaning task.

## SQLite tables

The runner creates these tables in memory and loads your cleaned orders and the supplied refunds.

```sql
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
```

## Channel summary

`analysis.sql` contains one SELECT query, which may use common table expressions. SQL owns all aggregations. Include only completed orders and channels with at least one completed order. Sort by `channel` ascending. Return these exact columns in this order.

| Column | Meaning |
| --- | --- |
| `channel` | `app`, `partner`, or `web` |
| `completed_orders` | Number of included orders |
| `gross_pence` | Sum of included order gross amounts |
| `refund_pence` | Sum of all refund events for included orders, or zero |
| `net_pence` | `gross_pence` minus `refund_pence` |
| `refunded_orders` | Number of distinct included orders with at least one refund |
| `refund_rate` | `refunded_orders` divided by `completed_orders`, as an unrounded fraction |

Each order contributes once to the order count and gross amount, including orders with no refunds or multiple refunds. A channel with no completed orders produces no row. Empty input produces no result rows.

The runner writes `output/summary.csv` with a header, integer counts and money, and the rate formatted to four decimal places. It performs no business calculations. On failure, the runner removes any old summary.
