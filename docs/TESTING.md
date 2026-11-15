# Testing and quality checks

## Run all tests locally

From the repository root, with the project's Python environment active:

    python -m unittest discover -s tests -v

The test suite includes tests for the historical CSV analysis and the Flask web app.

## Historical analysis tests

tests/test_app.py checks that:
- The recovered CSV loads 20 rows.
- All rows retain the expected source attribution.
- Five entries are observed_unpaid.
- Two entries need follow-up.
- The observed-unpaid potential value is ₹95.
- The follow-up value is ₹10 and remains separate.
- The report includes the expected totals.
- Invalid crowd levels and quantity bounds are rejected.

## Web application tests

tests/test_web_app.py creates an isolated temporary SQLite database for the test process and configures test credentials through environment variables before importing the application.

It checks that:
- Unauthenticated users cannot access the dashboard.
- An authenticated user can create an order with a quantity mismatch.
- A later recovery is recorded and reflected in the balance.
- A recovery larger than the outstanding amount is rejected.
- POST requests without a valid CSRF token are rejected.
- Invalid quantity combinations are not saved.
- Logging out removes authenticated access.

These tests are focused regression checks, not exhaustive browser, load, penetration, or deployment tests.

## Continuous integration

The GitHub Actions workflow in .github/workflows/tests.yml runs on pushes to main and pull requests targeting main. It checks out the repository, configures Python 3.12, installs requirements, compiles Python files, and runs unittest discovery.

A green workflow means those automated steps passed for that commit. It does not prove that every runtime environment, browser, network, or deployment configuration will work.

## Manual smoke-test checklist

Before using the app for real orders, test the following in a local environment:

1. Start with an empty test database.
2. Sign in using the configured password.
3. Submit a fully paid order and verify it appears as settled.
4. Submit a partially paid order and verify the balance.
5. Submit an order with zero quantity paid and verify the full value is outstanding.
6. Record a partial recovery and verify the balance decreases correctly.
7. Record the remaining recovery and verify the order becomes settled.
8. Attempt a recovery greater than the outstanding balance and verify it is rejected.
9. Confirm an unpaid status, then toggle it off.
10. Filter history by a date with records and a date without records.
11. Log out and verify the dashboard redirects to sign-in.
12. Reload the app and verify data persists in the same database file.
13. Open the interface on the intended phone/browser and check form usability.
14. Verify backups can be restored before relying on the database.

Use a disposable test database for manual testing. Do not experiment with live operational records.

## Reporting a defect

Record the Python version, operating system, exact steps to reproduce, expected result, actual result, and relevant non-sensitive error message. Never include passwords, session cookies, private database files, customer details, or secret environment values in an issue.
