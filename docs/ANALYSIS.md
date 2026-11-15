# Historical observation analysis

## Purpose

The command-line program app.py analyses a structured CSV observation log. It checks the data format, classifies entries by verification status, and summarizes the listed-price value of handovers recorded as observed unpaid.

It is separate from the live Flask application. It reads data.csv by default and does not write to the SQLite operational database.

## Run

    python app.py
    python app.py --data path/to/observations.csv

The CLI uses only the Python standard library. A relative path supplied to --data is resolved relative to the repository directory; an absolute path is used as supplied.

Exit status:
- 0: report generated, or no non-empty data rows were found.
- 2: input file could not be read or failed validation.

## CSV schema

The input must contain all of these columns:

| Column | Meaning |
|---|---|
| timestamp | Local observation time in YYYY-MM-DD HH:MM format |
| item | Product name |
| unit_price | Unit price in rupees |
| qty_handed_over | Number of units handed to the customer/group |
| qty_paid_for | Number of units covered by payment observed |
| crowd_level | low, medium, or high |
| observation_note | Short factual note about the handover/payment observation |
| verification_status | paid, observed_unpaid, or needs_follow_up |
| data_origin | Source/location attribution for the record |

Blank rows are skipped. Required fields must be present in the header. Each non-empty row is validated for timestamp format, positive price, quantity bounds, allowed crowd level, allowed status, and non-empty item/source.

The current validator parses price as a floating-point number and quantities as integers. The web tracker uses integer paise for transaction money; the CLI's current CSV format is retained as supplied and should be treated as a field-analysis calculation rather than an audited ledger.

## Verification statuses

- **paid:** All units handed over are recorded as paid. The validator rejects a paid row if paid quantity differs from handed-over quantity.
- **observed_unpaid:** At least one unit is recorded as unpaid based on the observer's direct observation. These rows contribute to the observed-unpaid potential value.
- **needs_follow_up:** Payment status is uncertain and requires checking. These rows are kept separate and excluded from observed-unpaid potential value.

Use needs_follow_up when payment may have been delayed, collected as part of a group payment, or could not be reliably observed. Do not use observed_unpaid simply because payment was not immediately visible.

## Calculation

For each row:

    row value = (qty_handed_over - qty_paid_for) × unit_price

The analysis sums this value for rows marked observed_unpaid. It separately sums the same calculation for needs_follow_up rows, but does not include that amount in the observed-unpaid potential value.

The report groups observed-unpaid value by:
- Item name.
- Time window derived from the timestamp.

Time windows are assigned as follows:
- Before 10:00
- 10:00–11:59
- 12:00–13:59
- 14:00–15:59
- 16:00–17:59
- 18:00 onward

The report also displays row count, total units handed over, total units paid for, observed-unpaid row count, follow-up row count, and units in observed-unpaid rows.

## Current recovered dataset

The repository currently contains 20 observation entries dated 14 November 2026 and attributed in the CSV to NIT Silchar Tapri — Rupam Das. The existing unit tests assert:

- 20 rows are loaded.
- Five rows are marked observed_unpaid.
- Two rows are marked needs_follow_up.
- Five units are in observed-unpaid rows.
- Observed-unpaid potential value is ₹95.
- Follow-up value is ₹10 and remains excluded from the potential value.

These are arithmetic summaries of the records in the file. They do not establish intent, prove theft, or establish a representative loss rate.

## Interpretation cautions

- The output depends on the accuracy and completeness of the source observations.
- The program does not independently verify payment, identity, intent, or whether a group paid later.
- A short observation window cannot be extrapolated into daily, weekly, monthly, or annual loss estimates.
- Listed unit prices must reflect the prices applicable at the time of observation.
- The time-window grouping is descriptive, not a statistical test of causation.
- No customer identity should be collected for this analysis.

## Validation and tests

Run:

    python -m unittest discover -s tests -v

The analysis tests check the recovered dataset summary and reject invalid crowd levels and quantity bounds. See TESTING.md for the full test entry point.
