"""Private demo reminders. No WhatsApp or external messages are sent."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from backend.database import audited_transaction

INDIA_TIME = timezone(timedelta(hours=5, minutes=30))


def india_today():
    return datetime.now(INDIA_TIME).date()


def send_reminders(db, context, *, actor, today=None, send_now=False):
    """Persist due reminders once per recipient/month/phase/day, atomically."""
    if send_now and actor != "foreman":
        raise ValueError("only the foreman can trigger reminders")
    if not send_now and actor != "scheduler":
        raise ValueError("scheduled reminders require scheduler actor")
    today = today or india_today()
    if type(today) is not date:
        raise ValueError("today must be a date")
    count = 0
    with audited_transaction(db, context, actor=actor, reason="send private payment reminders"):
        db.execute("BEGIN IMMEDIATE")
        months = db.execute("SELECT month, due_date FROM months ORDER BY month").fetchall()
        members = [row[0] for row in db.execute("SELECT id FROM members ORDER BY id")]
        for month, due_text in months:
            due = date.fromisoformat(due_text)
            days = (due - today).days
            phase = "before" if days == 2 else "due" if days == 0 else "overdue" if days < 0 else None
            if phase is None or (send_now and phase != "overdue"):
                continue
            for member in members:
                paid = db.execute("""
                    SELECT 1 FROM ledger_entries l JOIN payments p ON p.id = l.payment_id
                    WHERE l.member_id = ? AND l.month = ? AND l.kind = 'payment'
                      AND p.member_id = l.member_id AND p.month = l.month AND p.status = 'verified'
                """, (member, month)).fetchone()
                if paid:
                    continue
                already = db.execute("SELECT 1 FROM reminders WHERE member_id=? AND month=? AND phase=? AND send_date=?",
                                     (member, month, phase, today.isoformat())).fetchone()
                if already:
                    continue
                text = {"before": f"Month {month} payment is due in 2 days.",
                        "due": f"Month {month} payment is due today.",
                        "overdue": f"Month {month} payment is overdue."}[phase]
                db.execute("INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?)",
                           (str(uuid4()), member, month, phase, today.isoformat(), text))
                count += 1
    return count


def private_bubbles(db, member_id):
    return [{"type": "reminder", "text": row[0]} for row in
            db.execute("SELECT text FROM reminders WHERE member_id=? ORDER BY rowid", (member_id,))]
