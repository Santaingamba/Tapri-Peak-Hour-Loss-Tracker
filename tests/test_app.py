import unittest
from pathlib import Path
from app import analyse, load_rows, render_report

ROOT = Path(__file__).resolve().parents[1]

class TrackerTests(unittest.TestCase):
    def test_default_csv_contains_twenty_observation_entries(self):
        rows = load_rows(ROOT / "data.csv")
        self.assertEqual(len(rows), 20)
        self.assertTrue(all(r["origin"] == "NIT Silchar Tapri — Rupam Das" for r in rows))

    def test_confirmed_and_pending_values_are_separate(self):
        result = analyse(load_rows(ROOT / "data.csv"))
        self.assertEqual(result["verified_rows"], 5)
        self.assertEqual(result["follow_up_rows"], 2)
        self.assertEqual(result["potential_value"], 95.0)
        self.assertEqual(result["follow_up_value"], 10.0)
        self.assertEqual(result["verified_units"], 5)

    def test_report_displays_both_totals(self):
        report = render_report(analyse(load_rows(ROOT / "data.csv")))
        self.assertIn("FIELD LOG SUMMARY", report)
        self.assertIn("Rs 95.00", report)
        self.assertIn("Rs 10.00", report)

    def test_rejects_invalid_crowd_level(self):
        content = (ROOT / "data.csv").read_text(encoding="utf-8")
        content = content.replace(",low,", ",packed,", 1)
        import tempfile
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False) as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        try:
            with self.assertRaisesRegex(ValueError, "crowd_level"): load_rows(temp_path)
        finally: temp_path.unlink(missing_ok=True)

    def test_rejects_invalid_quantity_bounds(self):
        content = (ROOT / "data.csv").read_text(encoding="utf-8")
        content = content.replace(",2,2,low,", ",2,3,low,", 1)
        import tempfile
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False) as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        try:
            with self.assertRaisesRegex(ValueError, "quantity"): load_rows(temp_path)
        finally: temp_path.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()
