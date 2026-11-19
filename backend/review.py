"""Foreman decisions on needs-review payments; approval is not bank proof."""

from uuid import uuid4

from backend.database import audited_transaction


def review_payment(db, context, *, item_id: str, decision: str, actor: str, reason: str) -> dict:
    """Record one decision atomically. Demo item IDs are payment IDs."""
    if actor != "foreman":
        raise ValueError("only the foreman can review")
    if decision not in {"approve", "reject"}:
        raise ValueError("decision must be approve or reject")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("a review reason is required")
    with audited_transaction(db, context, actor=actor, reason=reason):
        db.execute("BEGIN IMMEDIATE")
        payment = db.execute(
            "SELECT member_id, month, status FROM payments WHERE id = ?", (item_id,)
        ).fetchone()
        if payment is None:
            raise ValueError("review item not found")
        member_id, month, status = payment
        if status != "needs_review":
            raise ValueError("payment is not awaiting review")
        new_status = "manual_approved" if decision == "approve" else "rejected"
        db.execute("UPDATE payments SET status = ? WHERE id = ?", (new_status, item_id))
        db.execute(
            "INSERT INTO ledger_entries (id, member_id, month, payment_id, amount_paise, kind) VALUES (?, ?, ?, ?, 0, ?)",
            (str(uuid4()), member_id, month, item_id, f"review_{decision}"),
        )
    return {"item_id": item_id, "decision": decision}
