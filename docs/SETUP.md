# Setup and deployment

This guide covers local installation of the Flask tracker, configuration, and safe access from a phone. The historical CSV analysis program is described separately in ANALYSIS.md.

## Requirements

- Python 3.10 or newer.
- pip.
- A modern browser.
- A writable location for the SQLite database.
- Flask, installed from requirements.txt.

The web application uses Python's built-in SQLite driver. It does not require a separate database server.

## Install

    git clone https://github.com/Santaingamba/Tapri-Peak-Hour-Loss-Tracker.git
    cd Tapri-Peak-Hour-Loss-Tracker
    python -m venv .venv

Activate the virtual environment.

Windows PowerShell:

    .\.venv\Scripts\Activate.ps1

macOS / Linux:

    source .venv/bin/activate

Install the project dependency:

    python -m pip install --upgrade pip
    pip install -r requirements.txt

## Configure required secrets

Generate a cryptographically random session secret:

    python -c "import secrets; print(secrets.token_urlsafe(48))"

Set the generated value as TAPRI_SECRET_KEY and choose a private sign-in password as TAPRI_ADMIN_PIN.

Windows PowerShell:

    $env:TAPRI_SECRET_KEY = "your-generated-secret"
    $env:TAPRI_ADMIN_PIN = "your-private-password"

macOS / Linux:

    export TAPRI_SECRET_KEY='your-generated-secret'
    export TAPRI_ADMIN_PIN='your-private-password'

Both values must be present before importing or starting web_app.py. The secret must contain at least 32 characters; the password must contain at least eight. Never put actual values in source control, screenshots, issue reports, or shared documentation.

The variable name TAPRI_ADMIN_PIN is historical. Despite its name, it is a password/passphrase and does not have to be numeric.

## Start locally

    python web_app.py

Browse to http://127.0.0.1:5000. The application creates tapri.sqlite3 automatically on first startup. Keep the terminal open while using the app.

The default bind address is 127.0.0.1, which makes the server available only from the same computer.

## Use from a phone on the same trusted Wi-Fi

This is suitable only for a trusted private local network.

1. Connect the computer running the app and the phone to the same private Wi-Fi.
2. Find the computer's LAN IP address using the operating system's network settings.
3. Stop the app if it is running.
4. Set TAPRI_HOST to 0.0.0.0 in the same terminal.
5. Start the app again with python web_app.py.
6. On the phone, open http://COMPUTER-LAN-IP:5000, replacing the placeholder with the computer's actual LAN IP.

Binding to 0.0.0.0 makes the app listen on all network interfaces. It does not provide encryption. Use only on a trusted network, keep the machine firewall enabled, and do not forward the port from a router or expose it to the public internet. The development server is not intended for public production hosting.

## Environment variables

| Variable | Required | Default | Meaning |
|---|---:|---|---|
| TAPRI_SECRET_KEY | Yes | None | Random Flask session-signing secret, at least 32 characters |
| TAPRI_ADMIN_PIN | Yes | None | Owner sign-in password, at least 8 characters |
| TAPRI_DB_PATH | No | Repository directory/tapri.sqlite3 | Path to SQLite database |
| TAPRI_TIMEZONE | No | Asia/Kolkata | IANA timezone used for dashboard date and timestamps |
| TAPRI_HOST | No | 127.0.0.1 | Network interface to bind |
| PORT | No | 5000 | TCP port |
| TAPRI_HTTPS | No | 0 | Set to 1 only when the app is served through HTTPS |

The .env.example file documents the variable names but is not automatically loaded by the app. Export variables in the shell or configure them in the deployment platform's secret manager.

## Database location and backups

The live operational records are stored in a SQLite file. By default this is tapri.sqlite3 in the repository directory. For a persistent deployment, set TAPRI_DB_PATH to a stable writable location outside the application release directory.

Back up the database regularly. For a consistent backup while the app is active, use SQLite's backup API or stop the app before copying the database. Store backups in a private location with restricted access. Periodically test that a backup can be restored.

The app does not encrypt the SQLite file. Protect the host account, file permissions, backup location, and any device that can access it.

## Public deployment checklist

Do not deploy the Flask development server directly to the public internet. A public deployment requires additional operational work:

- Use a production WSGI server, such as Gunicorn on supported Linux hosting.
- Put the WSGI server behind a correctly configured HTTPS reverse proxy or managed platform ingress.
- Set TAPRI_HTTPS=1 only when HTTPS is actually enforced end-to-end at the trusted proxy boundary.
- Configure the platform to preserve the SQLite file across restarts and redeployments, or migrate to a managed database with appropriate backups.
- Keep secrets in the hosting provider's secret manager.
- Restrict database and backup access.
- Configure host firewall and platform access controls.
- Review trusted proxy configuration before relying on client IP addresses for rate limiting.
- Run the test suite after deployment and perform a real-device smoke test.
- Establish a backup and restore procedure.

The repository does not currently include a production deployment manifest or a hosted public URL. Do not assume that pushing to GitHub deploys the application.

## Troubleshooting

**Application refuses to start:** Check that TAPRI_SECRET_KEY and TAPRI_ADMIN_PIN are set in the terminal that starts Python and meet their minimum lengths.

**Address already in use:** Another process may be using port 5000. Stop it or choose another PORT.

**Phone cannot connect:** Confirm both devices are on the same trusted Wi-Fi, use the computer's current LAN IP, set TAPRI_HOST=0.0.0.0, and check the computer firewall.

**Data appears missing:** Confirm TAPRI_DB_PATH and the process working environment. The app may be opening a different SQLite file if the path changed.

**Menu suggestions are missing:** Check that products.csv is beside web_app.py and retains its item and unit_price_inr header columns.

**Timezone error:** Set TAPRI_TIMEZONE to a valid IANA timezone such as Asia/Kolkata.
