# Python and SQL intern assessment

Help an online retailer decide which sales channel deserves investigation. Clean an order export in Python, calculate channel metrics in SQL, and explain what the results mean.

Plan for about 60 minutes including reading, coding, and notes. This is a guide, not a limit. Spend as long as you choose. Elapsed time, extra features, and visual polish do not earn points.

## Start

Use a standard Python installation, version 3.10 or later. Python 3.11 or later is recommended. No packages, database server, paid account, or API key are required.

Use **Code > Download ZIP**, or clone this repository:

```sh
git clone https://github.com/Jasonada13/ai-solutions-intern-task.git
cd ai-solutions-intern-task
```

In the task folder, run:

```sh
python3 run.py --check-setup
python3 -m unittest discover -s tests
```

On Windows, use `python` or `py` instead of `python3`. The setup check prints `Setup OK`. The supplied tests pass before you complete the task. They check the starter, not your answer.

## Complete the task

Read [the data reference](DATA.md) for every cleaning rule and metric definition.

1. Implement `clean_orders()` in `solution.py`. Use Python for cleaning.
2. Write one SELECT query in `analysis.sql`. Use SQL for all aggregations.
3. Add at least one meaningful automated test in `tests/test_candidate.py`. Check a result or edge case from the data reference.
4. Run your solution and tests:

```sh
python3 run.py
python3 -m unittest discover -s tests
```

The runner creates `output/summary.csv`. Before implementation, it exits with an incomplete-task message.

5. Complete [NOTES.md](NOTES.md) in at most 200 words total. Give a business recommendation supported by two result values, an action, and a limitation. Explain one bottleneck at 100 million orders, one change, and its tradeoff. Describe your verification and working method using the prompts.

Keep your work in `solution.py`, `analysis.sql`, `tests/test_candidate.py`, and `NOTES.md`. Keep the supplied fixtures and runner unchanged.

AI is optional. No AI purchase or account setup is expected. In `NOTES.md`, describe the tool, model if known, purpose, one output you checked, and why the model suited the task. Usage and cost figures are optional. Do not include full chat logs.

## Submit by email

Run:

```sh
python3 package_submission.py
```

Email `submission.zip` through the invitation or reply channel provided by your recruiter. If the recruiter supplied an identifier, you may use it in the ZIP filename. No personal identity fields are required inside the task. Do not publish your answers in a fork, pull request, or issue.

The ZIP contains the named task files, fixtures, tests, notes, and generated summary. Packaging requires those files to exist.

## Assessment criteria

| Area | Points | Evidence |
| --- | ---: | --- |
| Python cleaning | 30 | Correct normalization, validation, duplicates, order, and unchanged inputs |
| SQL analysis | 30 | Correct eligibility, counts, sums, refund cardinality, rate, and output |
| Business interpretation | 20 | Two accurate values, a supported action, and a limitation |
| Verification | 10 | A meaningful passing test and a specific check or correction |
| Tool and scale judgment | 10 | Appropriate AI or manual method, and a bottleneck, change, and tradeoff |

We use automated checks and AI-assisted technical review. People make shortlist decisions. All tested rules are in the data reference. No slides, video, or diagrams are required.
