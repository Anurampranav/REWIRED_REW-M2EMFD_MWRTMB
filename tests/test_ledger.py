import copy
import sqlite3

import pytest

from backend.database import audited_transaction, connect
from backend.ledger import member_statement, post_verified_payment
from test_contract import EXAMPLES, validator_for


@pytest.fixture
def store(tmp_path):
    db, context = connect(tmp_path / "ledger.db")
    with audited_transaction(db, context, actor="foreman", reason="seed demo"):
        db.execute("INSERT INTO members VALUES ('m1', 'Ravi')")
        db.execute("INSERT INTO members VALUES ('m2', 'Other')")
        for month in range(1, 4):
            db.execute("INSERT INTO months VALUES (?, ?)", (month, "2026-12-01"))
            db.execute("INSERT INTO payments VALUES (?, 'm1', ?, ?, ?, 'verified')", (f"p{month}", month, 445001, f"{month:012d}"))
    yield db, context
    db.close()


def test_three_month_statement_and_audit(store):
    db, context = store
    for month in range(1, 4):
        post_verified_payment(db, context, f"p{month}", actor="verifier", reason="matched bank credit")
    with audited_transaction(db, context, actor="foreman", reason="record demo entries"):
        for month, kind, amount in [(1, "dividend", 55000), (2, "dividend", 40000), (2, "late_fee", 10000), (3, "prize", 8400000)]:
            db.execute("INSERT INTO ledger_entries VALUES (?, 'm1', ?, NULL, ?, ?)", (f"{kind}-{month}", month, amount, kind))
        db.execute("INSERT INTO ledger_entries VALUES ('other', 'm2', 1, NULL, 999, 'prize')")
    statement = member_statement(db, "m1")
    assert statement == [
        {"month": 1, "instalment_paise": 445001, "dividend_paise": 55000, "late_fee_paise": 0, "prize_paise": 0, "status": "verified"},
        {"month": 2, "instalment_paise": 445001, "dividend_paise": 40000, "late_fee_paise": 10000, "prize_paise": 0, "status": "verified"},
        {"month": 3, "instalment_paise": 445001, "dividend_paise": 0, "late_fee_paise": 0, "prize_paise": 8400000, "status": "verified"},
    ]
    assert db.execute("SELECT COUNT(*) FROM audit_log WHERE actor='verifier' AND action='ledger_entries.insert' AND reason='matched bank credit'").fetchone()[0] == 3
    assert member_statement(db, "m2")[0]["prize_paise"] == 999
    state = copy.deepcopy(EXAMPLES["state_response"][0])
    state["statement"] = statement
    validator_for("state_response").validate(state)


def test_duplicate_and_unverified_rejected_without_changes(store):
    db, context = store
    post_verified_payment(db, context, "p1", actor="verifier", reason="matched")
    with audited_transaction(db, context, actor="foreman", reason="prepare test"):
        db.execute("INSERT INTO payments VALUES ('p1b', 'm1', 1, 445001, '999999999999', 'verified')")
        db.execute("UPDATE payments SET status='needs_review' WHERE id='p2'")
    before = db.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]
    for payment in ("p1", "p1b", "p2", "missing"):
        with pytest.raises(ValueError):
            post_verified_payment(db, context, payment, actor="verifier", reason="check")
    assert db.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0] == before
    with pytest.raises(sqlite3.IntegrityError):
        with audited_transaction(db, context, actor="verifier", reason="duplicate attempt"):
            db.execute("INSERT INTO ledger_entries VALUES ('bypass', 'm1', 1, 'p1b', 445001, 'payment')")


def test_missing_member_and_record_without_payment(store):
    db, context = store
    with pytest.raises(ValueError):
        member_statement(db, "unknown")
    assert member_statement(db, "m1") == []
    with audited_transaction(db, context, actor="foreman", reason="record fee"):
        db.execute("INSERT INTO ledger_entries VALUES ('fee', 'm1', 1, NULL, 100, 'late_fee')")
    assert member_statement(db, "m1")[0]["status"] == "pending"
