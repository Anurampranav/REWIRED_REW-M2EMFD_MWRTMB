import sqlite3

import pytest

from backend.database import audited_transaction, connect


@pytest.fixture
def store(tmp_path):
    db, context = connect(tmp_path / "test.db")
    yield db, context
    db.close()


def seed(db, context):
    with audited_transaction(db, context, actor="foreman", reason="initial setup"):
        db.execute("INSERT INTO members VALUES (?, ?)", ("m1", "Ravi"))
        db.execute("INSERT INTO months VALUES (?, ?)", (3, "2026-12-01"))
        db.execute("INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?)", ("p1", "m1", 3, 445007, "123456789012", "verified"))
        db.execute("INSERT INTO ledger_entries VALUES (?, ?, ?, ?, ?, ?)", ("l1", "m1", 3, "p1", 445007, "payment"))


def test_mutations_produce_atomic_audit_rows(store):
    db, context = store
    seed(db, context)
    rows = db.execute("SELECT actor, action, reason, timestamp, entity_id FROM audit_log ORDER BY id").fetchall()
    assert [row[1] for row in rows] == ["members.insert", "months.insert", "payments.insert", "ledger_entries.insert"]
    assert all(row[0] == "foreman" and row[2] == "initial setup" and row[3].endswith("Z") for row in rows)
    with audited_transaction(db, context, actor="foreman", reason="correct name"):
        db.execute("UPDATE members SET name = ? WHERE id = ?", ("Ravi Kumar", "m1"))
    assert db.execute("SELECT actor, action, reason FROM audit_log ORDER BY id DESC LIMIT 1").fetchone() == ("foreman", "members.update", "correct name")


@pytest.mark.parametrize("sql", [
    "UPDATE audit_log SET reason = 'changed' WHERE id = 1",
    "DELETE FROM audit_log WHERE id = 1",
    "INSERT OR REPLACE INTO audit_log(id, actor, action, reason, timestamp, entity_id) VALUES (1, 'x', 'x', 'x', 'x', 'x')",
    "UPDATE ledger_entries SET amount_paise = 0 WHERE id = 'l1'",
    "DELETE FROM ledger_entries WHERE id = 'l1'",
    "INSERT OR REPLACE INTO ledger_entries VALUES ('l1', 'm1', 3, 'p1', 0, 'payment')",
])
def test_history_cannot_be_changed(store, sql):
    db, context = store
    seed(db, context)
    with pytest.raises(sqlite3.IntegrityError):
        with audited_transaction(db, context, actor="foreman", reason="attempt"):
            db.execute(sql)
    assert db.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == 4
    assert db.execute("SELECT amount_paise FROM ledger_entries WHERE id = 'l1'").fetchone()[0] == 445007


def test_audit_context_required_and_rollback_is_atomic(store):
    db, context = store
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO members VALUES ('m1', 'Ravi')")
    db.rollback()
    with pytest.raises(ValueError):
        with audited_transaction(db, context, actor="foreman", reason=" "):
            pass
    with pytest.raises(RuntimeError):
        with audited_transaction(db, context, actor="foreman", reason="setup"):
            db.execute("INSERT INTO members VALUES ('m1', 'Ravi')")
            raise RuntimeError("simulate failure")
    assert db.execute("SELECT COUNT(*) FROM members").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == 0


def test_foreign_keys_are_enforced(store):
    db, context = store
    with pytest.raises(sqlite3.IntegrityError):
        with audited_transaction(db, context, actor="foreman", reason="payment"):
            db.execute("INSERT INTO payments VALUES ('p', 'missing', 1, 100, NULL, 'pending')")


def test_replace_blocked_with_recursive_triggers_off(store):
    db, context = store
    seed(db, context)
    db.execute("PRAGMA recursive_triggers = OFF")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT OR REPLACE INTO audit_log(id, actor, action, reason, timestamp, entity_id) VALUES (1, 'x', 'x', 'x', 'x', 'x')")
