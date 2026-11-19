"""Generate deterministic, synthetic shared fixtures for T04.

The generated JSON files use only definitions from contracts/schemas.json.
Financial schedule and bank evidence are CSV because T01 intentionally has no
schema for chit configuration, auctions, or bank evidence rows.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
GROUP_ID = "group-synthetic-01"
MEMBER_COUNT = 20
CHIT_VALUE_PAISE = 10_000_000
COMMISSION_PAISE = 500_000
SCHEDULE = (
    # month, discount, due date, winner
    (1, 1_200_000, "2026-01-05", "member-01"),
    (2, 1_400_000, "2026-02-05", "member-02"),
    (3, 1_600_000, "2026-03-05", "member-03"),
    (4, 1_800_000, "2026-04-05", "member-04"),
)


def utr(month: int, member: int) -> str:
    """A 12-digit test identifier; it is deliberately not a real reference."""
    return f"{month:02d}{member:010d}"


def expected_instalment(discount_paise: int) -> int:
    dividend = (discount_paise - COMMISSION_PAISE) // MEMBER_COUNT
    return CHIT_VALUE_PAISE // MEMBER_COUNT - dividend


def payment_status(month: int, member: int) -> str:
    if month == 3 and member == 19:
        return "rejected"
    if month == 3 and member == 20:
        return "needs_review"
    if month == 4 and member == 16:
        return "rejected"
    if month == 4 and member == 17:
        return "needs_review"
    if month == 4 and member in {18, 19}:
        return "overdue"
    if month == 4 and member == 20:
        return "pending"
    return "verified"


def build_state() -> dict:
    members = [{"id": f"member-{number:02d}", "name": f"Member {number:02d}"} for number in range(1, MEMBER_COUNT + 1)]
    ledger: list[dict] = []
    evidence: list[dict] = []
    schedule_by_month = {month: discount for month, discount, _, _ in SCHEDULE}
    for month in range(1, 5):
        expected = expected_instalment(schedule_by_month[month])
        for member in range(1, MEMBER_COUNT + 1):
            status = payment_status(month, member)
            amount = expected - 100 if (month, member) in {(3, 19), (4, 16)} else expected
            entry = {
                "member_id": f"member-{member:02d}",
                "month": month,
                "status": status,
                "amount_paise": amount,
                "utr": utr(month, member) if status in {"verified", "rejected"} else None,
            }
            ledger.append(entry)
            if status == "verified":
                evidence.append({
                    "evidence_id": f"evidence-{month:02d}-{member:02d}",
                    "group_id": GROUP_ID,
                    "utr": entry["utr"],
                    "amount_paise": amount,
                    "credited_at": f"2026-{month:02d}-04T10:{member:02d}:00+05:30",
                    "payer_reference": f"synthetic-member-{member:02d}",
                })
    collected = sum(item["amount_paise"] for item in ledger if item["status"] == "verified")
    audit_log = [
        {"id": "audit-001", "actor": "member-01", "action": "payment_submitted", "reason": "Synthetic screenshot claim for month 1.", "timestamp": "2026-01-03T09:00:00+05:30"},
        {"id": "audit-002", "actor": "system", "action": "payment_processed", "reason": "Reader extracted a complete synthetic payment record.", "timestamp": "2026-01-03T09:00:02+05:30"},
        {"id": "audit-003", "actor": "system", "action": "payment_claimed", "reason": "Screenshot is a claim while independent evidence is pending.", "timestamp": "2026-01-03T09:00:03+05:30"},
        {"id": "audit-004", "actor": "system", "action": "payment_verified", "reason": "Synthetic bank evidence matched UTR and amount.", "timestamp": "2026-01-04T10:01:00+05:30"},
        {"id": "audit-005", "actor": "system", "action": "payment_rejected", "reason": "Month 3 amount was 100 paise below the expected instalment.", "timestamp": "2026-03-04T10:19:00+05:30"},
        {"id": "audit-006", "actor": "foreman", "action": "admin_override", "reason": "Rejected synthetic month 4 claim after manual amount review.", "timestamp": "2026-04-05T12:00:00+05:30"},
        {"id": "audit-007", "actor": "foreman", "action": "member_reassigned", "reason": "Synthetic receipt moved from member-12 to member-13 with recorded approval.", "timestamp": "2026-04-05T12:01:00+05:30"},
    ]
    for month, discount, _, winner in SCHEDULE:
        audit_log.append({
            "id": f"audit-auction-{month:02d}",
            "actor": "foreman",
            "action": "auction_winner_recorded",
            "reason": f"Month {month} winner {winner}; synthetic discount {discount} paise.",
            "timestamp": f"2026-{month:02d}-05T18:00:00+05:30",
        })
    return {
        "members": members,
        "months": [1, 2, 3, 4],
        "ledger": ledger,
        "counters": {
            "collected_paise": collected,
            "paid": sum(item["status"] == "verified" for item in ledger),
            "total_members": MEMBER_COUNT,
            "needs_review": sum(item["status"] == "needs_review" for item in ledger),
            "overdue": sum(item["status"] == "overdue" for item in ledger),
        },
        "flags": [
            {"item_id": "review-month-03-member-20", "member_id": "member-20", "month": 3, "reason": "Screenshot claim has no matching independent bank evidence."},
            {"item_id": "review-month-04-member-17", "member_id": "member-17", "month": 4, "reason": "Reader confidence is below the manual-review threshold."},
        ],
        "overdue": [item for item in ledger if item["status"] == "overdue"],
        "audit_log": audit_log,
        "statement": [
            {
                "month": month,
                "instalment_paise": expected_instalment(discount),
                "dividend_paise": (discount - COMMISSION_PAISE) // MEMBER_COUNT,
                "late_fee_paise": 0,
                "prize_paise": CHIT_VALUE_PAISE - discount,
                "status": "verified",
            }
            for month, discount, _, _ in SCHEDULE
        ],
        "private_bubbles": [],
    }, evidence


def write_json(name: str, value: object) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_csv(name: str, rows: list[dict]) -> None:
    with (ROOT / name).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    state, evidence = build_state()
    write_json("state_foreman.json", state)
    write_json("result_examples.json", {
        "message_response": [{"bubbles": [
            {"type": "text", "text": "Synthetic payment claim received for checking."},
            {"type": "result_card", "status": "verified", "amount_paise": 445000, "utr": utr(3, 1), "reason": "Independent synthetic bank evidence matched."},
            {"type": "result_card", "status": "duplicate", "amount_paise": 445000, "utr": utr(3, 1), "reason": "Synthetic UTR was already used."},
            {"type": "result_card", "status": "wrong_amount", "amount_paise": 444900, "utr": utr(3, 19), "reason": "Expected 445000 paise."},
            {"type": "result_card", "status": "needs_review", "amount_paise": 445000, "utr": None, "reason": "No independent synthetic bank evidence matches this screenshot claim."},
            {"type": "review_request", "item_id": "review-month-03-member-20", "reason": "Independent evidence is missing."},
            {"type": "reminder", "text": "Synthetic reminder: your month 4 instalment is due."},
        ]}],
        "review_request": [{"item_id": "review-month-03-member-20", "decision": "reject", "reason": "Independent evidence was not available.", "actor": "foreman"}],
        "review_response": [{"item_id": "review-month-03-member-20", "decision": "reject"}],
        "reminders_request": [{"actor": "foreman"}],
        "reminders_response": [{"sent": 3}],
        "demo_load_request": [{"actor": "foreman"}],
        "demo_load_response": [{"loaded": True}],
        "error_response": [{"error": {"code": "synthetic_validation_error", "message": "Synthetic fixture only."}}],
    })
    write_csv("financial_schedule.csv", [
        {
            "group_id": GROUP_ID,
            "month": month,
            "chit_value_paise": CHIT_VALUE_PAISE,
            "member_count": MEMBER_COUNT,
            "commission_paise": COMMISSION_PAISE,
            "winning_discount_paise": discount,
            "winner_member_id": winner,
            "due_date": due_date,
            "prize_paise": CHIT_VALUE_PAISE - discount,
            "surplus_paise": discount - COMMISSION_PAISE,
            "dividend_per_member_paise": (discount - COMMISSION_PAISE) // MEMBER_COUNT,
            "expected_instalment_paise": expected_instalment(discount),
            "expected_pool_paise": expected_instalment(discount) * MEMBER_COUNT,
        }
        for month, discount, due_date, winner in SCHEDULE
    ])
    write_csv("bank_evidence.csv", evidence)


if __name__ == "__main__":
    main()
