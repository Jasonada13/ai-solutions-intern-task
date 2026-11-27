# Technical task

Use Python and SQL to investigate a fictional automotive components supplier's performance, then recommend what the business should do next. Your results should be reproducible and useful to senior staff. No automotive knowledge is required.

Allow about one hour, including reading and writing your response. There is no hard time limit. Working partial submissions receive credit for the evidence they contain. We assess clear, useful communication. Speed, extra features and file format earn no automatic bonus.

## The business question

A fictional supplier sells components to vehicle manufacturers, parts distributors, and workshop networks. Its senior team wants to understand why sales increased while contribution weakened, and what to do next. Compare two equal periods. The `baseline` covers 1 to 28 May 2026, and `current` covers 1 to 28 June 2026. Both have the same completed 30-day follow-up for customer credits on returned components.

You will work with 20,000 generated base orders, plus repeated deliveries, invalid rows, products, and customer credits. The dataset fits on a laptop without cloud infrastructure or distributed processing.

Contribution means net revenue minus component and fulfilment costs. It excludes fixed overhead, tax, and acquisition spend, so it is not profit. All money is in GBP pence.

The scenario and generator were created with AI assistance. The generator creates all synthetic rows locally and deterministically. Every company, product code, price, volume, and pattern is invented. The data is not sourced or derived from any real company and does not represent industry benchmarks.

## Start here

Use Python 3.10 or newer with its standard library and SQLite support. No additional packages, accounts, API keys or paid tools are needed. Download or clone this repository, open a terminal in its folder and run:

```sh
python3 run.py --check-setup
python3 run.py --check-repro
```

On Windows, use `python` or `py` in place of `python3` if needed.

The supplied pipeline generates CSVs, prepares orders, builds a local SQLite database, runs the SQL and creates a self-contained report. The starter runs with deliberately incorrect data preparation and SQL. Setup checks, supplied tests and a successful repeat run do not prove the results are correct.

Read [DATA.md](DATA.md) for the exact rules, types and output columns. Open `output/report.html` in a browser to see the supplied report layout.

## Your work

Make your code and response changes in these four files. You may also add a business report and preview:

| File | What to do |
| --- | --- |
| `solution.py` | Repair `prepare_orders`: normalize and validate the input, handle duplicate orders and report quality counts. |
| `analysis.sql` | Calculate performance by period, customer channel, and component family. Handle customer credits without losing or multiplying orders. Keep business calculations in SQL. |
| `tests/test_candidate.py` | Add at least one Python test and one SQL test, each using small independent inputs and a hand-calculated expected result. Each should catch a plausible error. |
| `RESPONSE.md` | Give your business recommendation or identify your separate report, then explain your method using the supplied headings. |

The generator, database loading, HTML report, reproducibility check and ZIP packaging are supplied. You can use the HTML report or choose another format. PowerPoint and Power BI are encouraged where they help explain your findings. A separate report is optional.

Suggested timing is 10 minutes to read and run the starter, 25 minutes for Python and SQL, 10 minutes for tests, and 15 minutes for the recommendation, final run and packaging. Prioritize a result you can explain. Note any unfinished work and submit a working partial result.

## Explain the result

Prepare a brief report for a nontechnical senior reader. Explain the period change and cite at least two corrected result values. Identify a material segment by customer channel and component family. Recommend an action and quantify one illustrative opportunity. State the assumption or limitation behind your estimate.

Choose either route:

- Use the supplied HTML report. Write up to 200 words under `Business recommendation` in `RESPONSE.md`. The pipeline includes this text in `output/report.html` alongside the results.
- Submit your own report in any file format. Under `Business recommendation`, give its archived filename, such as `business-report/Performance report.pptx`, rather than repeating the narrative. Submit an actual file; a link alone is insufficient. If the report needs multiple files, put them in one ZIP and submit that as the report. For formats that need specialist software, a readable PDF or image preview is recommended and optional.

Keep a separate report concise, such as a few slides or one focused dashboard. It has no fixed word limit. The 200-word limit applies only to the inline recommendation in `RESPONSE.md`. We assess clarity, evidence and usefulness within the business value and communication score. Charts, slides and dashboard interactions can improve that score when they help the reader. The tool and file extension earn no extra points.

For one possible scenario, choose a segment and subtract current gross sales multiplied by its baseline credit-to-gross ratio from its current credit value. Hold sales and other costs fixed. A negative result is not a saving. You may use another supported scenario. Treat the estimate as an illustration, not a forecast, realized saving, or proof of causality.

Use up to 100 words under `Method and scale`. Describe one correction and how you checked it, your AI or manual method, and one bottleneck, proposed change and tradeoff at five million orders. If you used AI, name the model if known, its purpose and an output you verified. Token or cost figures are optional. Label estimates and unknown values.

Your own AI tools are optional. We do not supply AI access or credits, and paid access earns no advantage. You are responsible for your work and should be able to explain it. Exclude credentials, chat logs and personal information.

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

Replace the example paths with your files. Relative paths resolve from the task folder. `--report-preview` requires `--business-report`. The packager copies the report unchanged into `business-report/<filename>` and the preview into `business-report/preview/<filename>` inside the ZIP. They may share a filename because they occupy separate folders. Update the report filename in `RESPONSE.md` before the final `--check-repro` run.

Run `python3 run.py --check-repro` before packaging. It compares the summary, quality counts, report and manifest byte for byte across two complete runs. It writes a reproducibility record only when they match. Matching outputs confirm repeatability. Use your tests to check the calculations.

The five output files are:

| File | Purpose |
| --- | --- |
| `output/summary.csv` | Your SQL results. |
| `output/quality.json` | Your six data quality counts. |
| `output/report.html` | Supplied performance comparisons and the business section of your response, containing either your recommendation or a reference to your separate report. |
| `output/manifest.json` | Input, code and output hashes, dataset settings and environment versions. |
| `output/reproducibility.json` | The successful two-run comparison. |

Email `submission.zip` privately using the recruiter invitation or reply channel. Keep your answers out of public forks, pull requests and issues. The ZIP contains code, SQL, tests, documentation, your response, five generated output files and any report and preview you passed to the packager. Working partial submissions also need the reproducibility record.

All five output files are required whichever report format you choose. Someone extracting the ZIP can regenerate them and the data with the documented command, without network access. The pipeline does not regenerate a separate report or preview. Check that these files agree with your final results.

The default package excludes raw CSVs, the database, large logs, credentials, Git history and this repository's PDF and PowerPoint overviews. To include your own PowerPoint, pass it with `--business-report`. The packager preserves selected report and preview files unchanged.

`python3 run.py` performs one full run and removes any previous reproducibility record. Both run modes remove stale generated outputs if the pipeline fails. You can use `--orders` and `--seed` to try alternate data; use the default dataset for your submitted result.

## How we review it

| Area | Points |
| --- | ---: |
| Python and data preparation | 25 |
| SQL and metrics | 25 |
| Business value and communication | 25 |
| Verification and reproducibility | 15 |
| Tool and scale judgment | 10 |

Reviewers assess your reasoning, recommendations and verification. They may use automated checks and AI-assisted technical review. Human reviewers award partial credit and make shortlist decisions. Shortlisted candidates may be asked to explain their approach to technical and nontechnical audiences.

A [task overview](docs/technical-task.pdf) summarises the instructions and assessment criteria. A [PowerPoint overview](docs/technical-task.pptx) is also available.
