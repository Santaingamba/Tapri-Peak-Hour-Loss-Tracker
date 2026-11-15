# Automated test suite

Run every test from the repository root:

    python -m unittest discover -s tests -v

## Test modules

| Module | Scope |
|---|---|
| test_app.py | CSV input validation, time windows, generated analysis invariants, aggregation consistency, recovered data regression |
| test_cli.py | End-to-end CLI process invocation, custom CSV paths, exit codes and terminal output |
| test_web_app.py | Flask route workflows, authentication, CSRF, login throttling, session rotation, input validation, recovery, XSS escaping, headers |
| test_web_database.py | SQLite constraints, foreign-key enforcement, persistence behavior |

## Test design principles

- Prefer behavior and invariant assertions over checking implementation details.
- Use generated datasets and independent expected-value calculations to exercise analysis logic.
- Use temporary files and an isolated temporary SQLite database for test data.
- Test invalid inputs and security boundaries as well as successful paths.
- Keep test fixtures separate from production logic.
- Never add special cases to application code solely to satisfy a test.
- A regression test should describe a real contract or previously observed defect, not merely freeze an accidental implementation detail.

The recovered CSV summary test is intentionally a dataset regression check. It verifies the current source file; the generated invariant tests separately exercise the analysis logic across many data shapes.

## CI

GitHub Actions runs the full suite on Python 3.10, 3.11, and 3.12 for pushes to main and pull requests targeting main.

A passing suite does not prove the absence of defects. Continue to perform manual browser/device tests, backup/restore checks, and deployment security review before using the tracker for real transactions.
