import csv
import json
from pathlib import Path

from screenshot_fixture_tools import (
    ALLOWED_STATUSES,
    APP_LAYOUTS,
    CATEGORIES,
    MIN_IMAGES,
    PROVISIONAL_CSV,
    PROVISIONAL_DUE_DATE,
    REASON_BY_CATEGORY,
    STATUS_BY_CATEGORY,
    WATERMARK_TEXT,
    DATASET_DIR,
    render_fixture_image,
)

LAYOUT_PLAN = {
    "genuine": ("gpay", "phonepe", "paytm", "bank_app") * 3,
    "fake": ("gpay", "phonepe", "paytm", "bank_app") * 2,
    "reused": ("gpay", "phonepe", "paytm", "bank_app", "gpay", "phonepe", "paytm"),
    "wrong_amount": ("gpay", "phonepe", "paytm", "bank_app", "gpay", "phonepe", "paytm"),
    "late": ("gpay", "phonepe", "paytm", "bank_app", "gpay", "bank_app"),
}
EXPECTED_AMOUNT = 445007
CLAIM_AMOUNT = {"wrong_amount": 445000}
CLAIMED_DATE = {
    "genuine": "2026-03-05",
    "fake": "2026-03-08",
    "reused": "2026-03-06",
    "wrong_amount": "2026-03-07",
}
CSV_COLUMNS = ("evidence_source", "utr", "amount_paise", "month", "credit_date", "member_id", "scenario_id")


def build_cases():
    cases = []
    for category in CATEGORIES:
        for index, layout in enumerate(LAYOUT_PLAN[category], start=1):
            if category == "genuine":
                utr = f"9000000000{index:02d}"
            elif category == "fake":
                utr = f"900000000{19 + index:03d}"
            elif category == "reused":
                utr = f"9000000000{1 + (index - 1) % 3:02d}"
            elif category == "wrong_amount":
                utr = f"900000000{12 + index:03d}"
            else:
                utr = f"900000000{27 + index:03d}"
            claimed_date = CLAIMED_DATE.get(category, f"2026-03-{11 + index:02d}")
            image_id = f"T07-{category.replace('_', '-').upper()}-{layout.upper()}-{index:03d}"
            cases.append({
                "image_id": image_id,
                "filename": f"{category}/{layout}/{image_id.lower()}.png",
                "app_layout": layout,
                "category": category,
                "synthetic": True,
                "expected_status": STATUS_BY_CATEGORY[category],
                "expected_reason": (
                    f"Expected {EXPECTED_AMOUNT} paise."
                    if category == "wrong_amount"
                    else REASON_BY_CATEGORY[category]
                ),
                "expected_amount": EXPECTED_AMOUNT,
                "claimed_amount": CLAIM_AMOUNT.get(category, EXPECTED_AMOUNT),
                "expected_month": 3,
                "expected_utr_reference": utr,
                "corresponding_bank_csv_reference": PROVISIONAL_CSV,
                "scenario_id": f"PROVISIONAL-T06-{category.replace('_', '-').upper()}-{index:02d}",
                "claimed_date": claimed_date,
            })
    return cases


def write_bank_csv(path: Path, cases: list[dict]) -> None:
    seen = set()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for case in cases:
            utr = case["expected_utr_reference"]
            if case["category"] == "fake" or utr in seen:
                continue
            seen.add(utr)
            writer.writerow({
                "evidence_source": "PROVISIONAL_NOT_T06",
                "utr": utr,
                "amount_paise": case["expected_amount"],
                "month": case["expected_month"],
                "credit_date": case["claimed_date"] if case["category"] == "late" else "2026-03-05",
                "member_id": "member-7",
                "scenario_id": case["scenario_id"],
            })


def write_manifest(path: Path, cases: list[dict]) -> None:
    manifest = {
        "dataset": "ChitMirror payment screenshot dataset",
        "version": 1,
        "provisional": True,
        "dependency_status": "Issue #6 is open; this CSV, due date and scenario IDs are explicitly provisional",
        "provisional_due_date": PROVISIONAL_DUE_DATE,
        "minimum_images": MIN_IMAGES,
        "categories": list(CATEGORIES),
        "app_layouts": list(APP_LAYOUTS),
        "allowed_statuses": list(ALLOWED_STATUSES),
        "watermark": WATERMARK_TEXT,
        "bank_csv_reference": PROVISIONAL_CSV,
        "images": cases,
    }
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def generate(dataset_dir: Path = DATASET_DIR) -> list[dict]:
    dataset_dir.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    for case in cases:
        render_fixture_image(
            dataset_dir / case["filename"],
            layout=case["app_layout"],
            category=case["category"],
            image_id=case["image_id"],
            utr=case["expected_utr_reference"],
            claim_amount=case["claimed_amount"],
            claimed_date=case["claimed_date"],
        )
    write_bank_csv(dataset_dir / PROVISIONAL_CSV, cases)
    write_manifest(dataset_dir / "manifest.json", cases)
    return cases


def main() -> None:
    cases = generate()
    print(f"Generated {len(cases)} provisional synthetic screenshot fixtures")


if __name__ == "__main__":
    main()
