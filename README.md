# Technical task

Investigate a retailer's performance using Python and SQL, then explain what the business should do next. This is a practical exercise in turning imperfect data into a reproducible result that senior staff can use.

**Allow about one hour, including reading and notes. This is a guide, not a hard limit.** You may spend longer. Working partial submissions receive credit for the evidence they contain. We do not award points for speed, extra features or presentation polish.

## The business question

An online retailer's senior team wants to understand **why sales increased while contribution weakened, and what to do next**. Compare two equal periods: 1–28 May 2026 (`baseline`) and 1–28 June 2026 (`current`). Both have the same completed 30-day refund follow-up.

You will work with 200,000 generated base orders, plus repeated deliveries, invalid rows, products and refunds. This is a substantial laptop-sized dataset. You do not need cloud infrastructure or a distributed system.

Contribution means net revenue minus product and fulfilment costs. It excludes fixed overhead, tax and acquisition spend, so it is **not profit**. All data is synthetic and all money is in GBP pence.

## Start here

Use Python 3.10 or newer with its standard library and SQLite support. No additional packages, accounts, API keys or paid tools are needed. Download or clone this repository, open a terminal in its folder and run:

```sh
python3 run.py --check-setup
python3 run.py --check-repro
```

On Windows, use `python` or `py` in place of `python3` if needed.

The supplied pipeline generates CSVs, prepares orders, builds a local SQLite database, runs the SQL and creates a self-contained report. **The starter runs, but its data preparation and SQL results are deliberately wrong.** Setup, scaffold tests and a successful repeat run do not establish correctness.

Read [DATA.md](DATA.md) for the exact rules, types and output columns. Open `output/report.html` in a browser to see the supplied report layout.

## Your work

Edit only these four files:

| File | What to do |
| --- | --- |
| `solution.py` | Repair `prepare_orders`: normalize and validate the input, handle duplicate orders and report quality counts. |
| `analysis.sql` | Calculate performance by period, channel and product category, handling refunds without losing or multiplying orders. Keep business calculations in SQL. |
| `tests/test_candidate.py` | Add at least one Python test and one SQL test, each using small independent inputs and a hand-calculated expected result. Each should catch a plausible error. |
| `NOTES.md` | Explain the business recommendation and your method using the supplied headings and word limits. |

The generator, database loading, report, reproducibility check and ZIP packaging are supplied. No dashboard, slide deck or additional feature is required.

A suggested hour is 10 minutes to read and run the starter, 25 minutes for Python and SQL, 10 minutes for tests, and 15 minutes for the recommendation, final run and packaging. Prioritize a result you can explain. If something remains unfinished, say what it is in your notes and submit a working partial result.

## Explain the result

In **Business recommendation**, use up to **200 words** for a nontechnical senior reader. Explain the period change, cite at least two corrected result values, identify a material channel/category segment, recommend an action and quantify one illustrative opportunity. State the assumption or limitation behind that estimate.

One possible scenario is the current refund value minus the current gross sales multiplied by the baseline refund-to-gross ratio for a chosen segment, holding sales and other costs fixed. A negative result is not a saving. Another coherent, supported scenario is welcome. A scenario is not a forecast, a realized saving or evidence that one factor caused the change.

In **Method and scale**, use up to **100 words**. Describe one correction and how you checked it, your AI or manual method, and one bottleneck, proposed change and tradeoff at **five million orders**. If you used AI, name the model if known, its purpose and an output you verified. Token or cost figures are optional; label estimates or unknown values honestly.

You may use your own AI tools. We do not supply AI access or credits, and paid access earns no advantage. You remain responsible for the submitted work and should be able to explain it. Do not include credentials, chat logs or personal information in the files.

## Verify and submit privately

Run your tests, regenerate the final outputs twice, then build the ZIP:

```sh
python3 -m unittest discover -s tests
python3 run.py --check-repro
python3 package_submission.py
```

The required final pipeline command is `python3 run.py --check-repro`. It compares the summary, quality counts, report and manifest byte for byte across two complete runs. It writes a reproducibility record only when they match. Repeatability is evidence that the process is stable; it does not prove the answers are right.

The five output files are:

| File | Purpose |
| --- | --- |
| `output/summary.csv` | Your SQL results. |
| `output/quality.json` | Your six data quality counts. |
| `output/report.html` | A report with performance comparisons and your business recommendation. |
| `output/manifest.json` | Input, code and output hashes, dataset settings and environment versions. |
| `output/reproducibility.json` | The successful two-run comparison. |

Email **`submission.zip`** using the recruiter invitation or reply channel. **Do not publish answers through a public fork, pull request or issue.** The ZIP contains the code, SQL, tests, documentation, notes and five output files needed to reproduce the work. It excludes the raw CSVs, database, large logs, credentials, Git history and management PowerPoint. Someone extracting it can regenerate the data and results with the same command, without network access. A working partial submission also needs the reproducibility record.

`python3 run.py` performs one full run and removes any previous reproducibility record. Both run modes remove stale generated outputs if the pipeline fails. You can use `--orders` and `--seed` to try alternate data; use the default dataset for your submitted result.

## How we review it

| Area | Points |
| --- | ---: |
| Python and data preparation | 25 |
| SQL and metrics | 25 |
| Business value and communication | 25 |
| Verification and reproducibility | 15 |
| Tool and scale judgment | 10 |

Reviewers look for correct reasoning, supported recommendations and meaningful verification. Automated checks and AI-assisted technical review may help inspect the submitted work. Human reviewers award partial credit and make shortlist decisions. Shortlisted candidates may be asked to explain their approach to both technical and nontechnical audiences.

This is version 4. The [previous assessment](https://github.com/Jasonada13/ai-solutions-intern-task/tree/assessment-v3) is retained for reference. A [management overview](docs/technical-task.pptx) is also available.
