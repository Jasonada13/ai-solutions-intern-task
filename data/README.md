# Generated data

The pipeline generates these synthetic CSVs locally:

- `orders.csv`: raw order deliveries, including duplicates and invalid values.
- `products.csv`: product categories and unit costs.
- `refunds.csv`: refund deliveries, including repeated refund IDs.

Run `python3 run.py --check-repro` from the repository root to generate the default dataset and complete the pipeline twice. Defaults are 200,000 base orders and seed 42. Exact row counts and file hashes appear in `output/manifest.json`.

See [DATA.md](../DATA.md) for schemas, validation rules and metric definitions. The generated CSVs are ignored by Git and excluded from `submission.zip`; recipients regenerate them from the supplied code. Do not edit the CSVs as part of the task.
