#!/usr/bin/env python3
"""Analyse item handovers from a tapri observation CSV (standard library only)."""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = {
    "timestamp", "item", "unit_price", "qty_handed_over", "qty_paid_for",
    "crowd_level", "observation_note", "verification_status", "data_origin",
}
VALID_CROWD = {"low", "medium", "high"}
VALID_STATUS = {"paid", "observed_unpaid", "needs_follow_up"}
SIMULATED = "SIMULATED_NOT_FIELD_DATA"
FIELD = "FIELD_OBSERVATION"


def time_window(timestamp: datetime) -> str:
    hour = timestamp.hour
    if hour < 10:
        return "Before 10:00"
    if hour < 12:
        return "10:00–11:59"
    if hour < 14:
        return "12:00–13:59"
    if hour < 16:
        return "14:00–15:59"
    if hour < 18:
        return "16:00–17:59"
    return "18:00 onward"


def load_rows(path: Path) -> tuple[list[dict], bool]:
    """Return validated rows and whether every row is explicitly simulated."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError("Missing CSV columns: " + ", ".join(sorted(missing)))
        rows = []
        origins = set()
        for line_no, raw in enumerate(reader, start=2):
            if not any((value or "").strip() for value in raw.values()):
                continue
            try:
                stamp_text = raw["timestamp"].strip()
                stamp = datetime.strptime(stamp_text, "%Y-%m-%d %H:%M")
                price = float(raw["unit_price"])
                handed = int(raw["qty_handed_over"])
                paid = int(raw["qty_paid_for"])
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Row {line_no}: invalid timestamp, price, or quantity: {exc}") from exc

            item = raw["item"].strip()
            crowd = raw["crowd_level"].strip().lower()
            status = raw["verification_status"].strip().lower()
            origin = raw["data_origin"].strip().upper()
            if not item:
                raise ValueError(f"Row {line_no}: item is required")
            if price <= 0 or handed < 1 or paid < 0 or paid > handed:
                raise ValueError(f"Row {line_no}: invalid price or quantity bounds")
            if crowd not in VALID_CROWD:
                raise ValueError(f"Row {line_no}: crowd_level must be low, medium, or high")
            if status not in VALID_STATUS:
                raise ValueError(f"Row {line_no}: invalid verification_status")
            if status == "paid" and paid != handed:
                raise ValueError(f"Row {line_no}: paid rows must have all units paid")
            if status == "observed_unpaid" and paid == handed:
                raise ValueError(f"Row {line_no}: observed_unpaid needs at least one unpaid unit")
            if status == "needs_follow_up" and paid == handed:
                # A fully paid transaction should be marked paid, not uncertain.
                raise ValueError(f"Row {line_no}: use paid when all handed-over units were paid")
            if origin not in {FIELD, SIMULATED}:
                raise ValueError(f"Row {line_no}: data_origin must be {FIELD} or {SIMULATED}")
            origins.add(origin)
            rows.append({
                "timestamp": stamp, "item": item, "price": price,
                "handed": handed, "paid": paid, "crowd": crowd,
                "note": raw["observation_note"].strip(), "status": status,
                "window": time_window(stamp), "origin": origin,
            })

    if len(origins) > 1:
        raise ValueError("Do not mix simulated and field-observed rows in one CSV.")
    return rows, origins == {SIMULATED}


def analyse(rows: list[dict]) -> dict:
    verified = [r for r in rows if r["status"] == "observed_unpaid"]
    follow_up = [r for r in rows if r["status"] == "needs_follow_up"]
    item_totals = defaultdict(float)
    window_totals = defaultdict(float)
    crowd_totals = defaultdict(float)
    for row in verified:
        amount = (row["handed"] - row["paid"]) * row["price"]
        item_totals[row["item"]] += amount
        window_totals[row["window"]] += amount
        crowd_totals[row["crowd"]] += amount
    return {
        "rows": len(rows),
        "verified_rows": len(verified),
        "follow_up_rows": len(follow_up),
        "potential_value": sum(item_totals.values()),
        "item_totals": dict(item_totals),
        "window_totals": dict(window_totals),
        "crowd_totals": dict(crowd_totals),
        "verified_units": sum(r["handed"] - r["paid"] for r in verified),
    }


def render_report(summary: dict, simulated: bool) -> str:
    label = "SIMULATED DEMO — NOT FIELD EVIDENCE" if simulated else "FIELD LOG SUMMARY"
    lines = [
        "=" * 66, "TAPRI PEAK-HOUR LOSS TRACKER", label, "=" * 66,
        f"Rows analysed: {summary['rows']}",
        f"Directly observed unpaid handovers: {summary['verified_rows']}",
        f"Uncertain entries excluded: {summary['follow_up_rows']}",
        f"Units in unpaid handovers: {summary['verified_units']}",
        f"Potential uncollected value: Rs {summary['potential_value']:.2f}",
        "", "POTENTIAL VALUE BY TIME WINDOW",
    ]
    for key, value in sorted(summary["window_totals"].items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"  {key:<20} Rs {value:>7.2f}")
    if not summary["window_totals"]:
        lines.append("  No directly observed unpaid handovers recorded.")
    lines += ["", "POTENTIAL VALUE BY ITEM"]
    for key, value in sorted(summary["item_totals"].items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"  {key:<20} Rs {value:>7.2f}")
    if not summary["item_totals"]:
        lines.append("  No verified value to aggregate.")
    if summary["rows"] < 20:
        lines += ["", f"DATA WARNING: {summary['rows']} rows loaded; the assignment asks for at least 20 real entries."]
    lines += [
        "", "INTERPRETATION",
        "- Only rows marked observed_unpaid contribute to the estimate.",
        "- needs_follow_up rows are excluded until payment status is checked.",
        "- This calculation does not establish intent or prove theft.",
        "- Do not extrapolate this short sample into daily or monthly losses.",
        "=" * 66,
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarise item handovers and possible unpaid value.")
    parser.add_argument("--data", default="data.csv", help="CSV path (default: data.csv)")
    args = parser.parse_args()
    path = Path(args.data)
    if not path.is_absolute():
        path = ROOT / path
    try:
        rows, simulated = load_rows(path)
    except (OSError, ValueError) as exc:
        print(f"Input error: {exc}")
        return 2
    if not rows:
        print("No observation rows found. Add genuine observations to data.csv.")
        return 0
    print(render_report(analyse(rows), simulated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
