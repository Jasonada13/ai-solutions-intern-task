# Data and calculation rules

Use these rules for your implementation and tests. They define all the business rules for the task. The generator and pipeline are supplied. Make code and response changes in the four files listed in the [README](README.md). You may also add a business report and optional preview.

## Dataset

`python3 run.py --check-repro` generates the default data locally with generator version `v6`, seed `42`, and `20000` base orders. Of the base orders, 45% belong to `baseline` and 55% to `current`. Duplicate order deliveries and invalid rows add about 1% each. The default dataset contains 20,400 order rows, 5,443 customer credit deliveries, and 16 generic products. The manifest records exact file row counts and SHA-256 hashes.

The generator is deterministic. All companies, product codes such as `P001`, prices, volumes, and patterns are invented for this task. No data is sourced or derived from a real company. These values are not industry benchmarks, and no automotive knowledge is required.

| Period | Sales dates | Customer credit coverage |
| --- | --- | --- |
| `baseline` | 1 to 28 May 2026 | Completed 30-day follow-up |
| `current` | 1 to 28 June 2026 | Completed 30-day follow-up |

All supplied customer credits fall within the relevant follow-up, so no timestamp or cutoff calculation is needed. Each order contains one product and may contain multiple units. The `channel` field identifies the customer channel, `vehicle_manufacturer`, `parts_distributor`, or `workshop_network`. The `category` field identifies the component family, `braking`, `filtration`, `sensors`, or `electrical`. Orders have `completed` or `cancelled` status. Some completed orders have no customer credits.

Customer credits reduce sales values for returned components. This task uses simplified accounting rules. Money is integer GBP pence. Gross sales are after discounts and before customer credits. Product unit costs are fixed across both periods. Completed orders retain their component and fulfilment costs after a credit. Do not recover returned-stock costs. Contribution excludes fixed overhead, tax, and acquisition spend.

## Files, records and tables

The supplied `models.py` defines these records. CSV headers and SQLite column names use the same field names.

The schema keeps its `refund` identifiers for customer credits. `Refund`, `data/refunds.csv`, and the `refunds` table contain credit records. `refund_id` identifies a credit, and `refund_pence` is its value. The summary's `refunded_orders` counts orders with at least one credit. The manifest's `refund_follow_up_days` records the credit follow-up period. Keep these names unchanged.

| Record / file / table | Fields in order |
| --- | --- |
| `RawOrder` / `data/orders.csv` | `order_id`, `period`, `channel`, `status`, `product_id`, `quantity`, `gross_pence`, `fulfilment_cost_pence` |
| `Order` / `orders` | The same fields as `RawOrder`. |
| `Product` / `data/products.csv` / `products` | `product_id`, `category`, `unit_cost_pence` |
| `Refund` / `data/refunds.csv` / `refunds` | `refund_id`, `order_id`, `refund_pence` |

Every `RawOrder` field is a string. In `Order`, quantity and money fields are integers and the other fields are strings. `Product.unit_cost_pence` and `Refund.refund_pence` are integers; their other fields are strings. SQLite uses corresponding TEXT and INTEGER columns.

IDs are nonempty and case-sensitive, with no surrounding whitespace. Product IDs are unique and the catalog is valid. Periods are valid `baseline` or `current` values. Channels and statuses are valid after `strip().lower()`. Quantity and money strings may be malformed or outside the permitted range. Use only the rejection categories specified below.

Valid duplicate order rows contain identical normalized values. There are no conflicting revisions. Customer credit records are valid but may repeat. Records with the same `refund_id` have identical values. Different credit IDs with the same amount are separate credits. Credits may refer to missing, rejected, or cancelled orders. Exclude these from all calculations.

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

Write one SELECT in `analysis.sql`. CTEs are allowed. Join completed accepted orders to their products and return one row per period, customer channel, and component family. Sort by period with `baseline` before `current`, then channel, then category.

Return these columns in exactly this order:

| Column | Meaning |
| --- | --- |
| `period` | `baseline` or `current`. |
| `channel` | Normalized customer channel. |
| `category` | Component family. |
| `completed_orders` | Number of eligible orders. |
| `gross_pence` | Total gross sales. |
| `refund_pence` | Total eligible customer credit value, counting each credit ID once. |
| `net_revenue_pence` | Gross sales minus customer credits. |
| `product_cost_pence` | Sum of each order's quantity multiplied by component unit cost. |
| `fulfilment_cost_pence` | Total order fulfilment cost. |
| `contribution_pence` | Net revenue minus component and fulfilment costs. |
| `refunded_orders` | Number of eligible orders with at least one customer credit, not number of credit events. |

Each order contributes to counts, gross sales, and costs once, regardless of how many customer credit rows it has. Keep completed orders with no credits. Deduplicate credits by `refund_id`. Do not use `SUM(DISTINCT amount)`, which would combine separate credits with equal amounts. Count and money results must be integers. Negative contribution is valid. Empty inputs should produce no result rows and a header-only summary CSV.

The supplied `query_summary(orders, refunds, products, query)` helper uses this schema for small SQL tests. See the imports in `tests/test_candidate.py`. Build test records directly, independently of the generated totals. The supplied tests check that the pipeline runs and pass before you repair the starter.

## Supplied report and reproduction

The report sums segment counts and money values to compare the periods overall. Contribution margin is total contribution divided by total net revenue. Credit ratio is total customer credits divided by total gross sales. This compares money values. The dataset contains no returned-unit counts. Calculate these ratios from totals. Do not average segment ratios. The report handles zero denominators and negative values. It includes segment changes, quality counts, and only the `Business recommendation` section of `RESPONSE.md`. It escapes candidate text so the browser cannot execute it as HTML.

You can use the supplied HTML as your business report or submit a separate file, including PowerPoint or Power BI, as described in the [README](README.md). For a separate report, put its archived filename in the business section of `RESPONSE.md` instead of repeating the narrative. The generated HTML remains one of the five required output files.

The manifest records generator settings, periods, input row counts and hashes, Python and SQLite versions, the four candidate file hashes, and summary, quality and report hashes. Paths are relative. Stable outputs exclude timestamps, elapsed times and local usernames. The reproducibility record compares summary, quality, report and manifest across two full runs. Reproduction requires the same inputs, code and environment. Matching outputs establish repeatability, not business correctness.

The packager copies a report supplied through `package_submission.py --business-report "PATH"` unchanged into `business-report/<filename>` in the submission ZIP. It copies an optional `--report-preview "PATH"` into `business-report/preview/<filename>`. These files are outside the pipeline's generation and two-run comparison. The five generated outputs still reproduce as described above. A preview requires a report. Submit actual files; a link alone is insufficient. A readable PDF or image preview is recommended when the report needs specialist software.
