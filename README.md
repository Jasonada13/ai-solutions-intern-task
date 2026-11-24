# Technical task

Advanced version 3. The [previous assessment](https://github.com/Jasonada13/ai-solutions-intern-task/tree/assessment-v2) remains available for reference. Use the version named in your invitation.

An online retailer has a channel report that runs but gives the wrong answer. Orders arrive as revisions, refunds can be delivered more than once, and some records arrive after the reporting cutoff. Repair the Python and SQL, prove two corrections with small tests, and explain whether the report supports a business decision.

The [Technical task presentation](docs/technical-task.pptx) gives a plain-English overview.

Plan for about one hour, including reading and notes. This is a guide, with no hard time limit. The task is deliberately challenging. Submit your strongest evidence even if you do not finish. Correct parts receive partial credit. Time spent, extra features, and visual polish do not earn points.

## Start

Use Python 3.10 or later. No packages, database server, cloud account, or API key are required.

Choose **Code > Download ZIP**, or clone this repository:

```sh
git clone https://github.com/Jasonada13/ai-solutions-intern-task.git
cd ai-solutions-intern-task
```

Run these commands in the task folder:

```sh
python3 run.py --check-setup
python3 run.py
python3 -m unittest discover -s tests
```

On Windows, use `python` or `py` instead of `python3`. The setup check prints `Setup OK`. The starter creates `output/summary.csv` and `output/quality.json`, but its results are deliberately wrong. Supplied tests pass because they check file loading, formatting, and packaging only. They do not validate the Python or SQL answer.

## Repair the report

Read [DATA.md](DATA.md) for the complete rules and supplied helper functions. The report covers May orders using information available by 5 June 2026.

1. Repair `reconcile_orders()` in `solution.py`. Select the latest eligible revision of each order and report unresolved conflicts. Respect the single-pass and memory requirements.
2. Repair `analysis.sql`. Calculate the channel summary in SQL, using the selected orders and eligible, distinct refund events.
3. Add at least two automated tests in `tests/test_candidate.py`, one for Python and one for SQL. Each must use a small, self-contained example and assert a hand-calculated result that catches a plausible bug. The placeholder imports the supplied records and SQL helper.
4. Complete [NOTES.md](NOTES.md) in at most 200 words total. Assess a proposed business decision, cite two corrected result values, and explain your verification, working method, and one scaling tradeoff. Name unfinished work if relevant.
5. Run your solution and tests again:

```sh
python3 run.py
python3 -m unittest discover -s tests
```

Edit only `solution.py`, `analysis.sql`, `tests/test_candidate.py`, and `NOTES.md`. Keep the supplied models, fixtures, runner, and packaging unchanged. Python owns order reconciliation. SQL owns the report metrics. No presentation, interface, or deployment is required.

To explore a different cutoff, you can run `python3 run.py --as-of 2026-06-07T00:00:00Z`. Run `python3 run.py` again before submission so the submitted outputs use the default cutoff.

AI is optional. We provide no AI accounts or credits, and no purchase is expected. You may use your own tools. Describe your method and an output you verified in the notes. If you used AI, give the tool, model if known, purpose, and why that model suited the task. Token usage and cost are optional. Paid access and high spend do not earn points. Do not include full chat logs or credentials.

## Submit by email

Run:

```sh
python3 package_submission.py
```

Email `submission.zip` through the invitation or reply channel provided by your recruiter. If the recruiter supplied an identifier, you may use it in the ZIP filename. No personal identity fields are required inside the task. Do not publish your answers in a fork, pull request, or issue.

The ZIP includes the task files, fixtures, tests, notes, and both generated outputs. Packaging checks that these named files exist; it does not check correctness. Partial work is welcome. If your changes no longer run, keep a working partial version so you can generate the outputs, and describe what remains in your notes.

## Assessment criteria

| Area | Points | Evidence |
| --- | ---: | --- |
| Python reconciliation | 30 | Cutoff and revision selection, persistent conflict handling, deterministic outputs, unchanged inputs, and one-pass memory use |
| SQL analysis | 30 | Order eligibility, refund cutoff and deduplication, join cardinality, totals, counts, and real-valued rate |
| Business interpretation | 20 | Two accurate values, a justified decision and next action, and a limitation |
| Verification | 10 | One Python and one SQL counterexample test, with hand-calculated expectations and specific evidence |
| Tool and scale judgment | 10 | Appropriate AI or manual method, and a bottleneck, proposed change, and tradeoff at 100 million orders |

All assessed technical rules are in [DATA.md](DATA.md). We use automated checks and AI-assisted technical review, with human review of partial work and shortlist decisions.
