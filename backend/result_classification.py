"""Deterministic T15 payment classification; it never writes a ledger record."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from backend.payment_checks import PaymentCheckReport
from backend.screenshot_reader import ScreenshotClaim


VERIFIED = "verified"
DUPLICATE = "duplicate"
WRONG_AMOUNT = "wrong_amount"
NEEDS_REVIEW = "needs_review"
DEFAULT_CONFIDENCE_THRESHOLD = 0.80


@dataclass(frozen=True)
class ClassificationResult:
    """Audit-safe decision derived from OCR confidence and every T14 check."""

    classification: str
    reason: str
    confidence: float | None
    confidence_threshold: float
    expected_amount_paise: int
    actual_amount_paise: int | None
    utr: str | None
    duplicate: bool
    evidence_matches: bool
    validation_results: tuple[dict[str, object], ...]
    extracted: ScreenshotClaim | None

    def audit_record(self) -> dict[str, object]:
        """Full record for controlled audit storage; callers must not broadcast it."""
        return asdict(self)

    def message_response(self) -> dict:
        """Serialize only through the established T01 result-card contract."""
        return {"bubbles": [{
            "type": "result_card", "status": self.classification,
            "amount_paise": self.actual_amount_paise,
            "utr": self.utr if self.utr and self.classification != NEEDS_REVIEW else None,
            "reason": self.reason,
        }]}


def _results(report: PaymentCheckReport) -> tuple[dict[str, object], ...]:
    return tuple({"name": check.name, "passed": check.passed, "code": check.code, "reason": check.reason} for check in report.checks)


def _result(status: str, reason: str, claim: ScreenshotClaim | None, report: PaymentCheckReport, *, duplicate: bool = False, evidence_matches: bool = False) -> ClassificationResult:
    return ClassificationResult(status, reason, claim.confidence if claim else None,
                                DEFAULT_CONFIDENCE_THRESHOLD, report.expected_amount_paise,
                                report.claim.amount_paise, report.claim.utr, duplicate,
                                evidence_matches, _results(report), claim)


def classify_payment(claim: ScreenshotClaim | None, report: PaymentCheckReport, *, confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD) -> ClassificationResult:
    """Classify after T14; high OCR confidence is necessary but never proof by itself."""
    if not 0 <= confidence_threshold <= 1:
        raise ValueError("confidence_threshold must be between 0 and 1")
    validation = {check.name: check for check in report.checks}
    if claim is None:
        return _result(NEEDS_REVIEW, "Screenshot extraction is unavailable and requires manual review.", None, report)
    if claim.confidence is None:
        return _result(NEEDS_REVIEW, "OCR confidence is unavailable; independent review is required.", claim, report)
    if not 0 <= claim.confidence <= 1:
        return _result(NEEDS_REVIEW, "OCR confidence is invalid; independent review is required.", claim, report)
    if claim.confidence < confidence_threshold:
        return _result(NEEDS_REVIEW, f"OCR confidence {claim.confidence:.2f} is below the required {confidence_threshold:.2f}.", claim, report)
    duplicate_codes = {"duplicate_utr", "duplicate_image"}
    if any(check.code in duplicate_codes for check in report.checks):
        check = next(check for check in report.checks if check.code in duplicate_codes)
        return _result(DUPLICATE, check.reason, claim, report, duplicate=True)
    amount = validation["expected_amount"]
    if amount.code == "wrong_amount":
        return _result(WRONG_AMOUNT, amount.reason, claim, report)
    if not claim.transaction_date:
        return _result(NEEDS_REVIEW, "Screenshot transaction date is unavailable for validation.", claim, report)
    if any(not check.passed for check in report.checks):
        failed = next(check for check in report.checks if not check.passed)
        return _result(NEEDS_REVIEW, failed.reason, claim, report)
    return _result(VERIFIED, "Matched independent settled bank evidence after deterministic checks.", claim, report, evidence_matches=True)
