# Technical task

Investigate a retailer's performance using Python and SQL, then explain what the business should do next. This is a practical exercise in turning imperfect data into a reproducible result that senior staff can use.

**Allow about one hour, including reading and notes. This is a guide, not a hard limit.** You may spend longer. Working partial submissions receive credit for the evidence they contain. We reward clear, useful communication; speed, extra features and a particular file format earn no automatic bonus.

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

Make your code and notes changes in these four files. You may also add your own business report and an optional preview:

| File | What to do |
| --- | --- |
| `solution.py` | Repair `prepare_orders`: normalize and validate the input, handle duplicate orders and report quality counts. |
| `analysis.sql` | Calculate performance by period, channel and product category, handling refunds without losing or multiplying orders. Keep business calculations in SQL. |
| `tests/test_candidate.py` | Add at least one Python test and one SQL test, each using small independent inputs and a hand-calculated expected result. Each should catch a plausible error. |
| `NOTES.md` | Give your business recommendation or identify your separate report, then explain your method using the supplied headings. |

The generator, database loading, HTML report, reproducibility check and ZIP packaging are supplied. You can use the supplied HTML report or present your findings in a format you choose, including **PowerPoint or Power BI**. Building a separate report is optional.

A suggested hour is 10 minutes to read and run the starter, 25 minutes for Python and SQL, 10 minutes for tests, and 15 minutes for the recommendation, final run and packaging. Prioritize a result you can explain. If something remains unfinished, say what it is in your notes and submit a working partial result.

## Explain the result

Prepare a brief business report for a nontechnical senior reader: roughly **200 words, a few slides or one focused dashboard**. Explain the period change, cite at least two corrected result values, identify a material channel/category segment, recommend an action and quantify one illustrative opportunity. State the assumption or limitation behind that estimate.

Choose either route:

- **Supplied HTML report:** write up to 200 words under **Business recommendation** in `NOTES.md`. The pipeline includes them in `output/report.html` alongside the calculated results.
- **Your own report:** use any file format that communicates the findings well. PowerPoint and Power BI are welcome. Under **Business recommendation**, identify its archived filename, for example `business-report/Performance report.pptx`, instead of repeating the narrative in your notes. Submit an actual file, not only a public or account-gated link. If it needs specialist software, we recommend a readable PDF or image preview. If the report needs multiple files, put them in one ZIP and submit that as the report.

Keep a separate report concise, for example a few slides or one focused dashboard; it has no fixed word limit. The 200-word limit applies only to an inline recommendation in `NOTES.md`. Clarity, evidence and usefulness to the reader are assessed within the existing business value and communication score. Useful charts, clear slides or focused dashboard interactions can strengthen that score. Choosing a particular tool or file extension does not earn extra points.

One possible scenario is the current refund value minus the current gross sales multiplied by the baseline refund-to-gross ratio for a chosen segment, holding sales and other costs fixed. A negative result is not a saving. Another coherent, supported scenario is welcome. A scenario is not a forecast, a realized saving or evidence that one factor caused the change.

In **Method and scale**, use up to **100 words**. Describe one correction and how you checked it, your AI or manual method, and one bottleneck, proposed change and tradeoff at **five million orders**. If you used AI, name the model if known, its purpose and an output you verified. Token or cost figures are optional; label estimates or unknown values honestly.

You may use your own AI tools. We do not supply AI access or credits, and paid access earns no advantage. You remain responsible for the submitted work and should be able to explain it. Do not include credentials, chat logs or personal information in the files.

## Verify and submit privately

Run your tests, regenerate the final outputs twice, then build the ZIP. For the supplied HTML report:

```sh
python3 -m unittest discover -s tests
python3 run.py --check-repro
python3 package_submission.py
```

For a separate report, run the same tests and final pipeline command, then package the report file:

```sh
python3 package_submission.py --business-report "reports/Performance report.pptx"
```

You can also include a preview, for example for a Power BI report:

```sh
python3 package_submission.py --business-report "reports/Performance report.pbix" --report-preview "reports/Performance preview.pdf"
```

Replace the example paths with your files. Relative paths resolve from the task folder. `--report-preview` requires `--business-report`. The report is copied unchanged into `business-report/<filename>` and the preview into `business-report/preview/<filename>` inside the submission ZIP. They can share a filename because they occupy separate folders. Update the report filename in `NOTES.md` before the final `--check-repro` run.

The required final pipeline command is `python3 run.py --check-repro`. It compares the summary, quality counts, report and manifest byte for byte across two complete runs. It writes a reproducibility record only when they match. Repeatability is evidence that the process is stable; it does not prove the answers are right.

The five output files are:

| File | Purpose |
| --- | --- |
| `output/summary.csv` | Your SQL results. |
| `output/quality.json` | Your six data quality counts. |
| `output/report.html` | Supplied performance comparisons and the business section of your notes, containing either your recommendation or a reference to your separate report. |
| `output/manifest.json` | Input, code and output hashes, dataset settings and environment versions. |
| `output/reproducibility.json` | The successful two-run comparison. |

Email **`submission.zip`** using the recruiter invitation or reply channel. **Do not publish answers through a public fork, pull request or issue.** The ZIP contains the code, SQL, tests, documentation, notes, five generated output files and any report/preview explicitly supplied to the packager. A working partial submission also needs the reproducibility record.

The five technical output files remain required whichever report format you choose. Someone extracting the ZIP can regenerate them and the data with the documented command, without network access. A separately authored report and preview are preserved byte for byte, but are not regenerated by the pipeline. Check that they agree with your final results.

The default package excludes raw CSVs, the database, large logs, credentials, Git history and this repository's management PowerPoint. **Your own PowerPoint is included when you pass it with `--business-report`.** Explicitly selected report and preview files are included unchanged.

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

This is assessment version 4.1; the data generator remains version `v4`. The [previous assessment](https://github.com/Jasonada13/ai-solutions-intern-task/tree/assessment-v3) is retained for reference. A [management overview](docs/technical-task.pptx) is also available.
