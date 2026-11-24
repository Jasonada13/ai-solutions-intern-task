# Data reference

The files contain synthetic order and refund deliveries. All headers, values, and types are valid. The supplied loader parses integers and creates the immutable records in `models.py`. CSV cleaning and timestamp parsing are outside the task.

## Report context

| Parameter | Value | Boundary |
| --- | --- | --- |
| `period_start` | `2026-05-01T00:00:00Z` | Inclusive |
| `period_end` | `2026-06-01T00:00:00Z` | Exclusive |
| `as_of` | `2026-06-05T00:00:00Z` | Inclusive |

All timestamps use this canonical UTC format, so string comparisons work. IDs are case-sensitive. Channels are `app`, `partner`, and `web`. Status is `completed` or `cancelled`. Money is positive integer GBP pence. Revisions are positive integers.

## Python snapshot

`data/order_events.csv` contains order revisions, including repeated deliveries. The supplied types are:

```python
OrderEvent(order_id, revision, received_at, ordered_at, channel, status, gross_pence)
Order(order_id, ordered_at, channel, status, gross_pence)
Snapshot(orders, conflicted_order_ids)
```

Implement this function in `solution.py`:

```python
reconcile_orders(events: Iterable[OrderEvent], as_of: str) -> Snapshot
```

Apply these rules per order ID:

1. Consider only deliveries with `received_at <= as_of`.
2. Select the greatest eligible `revision`. Input order and receipt order do not determine the revision.
3. Compare the business payload at that revision: `ordered_at`, `channel`, `status`, and `gross_pence`. Repeated identical payloads have no effect. Different receipt times alone do not make a conflict.
4. If that revision has different payloads, exclude the order from `orders` and include its ID once in `conflicted_order_ids`. A later identical delivery must not erase this conflict.
5. A higher eligible revision resolves any lower-revision conflict. Future deliveries cannot create or resolve a conflict at the current cutoff.

Return both completed and cancelled orders. SQL decides which orders belong in the report. Sort `orders` by `order_id` and sort `conflicted_order_ids`. Both `Snapshot` fields are lists. Do not mutate inputs.

The function must accept a single-pass iterable and consume it once. Use working memory proportional to distinct observed order IDs, apart from returned output. Do not sort or materialize all deliveries. Sorting selected outputs is allowed. There is no hidden runtime threshold.

## Refund deliveries

`data/refunds.csv` loads as:

```python
Refund(refund_id, order_id, refund_pence, occurred_at, received_at)
```

A refund ID can be delivered repeatedly. Its `order_id`, amount, and `occurred_at` always agree; `received_at` can differ. Different refund IDs with equal amounts are distinct refunds.

A delivery is eligible only when both `occurred_at <= as_of` and `received_at <= as_of`. Count each refund ID once among eligible deliveries. Refunds after the May period can still count. The report follows the selected order cohort as known at the cutoff, rather than refund activity within May.

Refunds may refer to missing orders or orders excluded by status, conflict, or reporting period. These refunds contribute nothing. Retained completed orders in the supplied default fixture are not refunded beyond their gross amount.

## SQL summary

The runner loads your snapshot and all refund deliveries into these in-memory SQLite tables:

```sql
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
```

Write one SELECT query in `analysis.sql`. Common table expressions are allowed. The runner binds `:as_of`, `:period_start`, and `:period_end`; do not hardcode their values in the query.

Include orders with `status = 'completed'` and `period_start <= ordered_at < period_end`. Preserve orders with no eligible refunds. Each included order contributes once to its count and gross amount, regardless of how many refund deliveries it has. Deduplicate refunds by ID, not amount.

Return these exact columns in this order:

| Column | Meaning |
| --- | --- |
| `channel` | Channel, sorted ascending; only channels with eligible orders |
| `completed_orders` | Number of included orders |
| `gross_pence` | Sum of included order gross amounts |
| `refund_pence` | Sum of eligible distinct refund events for those orders, or zero |
| `net_pence` | `gross_pence` minus `refund_pence` |
| `refunded_orders` | Number of distinct included orders with an eligible refund |
| `refund_rate` | `refunded_orders` divided by `completed_orders`, as an unrounded real fraction |

Empty input gives no result rows. `SUM(DISTINCT refund_pence)` does not implement refund deduplication because different refunds can have the same amount.

## Tests and outputs

Use tiny examples you construct yourself in `tests/test_candidate.py`. `Order`, `OrderEvent`, `Refund`, and `Snapshot` are named tuples with the field order shown above. The supplied helper lets you test your SQL independently of Python reconciliation:

```python
rows = query_summary(orders, refunds, QUERY)
```

Here `orders` and `refunds` are iterables of the supplied records, `QUERY` is your SQL text, and the result is a list of tuples in the report column order. The helper also accepts keyword arguments `as_of`, `period_start`, and `period_end`, with the defaults above. It loads the tables and binds parameters; it does not calculate metrics.

The runner writes `output/summary.csv` with the header, integer counts and money, and a four-decimal rate. Empty results still have a header. It also writes `output/quality.json` with the `conflicted_order_ids` list from your snapshot. A failed report run removes both outputs so stale results cannot be submitted by accident.
