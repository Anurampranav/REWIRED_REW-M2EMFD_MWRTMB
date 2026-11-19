"""SQLite storage primitives; all domain mutations require an audit context."""

from contextlib import contextmanager
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS members (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL CHECK(length(trim(name)) > 0)
);
CREATE TABLE IF NOT EXISTS months (
    month INTEGER PRIMARY KEY CHECK(month > 0),
    due_date TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL REFERENCES members(id),
    month INTEGER NOT NULL REFERENCES months(month),
    amount_paise INTEGER NOT NULL CHECK(amount_paise >= 0),
    utr TEXT,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ledger_entries (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL REFERENCES members(id),
    month INTEGER NOT NULL REFERENCES months(month),
    payment_id TEXT REFERENCES payments(id),
    amount_paise INTEGER NOT NULL CHECK(amount_paise >= 0),
    kind TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT NOT NULL CHECK(length(trim(actor)) > 0),
    action TEXT NOT NULL,
    reason TEXT NOT NULL CHECK(length(trim(reason)) > 0),
    timestamp TEXT NOT NULL,
    entity_id TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ledger_one_payment_per_month
ON ledger_entries(member_id, month) WHERE kind = 'payment';
CREATE UNIQUE INDEX IF NOT EXISTS ledger_one_posting_per_payment
ON ledger_entries(payment_id) WHERE kind = 'payment' AND payment_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS ledger_one_late_fee_per_payment
ON ledger_entries(payment_id) WHERE kind = 'late_fee' AND payment_id IS NOT NULL;
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_replace BEFORE INSERT ON audit_log
WHEN EXISTS (SELECT 1 FROM audit_log WHERE id = NEW.id)
BEGIN SELECT RAISE(ABORT, 'audit log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS ledger_no_update BEFORE UPDATE ON ledger_entries
BEGIN SELECT RAISE(ABORT, 'ledger is append-only'); END;
CREATE TRIGGER IF NOT EXISTS ledger_no_delete BEFORE DELETE ON ledger_entries
BEGIN SELECT RAISE(ABORT, 'ledger is append-only'); END;
CREATE TRIGGER IF NOT EXISTS ledger_no_replace BEFORE INSERT ON ledger_entries
WHEN EXISTS (SELECT 1 FROM ledger_entries WHERE id = NEW.id)
BEGIN SELECT RAISE(ABORT, 'ledger is append-only'); END;
"""


def connect(path):
    """Open an initialized connection; use audited_transaction for domain writes."""
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys = ON")
    # REPLACE deletes the previous row: recursive triggers must catch it.
    db.execute("PRAGMA recursive_triggers = ON")
    context = {"actor": None, "reason": None}
    db.create_function("audit_actor", 0, lambda: context["actor"])
    db.create_function("audit_reason", 0, lambda: context["reason"])
    db.executescript(SCHEMA)
    for table, key in (("members", "id"), ("months", "month"), ("payments", "id"), ("ledger_entries", "id")):
        for operation in ("INSERT", "UPDATE", "DELETE"):
            row = "OLD" if operation == "DELETE" else "NEW"
            db.execute(f"""
                CREATE TRIGGER IF NOT EXISTS audit_{table}_{operation.lower()}
                AFTER {operation} ON {table}
                BEGIN
                  INSERT INTO audit_log(actor, action, reason, timestamp, entity_id)
                  VALUES (audit_actor(), '{table}.{operation.lower()}', audit_reason(),
                          strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), CAST({row}.{key} AS TEXT));
                END
            """)
    return db, context


@contextmanager
def audited_transaction(db, context, *, actor, reason):
    """Commit domain writes and their audit rows atomically or roll back both."""
    if not isinstance(actor, str) or not actor.strip() or not isinstance(reason, str) or not reason.strip():
        raise ValueError("actor and reason are required")
    if db.in_transaction or context["actor"] is not None:
        raise RuntimeError("nested or already active transactions are not supported")
    context.update(actor=actor, reason=reason)
    try:
        with db:
            yield db
    finally:
        context.update(actor=None, reason=None)
