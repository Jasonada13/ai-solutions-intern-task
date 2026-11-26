# Generated data

The pipeline generates these synthetic CSVs locally:

- `orders.csv`: raw order deliveries, including duplicates and invalid values.
- `products.csv`: product categories and unit costs.
- `refunds.csv`: refund deliveries, including repeated refund IDs.

Run `python3 run.py --check-repro` from the repository root to generate the default dataset and run the pipeline twice. Defaults are 200,000 base orders and seed 42. Find exact row counts and file hashes in `output/manifest.json`.

See [DATA.md](../DATA.md) for schemas, validation rules and metric definitions. Git ignores the generated CSVs, and `submission.zip` excludes them. Recipients regenerate them from the supplied code. Do not edit the CSVs.
