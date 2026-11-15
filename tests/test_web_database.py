import sqlite3
import unittest

import web_app


class DatabaseConstraintTests(unittest.TestCase):
    def setUp(self):
        with web_app.connect() as db:
            db.execute("DELETE FROM recoveries")
            db.execute("DELETE FROM orders")
            db.execute("DELETE FROM attempts")

    def insert_order(self, **overrides):
        values = {
            "created_at": "2026-01-01T10:00:00+05:30", "item": "Tea",
            "unit_price": 1000, "served": 2, "paid_qty": 1,
            "method": "cash", "crowd": "low", "note": "",
        }
        values.update(overrides)
        with web_app.connect() as db:
            return db.execute(
                """INSERT INTO orders(created_at,item,unit_price,served,paid_qty,method,crowd,note)
                   VALUES(:created_at,:item,:unit_price,:served,:paid_qty,:method,:crowd,:note)""",
                values,
            ).lastrowid

    def test_database_rejects_invalid_order_quantities_and_enums(self):
        invalid = [
            {"served": 0}, {"unit_price": 0}, {"paid_qty": -1},
            {"paid_qty": 3}, {"method": "crypto"}, {"crowd": "extreme"},
        ]
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(sqlite3.IntegrityError):
                self.insert_order(**values)

    def test_recovery_requires_existing_order(self):
        with web_app.connect() as db, self.assertRaises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO recoveries(order_id,amount,recovered_at,method,note) VALUES(?,?,?,?,?)",
                (987654321, 100, "2026-01-01T10:00:00+05:30", "cash", ""),
            )

    def test_database_accepts_valid_partial_recovery(self):
        order_id = self.insert_order()
        with web_app.connect() as db:
            db.execute(
                "INSERT INTO recoveries(order_id,amount,recovered_at,method,note) VALUES(?,?,?,?,?)",
                (order_id, 250, "2026-01-01T11:00:00+05:30", "upi", "Partial"),
            )
            self.assertEqual(
                db.execute("SELECT amount FROM recoveries WHERE order_id=?", (order_id,)).fetchone()[0],
                250,
            )

    def test_foreign_key_enforcement_is_enabled_per_connection(self):
        with web_app.connect() as db:
            self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
