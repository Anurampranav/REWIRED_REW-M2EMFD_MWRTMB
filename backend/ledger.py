"""Append verified payments and build per-member statements from ledger entries."""

import sqlite3
from uuid import uuid4

from backend.database import audited_transaction


def post_verified_payment(db, context, payment_id: str, *, actor: str, reason: str) -> str:
    """Post one pre-verified payment once, without performing verification here."""
    with audited_transaction(db, context, actor=actor, reason=reason):
        # Lock before reading so concurrent writers cannot both post the same month.
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT member_id, month, amount_paise, status FROM payments WHERE id = ?",
            (payment_id,),
        ).fetchone()
        if row is None:
            raise ValueError("payment not found")
        member_id, month, amount, status = row
        if status != "verified":
            raise ValueError("payment must be independently verified before posting")
        existing = db.execute(
            "SELECT 1 FROM ledger_entries WHERE kind = 'payment' AND (payment_id = ? OR (member_id = ? AND month = ?))",
            (payment_id, member_id, month),
        ).fetchone()
        if existing:
            raise ValueError("payment or member-month already posted")
        entry_id = str(uuid4())
        db.execute(
            "INSERT INTO ledger_entries (id, member_id, month, payment_id, amount_paise, kind) VALUES (?, ?, ?, ?, ?, 'payment')",
            (entry_id, member_id, month, payment_id, amount),
        )
    return entry_id


def member_statement(db: sqlite3.Connection, member_id: str) -> list[dict]:
    """Return ledger-derived figures only for the requested member, by month."""
    if db.execute("SELECT 1 FROM members WHERE id = ?", (member_id,)).fetchone() is None:
        raise ValueError("member not found")
    rows = db.execute(
        """
        SELECT month,
            SUM(CASE WHEN kind = 'payment' THEN amount_paise ELSE 0 END),
            SUM(CASE WHEN kind = 'dividend' THEN amount_paise ELSE 0 END),
            SUM(CASE WHEN kind = 'late_fee' THEN amount_paise ELSE 0 END),
            SUM(CASE WHEN kind = 'prize' THEN amount_paise ELSE 0 END),
            MAX(CASE WHEN kind = 'payment' THEN 1 ELSE 0 END)
        FROM ledger_entries WHERE member_id = ? GROUP BY month ORDER BY month
        """,
        (member_id,),
    ).fetchall()
    return [
        {"month": month, "instalment_paise": instalment, "dividend_paise": dividend,
         "late_fee_paise": late_fee, "prize_paise": prize,
         "status": "verified" if paid else "pending"}
        for month, instalment, dividend, late_fee, prize, paid in rows
    ]
