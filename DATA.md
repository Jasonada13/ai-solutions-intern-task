# Data and calculation rules

Use these rules for your implementation and tests. They define all the business rules for the task. The generator and pipeline are supplied. Make code and notes changes in the four files listed in the [README](README.md). You may also add a business report and optional preview.

## Dataset

`python3 run.py --check-repro` generates the default data locally with generator version `v4`, seed `42` and `200000` base orders. Of the base orders, 45% belong to `baseline` and 55% to `current`. Duplicate order deliveries and invalid rows add about 1% each. The default dataset contains 204,000 order rows, 54,312 refund deliveries and 16 products. The manifest records exact file row counts and SHA-256 hashes.

| Period | Sales dates | Refund coverage |
| --- | --- | --- |
| `baseline` | 1 to 28 May 2026 | Completed 30-day follow-up |
| `current` | 1 to 28 June 2026 | Completed 30-day follow-up |

All supplied refunds fall within the relevant follow-up, so no timestamp or cutoff calculation is needed. Each order contains one product and may contain multiple units. The catalog has four categories. Channels are `app`, `partner` and `web`. Orders have `completed` or `cancelled` status. Some completed orders have no refunds.

Money is integer GBP pence. Gross sales are after discounts and before refunds. Product unit costs are fixed across both periods. Completed orders incur product and fulfilment costs even when refunded. Do not recover returned-stock costs. Contribution excludes fixed overhead, tax and acquisition spend.

## Files, records and tables

The supplied `models.py` defines these records. CSV headers and SQLite column names use the same field names.

| Record / file / table | Fields in order |
| --- | --- |
| `RawOrder` / `data/orders.csv` | `order_id`, `period`, `channel`, `status`, `product_id`, `quantity`, `gross_pence`, `fulfilment_cost_pence` |
| `Order` / `orders` | The same fields as `RawOrder`. |
| `Product` / `data/products.csv` / `products` | `product_id`, `category`, `unit_cost_pence` |
| `Refund` / `data/refunds.csv` / `refunds` | `refund_id`, `order_id`, `refund_pence` |

Every `RawOrder` field is a string. In `Order`, quantity and money fields are integers and the other fields are strings. `Product.unit_cost_pence` and `Refund.refund_pence` are integers; their other fields are strings. SQLite uses corresponding TEXT and INTEGER columns.

IDs are nonempty and case-sensitive, with no surrounding whitespace. Product IDs are unique and the catalog is valid. Periods are valid `baseline` or `current` values. Channels and statuses are valid after `strip().lower()`. Quantity and money strings may be malformed or outside the permitted range. Use only the rejection categories specified below.

Valid duplicate order rows contain identical normalized values. There are no conflicting revisions. Refund records are valid but may repeat. Records with the same `refund_id` have identical values. Different refund IDs with the same amount are separate refunds. Refunds may refer to missing, rejected or cancelled orders. Exclude these from all calculations.

The pipeline rebuilds the database each run. `orders.order_id` and `products.product_id` are unique. The `refunds` table has no uniqueness constraint. SQL receives the accepted orders returned by your Python function, including valid cancelled orders.

## Python preparation

Implement this supplied interface:

```python
prepare_orders(
    rows: Iterable[RawOrder], product_ids: set[str]
) -> PreparedOrders
```

Process each raw row in this order:

1. Normalize channel and status with `strip().lower()`.
2. Convert quantity, gross and fulfilment cost with integer conversion. Quantity and gross must be positive; fulfilment cost must be nonnegative.
3. If conversion or a range check fails, reject the row as `invalid_values`.
4. Otherwise, if its product is absent from `product_ids`, reject it as `unknown_product`.
5. Otherwise, retain one valid row per `order_id` and count subsequent valid copies as `duplicate_rows`.

Validation comes before duplicate classification. An invalid row does not reserve its ID. Keep valid cancelled orders in the returned data; SQL applies business exclusions.

Return `PreparedOrders(orders, quality)`, where `orders` is a list of `Order` records sorted by `order_id`. Read the input iterator once without changing its records. Do not collect or sort all raw rows. You may keep accepted orders and seen IDs in memory. There is no hidden runtime threshold or required infrastructure.

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

Write one SELECT in `analysis.sql`. CTEs are allowed. Join completed accepted orders to their products and return one row per period, channel and category. Sort by period with `baseline` before `current`, then channel, then category.

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

Each order contributes to counts, gross sales and costs once, regardless of how many refund rows it has. Keep completed orders with no refunds. Deduplicate refunds by `refund_id`. Do not use `SUM(DISTINCT amount)`, which would combine separate refunds with equal amounts. Count and money results must be integers. Negative contribution is valid. Empty inputs should produce no result rows and a header-only summary CSV.

The supplied `query_summary(orders, refunds, products, query)` helper uses this schema for small SQL tests. See the imports in `tests/test_candidate.py`. Build test records directly, independently of the generated totals. The supplied tests check that the pipeline runs and pass before you repair the starter.

## Supplied report and reproduction

The report sums segment counts and money values to compare the periods overall. Contribution margin is total contribution divided by total net revenue. Refund ratio is total refunds divided by total gross sales. Calculate these ratios from totals; do not average segment ratios. The report handles zero denominators and negative values. It includes segment changes, quality counts and only the `Business recommendation` section of `NOTES.md`. It escapes candidate text so the browser cannot execute it as HTML.

You can use the supplied HTML as your business report or submit a separate file, including PowerPoint or Power BI, as described in the [README](README.md). For a separate report, put its archived filename in the business section of `NOTES.md` instead of repeating the narrative. The generated HTML remains one of the five required output files.

The manifest records generator settings, periods, input row counts and hashes, Python and SQLite versions, the four candidate file hashes, and summary, quality and report hashes. Paths are relative. Stable outputs exclude timestamps, elapsed times and local usernames. The reproducibility record compares summary, quality, report and manifest across two full runs. Reproduction requires the same inputs, code and environment. Matching outputs establish repeatability, not business correctness.

The packager copies a report supplied through `package_submission.py --business-report "PATH"` unchanged into `business-report/<filename>` in the submission ZIP. It copies an optional `--report-preview "PATH"` into `business-report/preview/<filename>`. These files are outside the pipeline's generation and two-run comparison. The five generated outputs still reproduce as described above. A preview requires a report. Submit actual files; a link alone is insufficient. A readable PDF or image preview is recommended when the report needs specialist software.
