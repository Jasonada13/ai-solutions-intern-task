# Generated data

The pipeline generates these synthetic CSVs locally and deterministically for a fictional automotive components supplier:

- `orders.csv`: raw order deliveries, including duplicates and invalid values.
- `products.csv`: generic components, their families, and unit costs.
- `refunds.csv`: customer credit deliveries for returned components, including repeated credit IDs.

All codes, prices, volumes, and patterns are invented. No data comes from a real company or represents industry benchmarks. See [Data and calculation rules](../DATA.md) for the retained credit field names.

Run `python3 run.py --check-repro` from the repository root to generate the default dataset and run the pipeline twice. Defaults are 20,000 base orders and seed 42. Find exact row counts and file hashes in `output/manifest.json`.

See [DATA.md](../DATA.md) for schemas, validation rules and metric definitions. Git ignores the generated CSVs, and `submission.zip` excludes them. Recipients regenerate them from the supplied code. Do not edit the CSVs.
