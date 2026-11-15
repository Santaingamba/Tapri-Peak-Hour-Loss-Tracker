import os
import tempfile
import unittest
from pathlib import Path

_TMP = tempfile.TemporaryDirectory()
os.environ["TAPRI_SECRET_KEY"] = "test-secret-key-with-more-than-32-characters"
os.environ["TAPRI_ADMIN_PIN"] = "test-password-123"
os.environ["TAPRI_DB_PATH"] = str(Path(_TMP.name) / "test.sqlite3")

import web_app


class TrackerWebTests(unittest.TestCase):
    def setUp(self):
        web_app.app.config.update(TESTING=True)
        with web_app.connect() as db:
            db.execute("DELETE FROM recoveries")
            db.execute("DELETE FROM orders")
            db.execute("DELETE FROM attempts")
        self.client = web_app.app.test_client()

    def token(self):
        with self.client.session_transaction() as session:
            return session["csrf"]

    def login(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        return self.client.post(
            "/login",
            data={"csrf": self.token(), "password": "test-password-123"},
            follow_redirects=True,
        )

    def create_order(self, **overrides):
        data = {
            "csrf": self.token(), "item": "Tea", "price": "10.00",
            "served": "3", "paid": "2", "method": "upi", "crowd": "high",
            "note": "",
        }
        data.update(overrides)
        return self.client.post("/orders", data=data)

    def test_private_pages_require_authentication(self):
        for path in ("/", "/history", "/orders/1"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 302)

    def test_order_and_partial_then_full_recovery(self):
        self.assertEqual(self.login().status_code, 200)
        response = self.create_order()
        self.assertEqual(response.status_code, 302)
        order_id = int(response.location.rsplit("/", 1)[1])
        detail = self.client.get(f"/orders/{order_id}").get_data(as_text=True)
        self.assertIn("₹10", detail)

        partial = self.client.post(
            f"/orders/{order_id}/recover",
            data={"csrf": self.token(), "amount": "4.25", "method": "cash", "note": "Partial"},
        )
        self.assertEqual(partial.status_code, 302)
        detail = self.client.get(f"/orders/{order_id}").get_data(as_text=True)
        self.assertIn("₹4.25", detail)
        self.assertIn("₹5.75", detail)

        final = self.client.post(
            f"/orders/{order_id}/recover",
            data={"csrf": self.token(), "amount": "5.75", "method": "upi", "note": "Balance"},
        )
        self.assertEqual(final.status_code, 302)
        detail = self.client.get(f"/orders/{order_id}").get_data(as_text=True)
        self.assertIn("₹0", detail)
        self.assertIn("Settled", self.client.get("/").get_data(as_text=True))

    def test_recovery_cannot_exceed_balance_or_be_zero(self):
        self.login()
        response = self.create_order(served="2", paid="1")
        order_id = int(response.location.rsplit("/", 1)[1])
        for amount in ("10.01", "0", "-1"):
            with self.subTest(amount=amount):
                result = self.client.post(
                    f"/orders/{order_id}/recover",
                    data={"csrf": self.token(), "amount": amount, "method": "upi"},
                    follow_redirects=True,
                )
                self.assertIn("flash error", result.get_data(as_text=True))
        with web_app.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM recoveries").fetchone()[0], 0)

    def test_invalid_orders_are_not_persisted(self):
        self.login()
        invalid = [
            {"served": "1", "paid": "2"},
            {"served": "0", "paid": "0"},
            {"served": "2", "paid": "-1"},
            {"price": "nan"},
            {"price": "inf"},
            {"price": "0"},
            {"price": "1.001"},
            {"method": "bitcoin"},
            {"crowd": "packed"},
            {"item": ""},
            {"item": "x" * 61},
        ]
        for values in invalid:
            with self.subTest(values=values):
                self.create_order(**values)
        with web_app.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 0)

    def test_invalid_payment_method_and_note_length_on_recovery(self):
        self.login()
        response = self.create_order()
        order_id = int(response.location.rsplit("/", 1)[1])
        for values in ({"method": "crypto"}, {"note": "x" * 241}):
            result = self.client.post(
                f"/orders/{order_id}/recover",
                data={"csrf": self.token(), "amount": "1", **values},
                follow_redirects=True,
            )
            self.assertIn("error", result.get_data(as_text=True).lower())
        with web_app.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM recoveries").fetchone()[0], 0)

    def test_csrf_is_required_for_every_state_changing_route(self):
        self.login()
        response = self.client.post("/orders", data={"item": "Tea"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.post("/logout").status_code, 400)

    def test_login_throttles_after_eight_failed_attempts(self):
        self.client.get("/login")
        for _ in range(8):
            response = self.client.post(
                "/login", data={"csrf": self.token(), "password": "wrong-password"},
            )
            self.assertEqual(response.status_code, 200)
        blocked = self.client.post(
            "/login", data={"csrf": self.token(), "password": "test-password-123"},
        )
        self.assertEqual(blocked.status_code, 429)

    def test_successful_login_rotates_csrf_token(self):
        self.client.get("/login")
        old_token = self.token()
        response = self.client.post(
            "/login", data={"csrf": old_token, "password": "test-password-123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(self.token(), old_token)

    def test_owner_can_confirm_and_unconfirm_discrepancy(self):
        self.login()
        response = self.create_order()
        order_id = int(response.location.rsplit("/", 1)[1])
        for expected in ("Remove confirmed status", "Confirm still unpaid"):
            response = self.client.post(
                f"/orders/{order_id}/confirm", data={"csrf": self.token()},
            )
            self.assertEqual(response.status_code, 302)
            self.assertIn(expected, self.client.get(f"/orders/{order_id}").get_data(as_text=True))

    def test_xss_payload_is_escaped_in_order_detail(self):
        self.login()
        payload = '<script>alert("x")</script>'
        response = self.create_order(item=payload)
        order_id = int(response.location.rsplit("/", 1)[1])
        html = self.client.get(f"/orders/{order_id}").get_data(as_text=True)
        self.assertNotIn(payload, html)
        self.assertIn("&lt;script&gt;", html)

    def test_history_date_validation_and_filter(self):
        self.login()
        self.create_order()
        self.assertEqual(self.client.get("/history?day=not-a-date").status_code, 400)
        self.assertEqual(self.client.get("/history?day=2026-11-14").status_code, 200)

    def test_missing_order_returns_404_without_leaking_details(self):
        self.login()
        response = self.client.get("/orders/999999")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("Traceback", response.get_data(as_text=True))

    def test_security_headers_and_session_cookie_flags(self):
        response = self.client.get("/login")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        self.assertIn("HttpOnly", response.headers.get("Set-Cookie", ""))
        self.assertIn("SameSite=Lax", response.headers.get("Set-Cookie", ""))

    def test_logout_removes_access(self):
        self.login()
        self.assertEqual(self.client.post("/logout", data={"csrf": self.token()}).status_code, 302)
        self.assertEqual(self.client.get("/").status_code, 302)

    def test_health_endpoint_does_not_require_login(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
