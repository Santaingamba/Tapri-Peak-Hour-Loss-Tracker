# Architecture and data model

## System overview

The repository has two independent execution paths:

    data.csv ──> app.py ──> validated observation rows ──> terminal report

    Browser ──HTTP──> Flask routes in web_app.py ──> SQLite database
                                  │
                                  └── products.csv (menu suggestions)

The CLI does not write to SQLite. The web app does not import or mutate the historical observation CSV.

## Components

### Historical analysis: app.py

- Uses csv.DictReader to read the selected observation file.
- Validates required headers and row values.
- Converts timestamps into datetime values.
- Assigns each observation to a time window.
- Calculates observed-unpaid and follow-up values separately.
- Aggregates observed-unpaid values by item and time window.
- Prints a text report and returns an error exit code for invalid input.

### Operational web app: web_app.py

- Flask provides the HTTP routes and request handling.
- Jinja templates are rendered from strings in web_app.py.
- SQLite stores orders, recoveries, sign-in settings, and login attempts.
- products.csv is read to populate item suggestions.
- Werkzeug password utilities hash and verify the owner password.
- The browser is the user interface; there is no separate frontend build pipeline.

## Main routes

| Route | Method | Purpose | Access |
|---|---|---|---|
| /health | GET | Basic process/database health response | Public |
| /login | GET, POST | Sign-in form and password verification | Public |
| / | GET | Today's dashboard and order form | Authenticated |
| /orders | POST | Create an order | Authenticated |
| /orders/<id> | GET | Order detail and recovery history | Authenticated |
| /orders/<id>/recover | POST | Record a later payment | Authenticated |
| /orders/<id>/confirm | POST | Toggle confirmed-unpaid status | Authenticated |
| /history | GET | Date-filtered order list | Authenticated |
| /logout | POST | End the session | Authenticated |

All state-changing routes use POST and require a CSRF token. Order IDs are integer route parameters and database access uses parameterized SQL.

## SQLite entities

### settings

Stores application settings, currently including the password hash. The raw password is not stored.

### orders

Each row represents one item line for an order/hand-over observation.

- id: integer primary key.
- created_at: timezone-aware ISO timestamp.
- item: item name entered by the operator.
- unit_price: price in integer paise.
- served: quantity handed over.
- paid_qty: quantity initially recorded as paid.
- method: cash, upi, mixed, or unknown.
- crowd: low, medium, or high.
- note: optional operational note.
- confirmed_unpaid: operator-controlled boolean flag.

### recoveries

Each row records a later payment associated with an order.

- id: integer primary key.
- order_id: foreign key to orders.
- amount: positive integer paise.
- recovered_at: timestamp.
- method: cash, upi, or other.
- note: optional note.

An order's outstanding amount is calculated as:

    initial mismatch = (served - paid_qty) × unit_price
    outstanding = initial mismatch - sum(recoveries)

The application rejects a recovery that exceeds the current outstanding balance. A database transaction serializes the read/check/write sequence to reduce race conditions.

### attempts

Stores sign-in attempt timestamps, client IP strings, and success flags for throttling. The application counts failed attempts from an IP address in the previous 15 minutes and blocks further login attempts after eight failures in that window.

## Money representation

The web app stores money as integer paise to avoid binary floating-point rounding in transaction calculations. For example, ₹10.50 is stored as 1050. User input is parsed and rounded only after checking that it has at most two decimal places.

The historical CSV analysis program uses the unit_price values from the CSV and Python floating-point aggregation; it is not the operational accounting ledger.

## Time handling

The web app uses TAPRI_TIMEZONE, defaulting to Asia/Kolkata, for timestamps and the dashboard's definition of today. Stored timestamps include the timezone offset. The login-attempt table uses UTC-naive ISO timestamps for its short throttling window.

## Persistence and concurrency

SQLite is appropriate for a small single-owner/local workflow. Connections are opened per request, foreign-key enforcement is enabled, and a busy timeout is configured. The database file must be on persistent writable storage. A deployment platform with ephemeral filesystems can lose data on restart unless storage is configured.

## Design boundaries

The current app does not implement customer accounts, employee roles, inventory stock, automatic bank reconciliation, external payment APIs, CSV exports, editing/deleting transactions, or multi-device cloud synchronization. Do not infer these capabilities from the existence of payment-method fields.
