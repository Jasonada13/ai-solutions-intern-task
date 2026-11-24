# Data and calculation rules

Use these rules for both your implementation and your tests. There are no additional business rules to discover. The generator and pipeline are supplied; repair only the four files listed in the [README](README.md).

## Dataset

`python3 run.py --check-repro` generates the default data locally with generator version `v4`, seed `42` and `200000` base orders. Of the base orders, 45% belong to `baseline` and 55% to `current`. There are additional duplicate order deliveries and invalid rows, about 1% of each, as well as products and refund records. The manifest records exact file row counts and SHA-256 hashes.

| Period | Sales dates | Refund coverage |
| --- | --- | --- |
| `baseline` | 1–28 May 2026 | Completed 30-day follow-up |
| `current` | 1–28 June 2026 | Completed 30-day follow-up |

All supplied refunds fall within the relevant follow-up. There is no timestamp or cutoff calculation. Each order contains one product and may contain multiple units. The catalog has four categories; channels are `app`, `partner` and `web`. Orders include both `completed` and `cancelled` statuses, and some completed orders have no refunds.

Money is integer GBP pence. Gross sales are after discounts and before refunds. Product unit costs are fixed across both periods. Product and fulfilment costs remain incurred for completed orders even when refunded; do not recover returned-stock costs. Contribution excludes fixed overhead, tax and acquisition spend.

## Files, records and tables

The supplied `models.py` defines these records. CSV headers and SQLite column names use the same field names.

| Record / file / table | Fields in order |
| --- | --- |
| `RawOrder` / `data/orders.csv` | `order_id`, `period`, `channel`, `status`, `product_id`, `quantity`, `gross_pence`, `fulfilment_cost_pence` |
| `Order` / `orders` | The same fields as `RawOrder`. |
| `Product` / `data/products.csv` / `products` | `product_id`, `category`, `unit_cost_pence` |
| `Refund` / `data/refunds.csv` / `refunds` | `refund_id`, `order_id`, `refund_pence` |

Every `RawOrder` field is a string. In `Order`, quantity and money fields are integers and the other fields are strings. `Product.unit_cost_pence` and `Refund.refund_pence` are integers; their other fields are strings. SQLite uses corresponding TEXT and INTEGER columns.

IDs are nonempty, case-sensitive and have no surrounding whitespace. Product IDs are unique and the catalog is valid. Periods are already valid `baseline` or `current` values. Channels and statuses are valid after `strip().lower()`. Quantity and money strings may be malformed or outside the permitted range. Do not invent additional ID, period, channel or status rejection categories.

Valid duplicate order rows have identical normalized payloads. There are no conflicting revisions. Refund records are valid but may repeat: the same `refund_id` always has an identical payload. Different refund IDs with the same amount are different refunds. References to missing, rejected or cancelled orders may exist and must contribute nothing.

The database is rebuilt each run. `orders.order_id` and `products.product_id` are unique; `refunds` has no uniqueness constraint. The SQL input contains the accepted orders returned by your Python function, including valid cancelled orders.

## Python preparation

Implement this supplied interface:

```python
prepare_orders(
    rows: Iterable[RawOrder], product_ids: set[str]
) -> PreparedOrders
```

For each raw row, apply this order:

1. Normalize channel and status with `strip().lower()`.
2. Convert quantity, gross and fulfilment cost with integer conversion. Quantity and gross must be positive; fulfilment cost must be nonnegative.
3. If conversion or a range check fails, reject the row as `invalid_values`.
4. Otherwise, if its product is absent from `product_ids`, reject it as `unknown_product`.
5. Otherwise, retain one valid row per `order_id` and count subsequent valid copies as `duplicate_rows`.

Validation comes before duplicate classification. An invalid row does not reserve its ID. Keep valid cancelled orders in the returned data; SQL applies business exclusions.

Return `PreparedOrders(orders, quality)`, where `orders` is a list of `Order` records sorted by `order_id`. Consume the input iterator once, do not mutate its records and do not materialize or sort all raw rows. Keeping accepted orders and seen IDs in memory is allowed. There is no hidden runtime threshold or required infrastructure.

`quality` is a `QualityCounts` record containing these six integers:

| Field | Meaning |
| --- | --- |
| `input_rows` | Every raw order row read. |
| `accepted_orders` | Valid unique orders retained, including cancelled orders. |
| `duplicate_rows` | Valid repeated order deliveries not retained. |
| `rejected_rows` | Rows rejected for invalid values or unknown products. |
| `invalid_values` | Rejections at the numeric conversion or range step. |
| `unknown_product` | Rejections for an unknown product after valid numeric checks. |

The counts must reconcile:

```text
input_rows = accepted_orders + duplicate_rows + rejected_rows
rejected_rows = invalid_values + unknown_product
```

## SQL performance summary

Write one SELECT in `analysis.sql`; CTEs are allowed. Return one row per period, channel and category containing completed accepted orders joined to their products. Sort by period with `baseline` before `current`, then channel, then category.

Return these columns in exactly this order:

| Column | Meaning |
| --- | --- |
| `period` | `baseline` or `current`. |
| `channel` | Normalized sales channel. |
| `category` | Product category. |
| `completed_orders` | Number of eligible orders. |
| `gross_pence` | Total gross sales. |
| `refund_pence` | Total eligible refund value, counting each refund ID once. |
| `net_revenue_pence` | Gross sales minus refunds. |
| `product_cost_pence` | Sum of each order's quantity multiplied by product unit cost. |
| `fulfilment_cost_pence` | Total order fulfilment cost. |
| `contribution_pence` | Net revenue minus product and fulfilment costs. |
| `refunded_orders` | Number of eligible orders with at least one refund, not number of refund events. |

Each order contributes to counts, gross sales and costs once, regardless of how many refund rows it has. Keep completed orders with no refunds. Deduplicate refunds by identity, not amount: `SUM(DISTINCT amount)` is not a valid substitute. Count and money results must be integers. Negative contribution is valid. Empty inputs should produce no result rows and a header-only summary CSV.

For small SQL tests, the supplied `query_summary(orders, refunds, products, query)` helper uses this same schema. See the imports in `tests/test_candidate.py`. Build test records directly, without depending on generated totals. The supplied scaffold tests check plumbing only and pass before the starter is repaired.

## Supplied report and reproduction

The report sums additive segment metrics into overall period comparisons. Contribution margin is total contribution divided by total net revenue; refund ratio is total refunds divided by total gross sales. These are ratios of totals, not averages of segment ratios. The report handles zero denominators and negative values, and includes segment changes, quality counts and only the **Business recommendation** section of `NOTES.md`. Candidate text is escaped rather than executed as HTML.

The manifest records generator settings, periods, input row counts and hashes, Python/SQLite versions, the four candidate file hashes and summary/quality/report hashes. Paths are relative; stable outputs contain no timestamps, elapsed times or local usernames. The reproducibility record compares summary, quality, report and manifest across two full runs. Reproduction requires the same inputs, code and environment; reproducibility alone does not establish business correctness.
