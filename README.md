# Automated Testing of a Banking Transaction Module

ISE2501 Software Testing & Quality Assurance, CA3 (Option 1: Specialized Tool Exploration & Program Unit/API Testing).

A Python banking module tested with pytest and Coverage.py, with mocks, property-based tests, mutation testing and a GitHub Actions pipeline.

**Team (Section 5ISE04)**

- Thirth Patel, 20241ISE0226 (Student A: Lead Tool Architect)
- Vaishnavi V, 20231ISE0180 (Student B: Lead Test Designer)

## Results

| Measure | Result |
|---|---|
| Tests | 155 passed, 0 failed |
| Duration | About 3 seconds |
| Statement and branch coverage | 100% (257 statements, 48 branches) |
| Mutation score | 97.2% (307 of 316 mutants killed) |
| Defects logged and fixed | 6 (5 seeded, 1 design gap) |

The 9 surviving mutants were reviewed by hand and do not change behavior. See the [defect log](docs/defect-log.md).

## Tools

All tools are free and open source. Versions are the ones used for the results above.

| Tool | Version | Used for |
|---|---|---|
| pytest | 9.2.0 | Running tests, fixtures, parameterization and markers |
| Coverage.py (through pytest-cov 7.1.0) | 7.17.1 | Statement and branch coverage, with a 90% gate |
| pytest-html | 4.2.0 | HTML test report |
| pytest-mock | 3.17.0 | Mocking the SMS and email gateway |
| Hypothesis | 6.170.14 | Property-based tests |
| Cosmic Ray | 8.7.0 | Mutation testing |
| GitHub Actions | N/A | Running the tests on each push and pull request |

## Run it

You need Python 3.12 or newer.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest --cov --cov-report=term-missing --cov-report=html --cov-report=xml --html=reports/test-report.html --self-contained-html
```

**Linux or macOS**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest --cov --cov-report=term-missing --cov-report=html --cov-report=xml --html=reports/test-report.html --self-contained-html
```

The run fails if coverage drops below 90%. Reports are written to:

- `reports/test-report.html` for pass/fail results
- `reports/coverage-html/index.html` for line-by-line coverage

### Other useful commands

Replace `python` with the virtual environment path shown above.

| Goal | Command |
|---|---|
| Boundary tests only | `python -m pytest -m boundary` |
| Negative tests only | `python -m pytest -m negative` |
| Property-based tests only | `python -m pytest -m property` |
| Mutation testing (about 6 minutes) | `python scripts/run_mutation.py` |

Mutation testing temporarily edits files in `src/`, so don't edit code or run other tests while it runs.

## Project layout

```text
src/bank/          System under test
  validation.py    Input checks
  service.py       Banking operations and rules
  fees.py          Transfer fee tiers
  interest.py      Savings interest slabs
  models.py        Accounts and statements
  ports.py         Storage and notification boundaries
  errors.py        Error codes
tests/             Test suite, fixtures and CSV test data
scripts/           Mutation testing runner
docs/              Specification, test matrix, defect log and run evidence
.github/workflows/ CI pipeline
```

## Documentation

- [Module specification](docs/specification.md)
- [Test case matrix](docs/test-matrix.md)
- [Defect log](docs/defect-log.md)
- [Defect fixes](docs/defects/fixes.diff)
- [Run evidence](docs/evidence)

## About the defects

Defects D1 to D5 were seeded on purpose to check that the tests catch real faults. D6 was a real design gap in our first draft. The run evidence includes the failing run from before the fixes and the passing run after them.

## AI assistance

Claude Code (Anthropic) was used in building this project.
