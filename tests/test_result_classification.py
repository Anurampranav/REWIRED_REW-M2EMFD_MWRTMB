from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from backend.payment_checks import ExtractedPaymentClaim, InMemoryImageHashRegistry, load_bank_evidence, validate_payment_claim
from backend.result_classification import DUPLICATE, NEEDS_REVIEW, VERIFIED, WRONG_AMOUNT, classify_payment
from backend.screenshot_reader import ScreenshotClaim


ROOT = Path(__file__).resolve().parents[1]
GROUP = json.loads((ROOT / "data" / "demo_chit.json").read_text())["group"]
EVIDENCE = load_bank_evidence(ROOT / "data" / "bank.csv")
SCENARIOS = json.loads((ROOT / "data" / "scenarios.json").read_text())["scenarios"]
SCHEMA = json.loads((ROOT / "contracts" / "schemas.json").read_text())


def screenshot(**changes):
    values = {"utr": "845270310001", "amount_paise": 500000, "payee": GROUP["group_upi_id"], "transaction_status": "completed", "transaction_date": "2026-11-04", "transaction_time": "10:00:00", "payment_application": "GPay", "confidence": .95}
    return ScreenshotClaim(**(values | changes))


def check_report(screen=None, **changes):
    screen = screen or screenshot()
    values = {"member_id": "member-01", "utr": screen.utr, "amount_paise": screen.amount_paise, "receiver_upi_id": screen.payee, "image_sha256": "a" * 64}
    payment_claim = ExtractedPaymentClaim(**(values | changes.pop("claim_changes", {})))
    return validate_payment_claim(payment_claim, expected_amount_paise=500000, expected_receiver_upi_id=GROUP["group_upi_id"], evidence_by_utr=EVIDENCE, **changes)


def classify(screen=None, **changes):
    screen = screen or screenshot()
    return classify_payment(screen, check_report(screen, **changes))


def test_bank_matched_high_confidence_claim_is_verified_and_contract_valid():
    result = classify()
    assert result.classification == VERIFIED and result.evidence_matches
    Draft202012Validator({**SCHEMA, "$ref": "#/$defs/message_response"}).validate(result.message_response())


@pytest.mark.parametrize(("screen", "kwargs", "expected"), [
    (screenshot(), {"used_utrs": ["845270310001"]}, DUPLICATE),
    (screenshot(), {"image_hash_registry": InMemoryImageHashRegistry(["a" * 64])}, DUPLICATE),
    (screenshot(amount_paise=450000), {}, WRONG_AMOUNT),
    (screenshot(confidence=.2), {}, NEEDS_REVIEW),
    (screenshot(utr=None), {}, NEEDS_REVIEW),
    (screenshot(amount_paise=None), {}, NEEDS_REVIEW),
    (screenshot(payee="other@upi"), {}, NEEDS_REVIEW),
    (screenshot(utr="845270319999"), {}, NEEDS_REVIEW),
    (screenshot(transaction_date=None), {}, NEEDS_REVIEW),
])
def test_result_categories_cover_duplicate_amount_confidence_and_incomplete_cases(screen, kwargs, expected):
    result = classify(screen, **kwargs)
    assert result.classification == expected and result.reason
    assert result.validation_results


def test_missing_confidence_or_malformed_claim_goes_to_review_without_fabricated_score():
    result = classify(screenshot(confidence=None))
    assert result.classification == NEEDS_REVIEW and result.confidence is None
    assert classify_payment(None, check_report()).classification == NEEDS_REVIEW


def test_conflicting_bank_evidence_and_multiple_failures_are_reviewable():
    result = classify(screenshot(payee="other@upi", transaction_date=None), claim_changes={"integrity_flags": ("metadata conflict",)})
    assert result.classification == NEEDS_REVIEW
    assert len([item for item in result.validation_results if not item["passed"]]) >= 2


def test_t06_planted_scenarios_classify_as_documented():
    expected = {"genuine_on_time": VERIFIED, "reused_utr": DUPLICATE, "fake_utr_not_in_csv": NEEDS_REVIEW, "wrong_amount": WRONG_AMOUNT, "late_payer": VERIFIED}
    for scenario in SCENARIOS:
        raw = scenario["claim"]
        screen = screenshot(utr=raw["utr"], amount_paise=raw["amount_paise"], payee=raw["receiver_upi_id"], transaction_date=raw["transaction_date"])
        claim_changes = {"member_id": raw["member_id"]}
        kwargs = {"claim_changes": claim_changes}
        if scenario["id"] == "reused_utr": kwargs["used_utrs"] = [raw["utr"]]
        assert classify(screen, **kwargs).classification == expected[scenario["id"]]
