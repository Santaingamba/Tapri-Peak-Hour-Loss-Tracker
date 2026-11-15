# Tapri Peak-Hour Loss Tracker

A phone-friendly daily order and payment-reconciliation app for the NIT Silchar tapri. The existing observation-analysis CLI (app.py) remains available; web_app.py adds the operational tracker.

## Daily workflow

1. Open the app on a phone or laptop.
2. Record item, price, quantity served, quantity paid for, payment method, and an optional note.
3. The app flags a quantity mismatch immediately.
4. Check cash/UPI records and confirm whether the amount is genuinely still unpaid.
5. If payment arrives later, record it against the original order. The outstanding balance decreases.
6. Review today's orders or filter history by date.

The dashboard shows order count, units served, payments recorded (including later recoveries), and the amount still needing reconciliation. A mismatch is a prompt to check, not proof of deliberate non-payment.

## Run locally

Requires Python 3.10+.

    python -m venv .venv
    # Windows PowerShell
    .\.venv\Scripts\Activate.ps1
    # macOS / Linux
    source .venv/bin/activate
    pip install -r requirements.txt

Generate a random session secret:

    python -c "import secrets; print(secrets.token_urlsafe(48))"

Set both values in the same terminal before starting. Use a private password/passphrase of at least 8 characters; never use example credentials.

Windows PowerShell:

    $env:TAPRI_SECRET_KEY = "paste-generated-random-secret"
    $env:TAPRI_ADMIN_PIN = "choose-a-private-password"

macOS / Linux:

    export TAPRI_SECRET_KEY='paste-generated-random-secret'
    export TAPRI_ADMIN_PIN='choose-a-private-password'

Start with:

    python web_app.py

Open http://127.0.0.1:5000. The first run creates tapri.sqlite3 beside web_app.py. For a phone on the same trusted private Wi-Fi, set TAPRI_HOST=0.0.0.0 and open http://computer-lan-ip:5000 on the phone. Do not expose Flask's development server directly to the public internet. Remote use requires a production WSGI server, HTTPS reverse proxy, TAPRI_HTTPS=1, and persistent protected storage.

Optional variables: TAPRI_DB_PATH (database path), TAPRI_TIMEZONE (defaults to Asia/Kolkata), TAPRI_HOST (defaults to 127.0.0.1), PORT (defaults to 5000), and TAPRI_HTTPS (defaults to 0).

## Data and privacy

- The live app starts with an empty operational database. It does not automatically import the historical observation CSV; those records belong to the separate observation exercise.
- products.csv supplies item suggestions and reference prices. Verify prices at the counter; each saved order retains its own price.
- Do not enter customer names, phone numbers, account details, faces, or other identifying information.
- The app does not connect to banks, UPI notifications, QR payments, CCTV, or a POS terminal. Payment records must be verified by the operator.
- Back up tapri.sqlite3 securely. The password is hashed, but the database itself is not encrypted.
- Never commit .env, credentials, or the SQLite database.

## Security controls

Owner password hash (scrypt), required random session secret, HTTP-only and SameSite session cookies, optional Secure cookie for HTTPS, session rotation on login, CSRF checks on POST forms, login throttling (8 failed attempts per IP per 15 minutes), parameterized SQL, SQLite foreign keys, bounded input validation, integer-paise money storage, serialized recovery balance checks, Jinja auto-escaping, request-size limit, security headers, and debug mode disabled.

This is a small single-owner operational tool, not a payment processor or audited accounting system. Public deployment still requires a production WSGI server, HTTPS, persistent protected storage, backups, and an independent security review.

## Existing analysis tool

    python app.py
    python app.py --data path/to/observations.csv
    python -m unittest discover -s tests -v

The recovered historical dataset in data.csv is retained for analysis and is not inserted into the live transaction ledger.

## Calculation

Initial mismatch = (quantity served - quantity paid) × unit price. Later payments reduce the outstanding balance. Uncertain mismatches are never silently treated as confirmed loss.
