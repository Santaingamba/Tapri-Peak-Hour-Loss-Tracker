import unittest
from pathlib import Path
from app import analyse, load_rows, render_report

ROOT = Path(__file__).resolve().parents[1]


class TrackerTests(unittest.TestCase):
    def test_default_csv_is_explicitly_simulated(self):
        rows, simulated = load_rows(ROOT / "data.csv")
        self.assertTrue(simulated)
        self.assertEqual(len(rows), 24)

    def test_only_verified_unpaid_rows_contribute(self):
        rows, simulated = load_rows(ROOT / "data.csv")
        result = analyse(rows)
        self.assertTrue(simulated)
        self.assertEqual(result["verified_rows"], 8)
        self.assertEqual(result["follow_up_rows"], 2)
        self.assertEqual(result["potential_value"], 130.0)

    def test_simulation_warning_is_prominent(self):
        rows, simulated = load_rows(ROOT / "data.csv")
        report = render_report(analyse(rows), simulated)
        self.assertIn("SIMULATED DEMO — NOT FIELD EVIDENCE", report)
        self.assertIn("Rs 130.00", report)

    def test_rejects_invalid_crowd_level(self):
        content = (ROOT / "data.csv").read_text(encoding="utf-8")
        content = content.replace(",low,", ",packed,")
        import tempfile
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False) as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        try:
            with self.assertRaisesRegex(ValueError, "crowd_level"):
                load_rows(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_rejects_mixed_provenance(self):
        content = (ROOT / "data.csv").read_text(encoding="utf-8")
        content = content.replace("SIMULATED_NOT_FIELD_DATA", "FIELD_OBSERVATION", 1)
        import tempfile
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False) as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        try:
            with self.assertRaisesRegex(ValueError, "mix simulated"):
                load_rows(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
