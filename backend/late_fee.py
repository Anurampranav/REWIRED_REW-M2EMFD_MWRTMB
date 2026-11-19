"""Late-fee assessment from independently supplied bank credit timestamps."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from backend.database import audited_transaction
from backend.group_config import GroupConfig

INDIA_TIME = timezone(timedelta(hours=5, minutes=30))


def calculate_late_fee(config: GroupConfig, *, bank_credit_time: datetime, base_due_paise: int) -> int:
    """Assess after the due date in India; percentage applies to the untagged base."""
    if not isinstance(bank_credit_time, datetime) or bank_credit_time.utcoffset() is None:
        raise ValueError("bank credit time must include a timezone offset")
    if type(base_due_paise) is not int or base_due_paise < 0:
        raise ValueError("base due must be non-negative integer paise")
    if bank_credit_time.astimezone(INDIA_TIME).date() <= config.due_date:
        return 0
    if config.late_fee_type == "flat":
        return config.late_fee_value
    amount, remainder = divmod(base_due_paise * config.late_fee_value, 10_000)
    if remainder:
        raise ValueError("percentage fee cannot be represented exactly in paise")
    return amount


def record_late_fee(db, context, *, payment_id: str, config: GroupConfig, bank_credit_time: datetime,
                    base_due_paise: int, actor: str, reason: str) -> int:
    """Record a fee once after verified payment posting; inputs must come from trusted services."""
    fee = calculate_late_fee(config, bank_credit_time=bank_credit_time, base_due_paise=base_due_paise)
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("a reason is required")
    audit_reason = f"{reason.strip()} | bank credit {bank_credit_time.isoformat()} | base due {base_due_paise} paise"
    with audited_transaction(db, context, actor=actor, reason=audit_reason):
        db.execute("BEGIN IMMEDIATE")
        payment = db.execute(
            "SELECT p.member_id, p.month, p.status, m.due_date "
            "FROM payments p JOIN months m ON m.month = p.month WHERE p.id = ?", (payment_id,)
        ).fetchone()
        if payment is None:
            raise ValueError("payment not found")
        member_id, month, status, due_date = payment
        if status != "verified" or not db.execute(
            "SELECT 1 FROM ledger_entries WHERE payment_id = ? AND kind = 'payment'", (payment_id,)
        ).fetchone():
            raise ValueError("payment must be verified and posted")
        try:
            stored_due = date.fromisoformat(due_date)
        except ValueError as exc:
            raise ValueError("stored due date must be ISO formatted") from exc
        if stored_due != config.due_date:
            raise ValueError("configured due date does not match the payment month")
        if db.execute("SELECT 1 FROM ledger_entries WHERE payment_id = ? AND kind = 'late_fee'", (payment_id,)).fetchone():
            raise ValueError("late fee already recorded")
        if fee:
            db.execute(
                "INSERT INTO ledger_entries (id, member_id, month, payment_id, amount_paise, kind) VALUES (?, ?, ?, ?, ?, 'late_fee')",
                (str(uuid4()), member_id, month, payment_id, fee),
            )
    return fee
