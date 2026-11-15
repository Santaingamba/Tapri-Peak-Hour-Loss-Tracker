import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "app.py"


class CliIntegrationTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        )

    def test_default_command_emits_report(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("TAPRI PEAK-HOUR LOSS TRACKER", result.stdout)
        self.assertIn("INTERPRETATION", result.stdout)

    def test_custom_valid_csv_is_analysed(self):
        content = (
            "timestamp,item,unit_price,qty_handed_over,qty_paid_for,crowd_level,"
            "observation_note,verification_status,data_origin\n"
            "2026-01-02 09:15,Snack,12.50,3,1,medium,Checked,observed_unpaid,CLI test\n"
        )
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".csv", delete=False) as handle:
            handle.write(content)
            path = Path(handle.name)
        try:
            result = self.run_cli("--data", path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Rs 25.00", result.stdout)
        finally:
            path.unlink(missing_ok=True)

    def test_missing_file_returns_documented_error_code(self):
        result = self.run_cli("--data", ROOT / "file-that-does-not-exist.csv")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Input error:", result.stdout)

    def test_invalid_csv_returns_nonzero_without_traceback(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".csv", delete=False) as handle:
            handle.write("wrong,headers\n1,2\n")
            path = Path(handle.name)
        try:
            result = self.run_cli("--data", path)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Missing CSV columns", result.stdout)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
