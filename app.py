#!/usr/bin/env python3
"""Analyse item handovers from a tapri observation CSV (standard library only)."""
from __future__ import annotations
import argparse
import csv
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = {"timestamp", "item", "unit_price", "qty_handed_over", "qty_paid_for", "crowd_level", "observation_note", "verification_status", "data_origin"}
VALID_CROWD = {"low", "medium", "high"}
VALID_STATUS = {"paid", "observed_unpaid", "needs_follow_up"}

def time_window(timestamp: datetime) -> str:
    hour = timestamp.hour
    if hour < 10: return "Before 10:00"
    if hour < 12: return "10:00–11:59"
    if hour < 14: return "12:00–13:59"
    if hour < 16: return "14:00–15:59"
    if hour < 18: return "16:00–17:59"
    return "18:00 onward"

def load_rows(path: Path) -> list[dict]:
    """Read and validate the observation CSV."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing: raise ValueError("Missing CSV columns: " + ", ".join(sorted(missing)))
        rows = []
        for line_no, raw in enumerate(reader, start=2):
            if None in raw:
                raise ValueError(f"Row {line_no}: unexpected extra CSV fields")
            if not any((value or "").strip() for value in raw.values()): continue
            try:
                stamp = datetime.strptime((raw.get("timestamp") or "").strip(), "%Y-%m-%d %H:%M")
                price = float(raw.get("unit_price", ""))
                handed = int(raw.get("qty_handed_over", ""))
                paid = int(raw.get("qty_paid_for", ""))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Row {line_no}: invalid timestamp, price, or quantity: {exc}") from exc
            item = (raw.get("item") or "").strip()
            crowd = (raw.get("crowd_level") or "").strip().lower()
            status = (raw.get("verification_status") or "").strip().lower()
            origin = (raw.get("data_origin") or "").strip()
            if not item or not origin: raise ValueError(f"Row {line_no}: item and data_origin are required")
            if not math.isfinite(price) or price <= 0 or handed < 1 or paid < 0 or paid > handed:
                raise ValueError(f"Row {line_no}: invalid price or quantity bounds")
            if crowd not in VALID_CROWD: raise ValueError(f"Row {line_no}: crowd_level must be low, medium, or high")
            if status not in VALID_STATUS: raise ValueError(f"Row {line_no}: invalid verification_status")
            if status == "paid" and paid != handed: raise ValueError(f"Row {line_no}: paid rows must have all units paid")
            if status == "observed_unpaid" and paid == handed: raise ValueError(f"Row {line_no}: observed_unpaid needs at least one unpaid unit")
            if status == "needs_follow_up" and paid == handed: raise ValueError(f"Row {line_no}: use paid when all handed-over units were paid")
            rows.append({"timestamp": stamp, "item": item, "price": price, "handed": handed, "paid": paid,
                         "crowd": crowd, "note": (raw.get("observation_note") or "").strip(), "status": status,
                         "window": time_window(stamp), "origin": origin})
    return rows

def analyse(rows: list[dict]) -> dict:
    verified = [r for r in rows if r["status"] == "observed_unpaid"]
    follow_up = [r for r in rows if r["status"] == "needs_follow_up"]
    item_totals, window_totals = defaultdict(float), defaultdict(float)
    def value(row): return (row["handed"] - row["paid"]) * row["price"]
    for row in verified:
        item_totals[row["item"]] += value(row)
        window_totals[row["window"]] += value(row)
    return {"rows": len(rows), "verified_rows": len(verified), "follow_up_rows": len(follow_up),
            "potential_value": sum(item_totals.values()), "follow_up_value": sum(value(r) for r in follow_up),
            "item_totals": dict(item_totals), "window_totals": dict(window_totals),
            "verified_units": sum(r["handed"] - r["paid"] for r in verified),
            "handed_units": sum(r["handed"] for r in rows), "paid_units": sum(r["paid"] for r in rows)}

def render_report(summary: dict) -> str:
    lines = ["=" * 66, "TAPRI PEAK-HOUR LOSS TRACKER", "FIELD LOG SUMMARY", "=" * 66,
             f"Rows analysed: {summary['rows']}", f"Units handed over: {summary['handed_units']}",
             f"Units paid for: {summary['paid_units']}", f"Directly observed unpaid handovers: {summary['verified_rows']}",
             f"Uncertain entries excluded: {summary['follow_up_rows']}", f"Units in observed unpaid handovers: {summary['verified_units']}",
             f"Potential uncollected value: Rs {summary['potential_value']:.2f}",
             f"Value pending follow-up (excluded): Rs {summary['follow_up_value']:.2f}", "", "POTENTIAL VALUE BY TIME WINDOW"]
    for key, amount in sorted(summary["window_totals"].items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"  {key:<20} Rs {amount:>7.2f}")
    if not summary["window_totals"]: lines.append("  No directly observed unpaid handovers recorded.")
    lines += ["", "POTENTIAL VALUE BY ITEM"]
    for key, amount in sorted(summary["item_totals"].items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"  {key:<20} Rs {amount:>7.2f}")
    if not summary["item_totals"]: lines.append("  No observed unpaid value to aggregate.")
    lines += ["", "INTERPRETATION", "- Only rows marked observed_unpaid contribute to potential value.",
              "- needs_follow_up rows are excluded until payment status is checked.",
              "- This calculation does not establish intent or prove theft.",
              "- Do not extrapolate this short sample into daily or monthly losses.", "=" * 66]
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser(description="Summarise item handovers and possible unpaid value.")
    parser.add_argument("--data", default="data.csv", help="CSV path (default: data.csv)")
    args = parser.parse_args()
    path = Path(args.data)
    if not path.is_absolute(): path = ROOT / path
    try: rows = load_rows(path)
    except (OSError, ValueError) as exc:
        print(f"Input error: {exc}")
        return 2
    if not rows:
        print("No observation rows found. Add observation entries to data.csv.")
        return 0
    print(render_report(analyse(rows)))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
