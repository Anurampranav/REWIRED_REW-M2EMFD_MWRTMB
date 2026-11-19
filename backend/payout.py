"""Immutable settlement registration and demo-only payout ledger gate."""

from uuid import uuid4

from backend.chit_engine import settle_month
from backend.database import audited_transaction


def _require_foreman(actor):
    if actor != "foreman":
        raise ValueError("only the foreman can settle or unlock payout")


def register_settlement(db, context, *, month, config, winner_id, discount_paise,
                        previously_prized=(), actor, reason):
    """Calculate and save the agreed member set, amounts and winner once."""
    _require_foreman(actor)
    settlement = settle_month(config, winner_id=winner_id, discount_paise=discount_paise,
                              previously_prized=previously_prized)
    with audited_transaction(db, context, actor=actor, reason=reason):
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute("SELECT due_date FROM months WHERE month = ?", (month,)).fetchone()
        if existing is None or existing[0] != config.due_date.isoformat():
            raise ValueError("month and configured due date must match")
        if {row[0] for row in db.execute("SELECT id FROM members")} != set(config.member_ids):
            raise ValueError("configured members must match the group")
        db.execute("INSERT INTO settlements VALUES (?, ?, ?, ?, ?, ?)",
                   (month, winner_id, discount_paise, settlement.prize_paise,
                    settlement.commission_paise, settlement.total_tag_paise))
        db.executemany("INSERT INTO settlement_dues VALUES (?, ?, ?, ?, ?)",
                       [(month, due.member_id, due.base_due_paise, due.tag_paise, due.dividend_paise)
                        for due in settlement.dues])
    return settlement


def unlock_payout(db, context, *, month, actor, reason):
    """Record a demo payout once; no real bank transfer is performed."""
    _require_foreman(actor)
    with audited_transaction(db, context, actor=actor, reason=reason):
        db.execute("BEGIN IMMEDIATE")
        settlement = db.execute("SELECT winner_id, prize_paise FROM settlements WHERE month = ?", (month,)).fetchone()
        if settlement is None:
            raise ValueError("settlement not found")
        winner_id, prize = settlement
        dues = db.execute("SELECT member_id, base_due_paise, tag_paise, dividend_paise FROM settlement_dues WHERE month = ? ORDER BY member_id", (month,)).fetchall()
        if not dues or {r[0] for r in dues} != {r[0] for r in db.execute("SELECT id FROM members")}:
            raise ValueError("settlement member set does not match group")
        prior_prize = db.execute("SELECT member_id, amount_paise FROM ledger_entries WHERE month = ? AND kind = 'prize'", (month,)).fetchone()
        if prior_prize:
            dividends = db.execute("SELECT member_id, amount_paise FROM ledger_entries WHERE month = ? AND kind = 'dividend' ORDER BY member_id", (month,)).fetchall()
            if prior_prize != (winner_id, prize) or dividends != [(r[0], r[3]) for r in dues]:
                raise ValueError("existing payout does not match settlement; reconcile manually")
            return {"unlocked": True, "already_recorded": True, "missing_members": []}
        missing = []
        for member, base, tag, dividend in dues:
            payment = db.execute("""
                SELECT p.amount_paise, p.status, l.amount_paise, p.member_id, p.month
                FROM ledger_entries l JOIN payments p ON p.id = l.payment_id
                WHERE l.member_id = ? AND l.month = ? AND l.kind = 'payment'
            """, (member, month)).fetchone()
            if payment is None or payment != (base + tag, "verified", base + tag, member, month):
                missing.append(member)
        # Fee payments are not represented yet; do not count unpaid fees as settled.
        if db.execute("SELECT 1 FROM ledger_entries WHERE month = ? AND kind = 'late_fee' AND amount_paise > 0", (month,)).fetchone():
            raise ValueError("late fees require reconciliation before payout")
        if missing:
            return {"unlocked": False, "already_recorded": False, "missing_members": missing}
        if db.execute("SELECT 1 FROM ledger_entries WHERE month = ? AND kind = 'dividend'", (month,)).fetchone():
            raise ValueError("dividend already recorded; reconcile before payout")
        db.execute("INSERT INTO ledger_entries VALUES (?, ?, ?, NULL, ?, 'prize')", (str(uuid4()), winner_id, month, prize))
        db.executemany("INSERT INTO ledger_entries VALUES (?, ?, ?, NULL, ?, 'dividend')",
                       [(str(uuid4()), member, month, dividend) for member, _, _, dividend in dues])
        return {"unlocked": True, "already_recorded": False, "missing_members": []}
