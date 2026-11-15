# Security and privacy notes

## Intended deployment boundary

The current web app is a small single-owner operational tool. Its safest initial use is on the same computer or on a trusted private local Wi-Fi network. It is not ready to be exposed directly to the public internet using Flask's built-in development server.

## Implemented controls

- **Owner authentication:** the configured password is hashed with Werkzeug's scrypt password-hashing method and the hash is stored in SQLite.
- **Required session secret:** startup fails unless TAPRI_SECRET_KEY is provided and is at least 32 characters long.
- **Session cookie flags:** HTTP-only and SameSite=Lax are enabled; Secure can be enabled with TAPRI_HTTPS=1.
- **Session rotation:** the session is cleared and a fresh CSRF token is created after successful sign-in.
- **CSRF protection:** every POST route requires a token stored in the session and submitted in the form.
- **Login throttling:** after eight failed attempts from an IP address in a rolling 15-minute window, further attempts are blocked for that window.
- **SQL parameterization:** user-provided values are passed as SQL parameters rather than interpolated into SQL statements.
- **Database constraints:** positive prices and quantities, allowed payment methods, allowed crowd values, and foreign-key relationships are enforced.
- **Input validation:** item names, notes, prices, quantities, dates, payment methods, and crowd levels are bounded or checked.
- **Money arithmetic:** the web application stores transaction amounts as integer paise.
- **Recovery transaction:** recovery balance is checked within a SQLite write transaction before the recovery is inserted.
- **Template escaping:** user-entered values are rendered through Jinja auto-escaping.
- **Response headers:** the app sets anti-sniffing, frame, referrer, permissions, and content-security policy headers.
- **Request size:** Flask's maximum request body size is limited.
- **Debug disabled:** the application entry point runs with debug=False.

## Operational responsibilities

These controls do not replace secure deployment practices.

- Keep secrets out of source control and shared files.
- Use a strong, unique owner password.
- Protect the machine account and restrict access to the SQLite file.
- Keep the database and backups in private storage.
- Use HTTPS for remote access and set TAPRI_HTTPS=1 only when HTTPS is actually enforced.
- Use a production WSGI server and a correctly configured reverse proxy for public hosting.
- Configure persistent storage and test backup restoration.
- Keep Python and dependencies updated.
- Restrict network access and avoid public port forwarding.
- Do not store customer identity or sensitive payment information in notes.

## Known limitations and residual risks

- The app does not encrypt the SQLite database or backups.
- There are no separate user accounts, staff roles, or audit identity per operator.
- The login throttling is based on the request's remote address. Reverse-proxy deployments require careful proxy configuration; blindly trusting forwarded IP headers would be unsafe.
- The app has no password reset or in-app password-change workflow. Changing the configured environment password after the database has been initialized does not automatically replace the password hash already stored in settings.
- The application does not provide automatic payment verification, tamper-evident audit logs, transaction editing history, or multi-factor authentication.
- A successful test suite is not a security audit.
- Public deployment requires independent review of the hosting setup, TLS termination, proxy behavior, storage, backups, and access policy.

## If credentials are exposed

1. Stop the service if necessary.
2. Generate a new TAPRI_SECRET_KEY and update the deployment secret.
3. Treat the owner password as compromised and restrict access until a password rotation procedure is completed.
4. Review access to the database and backups.
5. Do not paste the exposed secret into an issue or commit.
6. If the session secret changes, existing signed sessions will no longer validate.

## Privacy principles

Record only operational information needed to reconcile an order. Do not record customer names, phone numbers, account numbers, photographs of customers, or other identifying details. An unpaid flag must never be used to publicly accuse or identify a person.
