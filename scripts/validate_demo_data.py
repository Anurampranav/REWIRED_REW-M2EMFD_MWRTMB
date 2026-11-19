"""Validate the synthetic T06 bank CSV and screenshot scenarios."""

from __future__ import annotations

import csv
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _load(name: str) -> dict[str, Any]:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def validate_demo_data() -> list[str]:
    """Return every fixture consistency error; an empty list means valid."""
    errors: list[str] = []
    try:
        demo = _load("demo_chit.json")
        scenario_doc = _load("scenarios.json")
        manifest = _load("screenshot_manifest.json")
        with (DATA / "bank.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
    except (OSError, json.JSONDecodeError, csv.Error) as exc:
        return [f"Could not read T06 fixture: {exc}"]

    group = demo["group"]
    members = demo["members"]
    member_ids = {member["id"] for member in members}
    due_date = date.fromisoformat(group["due_date"])
    expected_monthly = group["chit_value_paise"] // group["member_count"]
    if not demo.get("synthetic"):
        errors.append("demo_chit.json must be marked synthetic")
    if group["chit_value_paise"] != 10_000_000 or group["member_count"] != 20:
        errors.append("Demo chit must be ₹1,00,000 split across 20 members")
    if group["foreman_commission_percent"] != 5 or group["foreman_commission_paise"] != 500_000:
        errors.append("Demo foreman commission must equal 5% of the chit value")
    if group["base_instalment_paise"] != expected_monthly:
        errors.append("Base instalment must equal chit value divided by member count")
    if group["group_upi_id_is_routable"] or not group["group_upi_id"].endswith(".invalid"):
        errors.append("Demo group UPI ID must be a non-routable .invalid placeholder")
    if len(members) != 20 or len(member_ids) != 20:
        errors.append("Demo chit must contain exactly 20 uniquely identified members")

    utrs = [row.get("utr", "") for row in rows]
    if len(rows) != 20 or len(set(utrs)) != 20:
        errors.append("Bank CSV must have exactly 20 rows with unique UTRs")
    if any(not re.fullmatch(r"\d{12}", utr) for utr in utrs):
        errors.append("Every CSV UTR must contain exactly 12 digits")
    row_by_utr = {row.get("utr"): row for row in rows}
    row_member_ids = {row.get("payer_member_id") for row in rows}
    if row_member_ids != member_ids:
        errors.append("CSV must contain exactly one payment row for every demo member")
    for row in rows:
        if row.get("receiver_upi_id") != group["group_upi_id"]:
            errors.append(f"Unexpected receiver for UTR {row.get('utr')}")
        try:
            amount_paise = int(row.get("amount_paise", ""))
        except ValueError:
            amount_paise = -1
        if row.get("amount_tag") != "monthly_instalment" or amount_paise != expected_monthly:
            errors.append(f"Unexpected tagged amount for UTR {row.get('utr')}")
        if row.get("bank_status") != "SETTLED":
            errors.append(f"Bank row {row.get('utr')} must be settled")

    late_rows = [row for row in rows if date.fromisoformat(row["transaction_date"]) > due_date]
    if len(late_rows) != 1 or late_rows[0].get("scenario_tag") != "late_payer":
        errors.append("Exactly one CSV payment must be tagged as the late payer")

    scenarios = scenario_doc.get("scenarios", [])
    expected_ids = {"genuine_on_time", "reused_utr", "fake_utr_not_in_csv", "wrong_amount", "late_payer"}
    if {scenario.get("id") for scenario in scenarios} != expected_ids:
        errors.append("Scenario plan must contain the five required demo cases")
    fixture_ids = {item.get("id") for item in manifest.get("screenshots", [])}
    manifest_by_id = {item.get("id"): item for item in manifest.get("screenshots", [])}
    scenario_by_id = {scenario.get("id"): scenario for scenario in scenarios}
    if fixture_ids != {scenario.get("screenshot_fixture_id") for scenario in scenarios}:
        errors.append("Screenshot manifest IDs must match the scenario fixtures")
    if manifest.get("image_files_included") is not False:
        errors.append("Screenshot manifest must state that the synthetic images are not real uploads")

    for scenario_id, scenario in scenario_by_id.items():
        claim = scenario.get("claim", {})
        expected = scenario.get("expected_result", {})
        bubble = expected.get("bubble", {})
        screenshot = manifest_by_id.get(scenario.get("screenshot_fixture_id"), {})
        if scenario.get("screenshot_fixture_id") not in fixture_ids:
            errors.append(f"Scenario {scenario_id} has no screenshot fixture ID")
        if screenshot.get("expected_status") != bubble.get("status"):
            errors.append(f"Screenshot manifest status does not match scenario {scenario_id}")
        if scenario_id == "late_payer" and screenshot.get("timing") != "late":
            errors.append("Late payer screenshot manifest must mark timing as late")
        if not scenario_doc.get("synthetic"):
            errors.append("scenarios.json must be marked synthetic")
        if scenario_id == "genuine_on_time":
            row = row_by_utr.get(claim.get("utr"))
            if not row or row.get("scenario_tag") != "genuine_on_time" or bubble.get("status") != "verified" or not expected.get("ledger", {}).get("recorded"):
                errors.append("Genuine case must match CSV evidence and be recorded")
        elif scenario_id == "reused_utr":
            row = row_by_utr.get(claim.get("utr"))
            if not row or row.get("scenario_tag") != "reused_utr_source" or not scenario.get("precondition") or bubble.get("status") != "duplicate" or expected.get("ledger", {}).get("recorded"):
                errors.append("Reused UTR case must point to an existing payment and never post again")
        elif scenario_id == "fake_utr_not_in_csv":
            if claim.get("utr") in row_by_utr or bubble.get("utr") is not None or bubble.get("status") != "needs_review" or expected.get("ledger", {}).get("recorded"):
                errors.append("Fake UTR must be absent from CSV, return needs_review, and not post")
        elif scenario_id == "wrong_amount":
            row = row_by_utr.get(claim.get("utr"))
            evidence_amount = int(row["amount_paise"]) if row and row["amount_paise"].isdigit() else None
            if not row or evidence_amount is None or evidence_amount == claim.get("amount_paise") or row.get("scenario_tag") != "wrong_amount_source" or bubble.get("status") != "wrong_amount" or expected.get("ledger", {}).get("recorded"):
                errors.append("Wrong amount case must disagree with CSV evidence and never post")
        elif scenario_id == "late_payer":
            row = row_by_utr.get(claim.get("utr"))
            ledger = expected.get("ledger", {})
            if not row or row.get("scenario_tag") != "late_payer" or date.fromisoformat(row["transaction_date"]) <= due_date or bubble.get("status") != "verified" or not ledger.get("recorded") or ledger.get("timing") != "late" or ledger.get("status") != "overdue" or ledger.get("late_fee_paise") is not None:
                errors.append("Late payment must match bank evidence, be recorded with a late flag, and have no invented fee")

    return errors


def main() -> int:
    errors = validate_demo_data()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: 20 synthetic bank rows, tagged amounts, 5 screenshot scenarios, and 1 late payer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

