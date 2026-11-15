# Tapri Peak-Hour Loss Tracker

A lightweight, phone-friendly order recording and payment-reconciliation project for a small campus tapri at NIT Silchar. It is designed to help the owner review handovers, payments, and possible outstanding amounts during busy periods.

The repository contains **two related but separate tools**:

- **Historical observation analysis** — a Python command-line program that validates and summarizes the recovered observation log in data.csv.
- **Daily operational tracker** — a Flask web application that records new orders in a local SQLite database, highlights quantity/payment mismatches, and records later payments.

The historical CSV is not automatically imported into the live transaction database. This separation prevents an observation exercise from being mistaken for the owner's ongoing transaction ledger.

## Contents

| Path | Purpose |
|---|---|
| web_app.py | Flask application for daily order entry and reconciliation |
| app.py | Standard-library CLI for analysing observation CSV files |
| data.csv | Recovered observation dataset used by the CLI |
| products.csv | Item names and reference prices used for menu suggestions |
| requirements.txt | Python runtime dependencies |
| .env.example | Names and descriptions of runtime environment variables; contains placeholders only |
| tests/ | Automated tests for both applications |
| research.md | Problem framing, background sources, and evidence boundaries |
| fieldwork.md | Fieldwork method, owner-conversation, and evidence record |
| reflection.md | Student-authored reflection prompt |
| ai-chats/README.md | Instructions for adding actual AI conversation exports |
| docs/ | Detailed setup, usage, architecture, testing, and security documentation |

## What the application does

### Daily web tracker

1. The operator signs in with the owner password configured locally.
2. They record the item, unit price, quantity served, quantity paid for, payment method, crowd level, and an optional note.
3. If the served and paid quantities differ, the app sends the operator to the order detail page so the discrepancy can be checked.
4. The operator reviews cash/UPI records and may mark the remaining amount as confirmed unpaid.
5. If a payment arrives later, the operator records the amount against the original order. The outstanding balance is recalculated.
6. The dashboard shows today's order count, units served, recorded payments, and amounts still requiring reconciliation. The history page filters records by date.

A mismatch is a **reconciliation prompt**, not proof of theft or intent. A later payment can reduce the balance to zero.

### Historical CSV analysis

The CLI validates the required columns, timestamps, prices, quantities, crowd levels, and verification statuses. It separates entries marked observed_unpaid from entries marked needs_follow_up, then summarizes the value of the former by time window and item.

For the recovered dataset currently in the repository, the tested analysis reports 20 entries, five observed-unpaid entries totalling ₹95, and two follow-up entries totalling ₹10. The ₹10 is excluded from the observed-unpaid potential value. These are findings from this short recorded sample, not an estimate of daily or monthly losses.

## Quick start: web application

Requires Python 3.10 or newer.

### 1. Clone and create an environment

    git clone https://github.com/Santaingamba/Tapri-Peak-Hour-Loss-Tracker.git
    cd Tapri-Peak-Hour-Loss-Tracker
    python -m venv .venv

Activate it:

**Windows PowerShell**

    .\.venv\Scripts\Activate.ps1

**macOS / Linux**

    source .venv/bin/activate

Install dependencies:

    python -m pip install --upgrade pip
    pip install -r requirements.txt

### 2. Configure secrets

Generate a high-entropy session secret:

    python -c "import secrets; print(secrets.token_urlsafe(48))"

Set both environment variables in the same terminal session. Choose a private password of at least eight characters; do not reuse a public or example password.

**Windows PowerShell**

    $env:TAPRI_SECRET_KEY = "paste-the-generated-secret"
    $env:TAPRI_ADMIN_PIN = "choose-a-private-password"

**macOS / Linux**

    export TAPRI_SECRET_KEY='paste-the-generated-secret'
    export TAPRI_ADMIN_PIN='choose-a-private-password'

The application refuses to start if either required value is missing or too short. The environment variable name TAPRI_ADMIN_PIN is retained for compatibility; it is used as the owner sign-in password, not as a numeric PIN.

### 3. Start the app

    python web_app.py

Open http://127.0.0.1:5000 in a browser on the same computer. The first run creates a SQLite database named tapri.sqlite3 beside the application unless TAPRI_DB_PATH is set.

For more detail, including phone-on-Wi-Fi use and deployment cautions, see docs/SETUP.md.

## Quick start: historical analysis

No third-party package is needed for the CLI; it uses the Python standard library.

    python app.py
    python app.py --data path/to/another-observation-file.csv

Run the complete automated test suite with:

    python -m unittest discover -s tests -v

See docs/ANALYSIS.md for the CSV schema, status definitions, calculation, and interpretation limits.

## Important data and privacy notes

- The live web app starts with an empty operational database. It does not import data.csv.
- products.csv provides menu suggestions, not authoritative live pricing. Confirm the price at the counter; each order stores the price entered at the time.
- Do not enter customer names, phone numbers, account details, or other identifying information.
- The app does not integrate with a bank, UPI provider, QR payment system, CCTV, or POS terminal. Payment information is entered and checked by a person.
- The SQLite database contains operational records. Protect it and make secure backups; password hashing does not encrypt the database.
- Never commit real credentials, environment files, local databases, or private fieldwork photos.
- The recovered observation data should be interpreted only within its documented scope.

## Project status and limitations

Implemented: order recording, discrepancy flags, later-payment recovery, date-filtered history, owner sign-in, local SQLite persistence, input validation, CSRF checks, login throttling, security headers, and automated tests.

Not implemented: automatic payment verification, bank/UPI integration, inventory deduction, customer accounts, multi-user roles, cloud synchronization, CSV export from the web app, edit/delete workflows, or a hosted production deployment.

This is a small operational aid and not a payment processor, inventory system, audited accounting package, or forensic tool. A successful CI run is useful evidence that the automated checks passed; it is not a guarantee of zero defects or a substitute for field testing.

## Documentation

- [Setup and deployment](docs/SETUP.md)
- [Daily user guide](docs/USER_GUIDE.md)
- [Historical data analysis](docs/ANALYSIS.md)
- [Architecture and data model](docs/ARCHITECTURE.md)
- [Testing and quality checks](docs/TESTING.md)
- [Security and privacy](docs/SECURITY.md)
- [Research note](research.md)
- [Fieldwork record](fieldwork.md)
- [Student reflection prompt](reflection.md)

## Responsible interpretation

The purpose is to make payment reconciliation easier, not to label customers. A quantity mismatch can arise from delayed payment, a group settling together, a missed entry, or an observation error. Only classify an amount as confirmed unpaid after checking the available payment evidence. Do not infer motive, identify individuals, or extrapolate the small observation sample into a wider loss estimate.
