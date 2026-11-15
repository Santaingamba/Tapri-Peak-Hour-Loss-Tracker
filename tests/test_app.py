import csv
import math
import random
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from app import REQUIRED, analyse, load_rows, render_report, time_window

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["timestamp", "item", "unit_price", "qty_handed_over", "qty_paid_for",
          "crowd_level", "observation_note", "verification_status", "data_origin"]


def write_csv(rows, header=FIELDS):
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False)
    writer = csv.DictWriter(handle, fieldnames=header)
    writer.writeheader()
    writer.writerows(rows)
    handle.close()
    return Path(handle.name)


def row(**changes):
    result = {
        "timestamp": "2026-11-14 12:00", "item": "Tea", "unit_price": "10",
        "qty_handed_over": "2", "qty_paid_for": "1", "crowd_level": "medium",
        "observation_note": "Observed at counter", "verification_status": "observed_unpaid",
        "data_origin": "Test fixture",
    }
    result.update(changes)
    return result


class TimeWindowTests(unittest.TestCase):
    def test_all_window_boundaries(self):
        cases = {
            0: "Before 10:00", 9: "Before 10:00",
            10: "10:00–11:59", 11: "10:00–11:59",
            12: "12:00–13:59", 13: "12:00–13:59",
            14: "14:00–15:59", 15: "14:00–15:59",
            16: "16:00–17:59", 17: "16:00–17:59",
            18: "18:00 onward", 23: "18:00 onward",
        }
        for hour, expected in cases.items():
            with self.subTest(hour=hour):
                self.assertEqual(time_window(datetime(2026, 1, 1, hour)), expected)


class CsvValidationTests(unittest.TestCase):
    def test_required_columns_are_enforced(self):
        path = write_csv([row()], header=FIELDS[:-1])
        try:
            with self.assertRaisesRegex(ValueError, "Missing CSV columns"):
                load_rows(path)
        finally:
            path.unlink()

    def test_rejects_non_finite_and_non_positive_prices(self):
        for price in ("nan", "inf", "-inf", "0", "-1"):
            path = write_csv([row(unit_price=price)])
            try:
                with self.subTest(price=price), self.assertRaises(ValueError):
                    load_rows(path)
            finally:
                path.unlink()

    def test_rejects_invalid_timestamps_and_quantities(self):
        bad_rows = [
            row(timestamp="14/11/2026 12:00"),
            row(qty_handed_over="0"),
            row(qty_handed_over="-1"),
            row(qty_paid_for="-1"),
            row(qty_paid_for="3"),
            row(qty_paid_for="1.5"),
        ]
        for bad in bad_rows:
            path = write_csv([bad])
            try:
                with self.subTest(row=bad), self.assertRaises(ValueError):
                    load_rows(path)
            finally:
                path.unlink()

    def test_rejects_invalid_status_combinations(self):
        cases = [
            row(verification_status="paid", qty_paid_for="1"),
            row(verification_status="observed_unpaid", qty_paid_for="2"),
            row(verification_status="needs_follow_up", qty_paid_for="2"),
            row(verification_status="unknown"),
        ]
        for bad in cases:
            path = write_csv([bad])
            try:
                with self.subTest(row=bad), self.assertRaises(ValueError):
                    load_rows(path)
            finally:
                path.unlink()

    def test_rejects_extra_csv_fields(self):
        path = write_csv([row()])
        content = path.read_text(encoding="utf-8").replace("Test fixture\n", "Test fixture,unexpected\n")
        path.write_text(content, encoding="utf-8")
        try:
            with self.assertRaisesRegex(ValueError, "extra CSV fields"):
                load_rows(path)
        finally:
            path.unlink()

    def test_skips_blank_rows_and_accepts_utf8_bom(self):
        path = write_csv([row()])
        try:
            content = path.read_text(encoding="utf-8")
            path.write_text("\ufeff" + content + "\n,,,,,,,,\n", encoding="utf-8")
            self.assertEqual(len(load_rows(path)), 1)
        finally:
            path.unlink()

    def test_missing_item_and_source_are_rejected(self):
        for bad in (row(item=" "), row(data_origin=" ")):
            path = write_csv([bad])
            try:
                with self.subTest(row=bad), self.assertRaises(ValueError):
                    load_rows(path)
            finally:
                path.unlink()


class AnalysisInvariantTests(unittest.TestCase):
    def test_generated_dataset_invariants_and_independent_totals(self):
        rng = random.Random(82461)
        for _ in range(100):
            rows = []
            expected_unpaid = 0.0
            expected_follow_up = 0.0
            expected_unpaid_units = 0
            expected_handed = expected_paid = 0
            for index in range(rng.randint(1, 40)):
                handed = rng.randint(1, 20)
                paid = rng.randint(0, handed)
                price = rng.randint(1, 500) / 2
                if paid == handed:
                    status = "paid"
                else:
                    status = rng.choice(("observed_unpaid", "needs_follow_up"))
                r = {
                    "timestamp": datetime(2026, 11, 14, rng.randrange(24), rng.randrange(60)),
                    "item": f"item-{rng.randrange(5)}", "price": price,
                    "handed": handed, "paid": paid, "crowd": "medium",
                    "note": "", "status": status, "window": "derived",
                    "origin": "generated",
                }
                rows.append(r)
                amount = (handed - paid) * price
                if status == "observed_unpaid":
                    expected_unpaid += amount
                    expected_unpaid_units += handed - paid
                elif status == "needs_follow_up":
                    expected_follow_up += amount
                expected_handed += handed
                expected_paid += paid
            result = analyse(rows)
            self.assertAlmostEqual(result["potential_value"], expected_unpaid)
            self.assertAlmostEqual(result["follow_up_value"], expected_follow_up)
            self.assertEqual(result["verified_units"], expected_unpaid_units)
            self.assertEqual(result["handed_units"], expected_handed)
            self.assertEqual(result["paid_units"], expected_paid)
            self.assertEqual(result["rows"], len(rows))
            self.assertEqual(sum(result["item_totals"].values()), result["potential_value"])
            self.assertEqual(sum(result["window_totals"].values()), result["potential_value"])

    def test_only_observed_unpaid_rows_contribute_to_aggregates(self):
        rows = [
            {"timestamp": datetime(2026, 1, 1, 9), "item": "A", "price": 20,
             "handed": 2, "paid": 1, "status": "observed_unpaid", "window": "morning"},
            {"timestamp": datetime(2026, 1, 1, 10), "item": "B", "price": 99,
             "handed": 3, "paid": 1, "status": "needs_follow_up", "window": "later"},
        ]
        result = analyse(rows)
        self.assertEqual(result["potential_value"], 20)
        self.assertEqual(result["follow_up_value"], 198)
        self.assertEqual(result["item_totals"], {"A": 20})
        self.assertEqual(result["window_totals"], {"morning": 20})

    def test_empty_dataset_has_zero_totals_and_explanatory_report(self):
        result = analyse([])
        self.assertEqual(result["potential_value"], 0)
        self.assertEqual(result["follow_up_value"], 0)
        report = render_report(result)
        self.assertIn("No directly observed unpaid handovers recorded.", report)
        self.assertIn("No observed unpaid value to aggregate.", report)

    def test_recovered_observation_file_summary(self):
        rows = load_rows(ROOT / "data.csv")
        result = analyse(rows)
        self.assertEqual(len(rows), 20)
        self.assertEqual(result["verified_rows"], 5)
        self.assertEqual(result["follow_up_rows"], 2)
        self.assertEqual(result["potential_value"], 95)
        self.assertEqual(result["follow_up_value"], 10)
        self.assertEqual(result["verified_units"], 5)


if __name__ == "__main__":
    unittest.main()
