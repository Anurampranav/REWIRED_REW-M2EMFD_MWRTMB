import copy
import sqlite3

import pytest

from backend.database import audited_transaction, connect
from backend.ledger import member_statement, post_verified_payment
from backend.review import review_payment
from test_contract import EXAMPLES, validator_for


@pytest.fixture
def store(tmp_path):
    db, context = connect(tmp_path / "review.db")
    with audited_transaction(db, context, actor="foreman", reason="demo setup"):
        db.execute("INSERT INTO members VALUES ('m1', 'Ravi')")
        db.execute("INSERT INTO months VALUES (3, '2026-12-01')")
        db.execute("INSERT INTO payments VALUES ('p1', 'm1', 3, 445007, '123456789012', 'needs_review')")
    yield db, context
    db.close()


@pytest.mark.parametrize("decision,status,kind", [("approve", "manual_approved", "review_approve"), ("reject", "rejected", "review_reject")])
def test_decision_recorded_with_reason(store, decision, status, kind):
    db, context = store
    result = review_payment(db, context, item_id="p1", decision=decision, actor="foreman", reason="checked bank evidence")
    validator_for("review_response").validate(result)
    assert db.execute("SELECT status FROM payments WHERE id='p1'").fetchone()[0] == status
    assert db.execute("SELECT kind, amount_paise FROM ledger_entries").fetchone() == (kind, 0)
    audit = db.execute("SELECT action, actor, reason FROM audit_log WHERE action IN ('payments.update', 'ledger_entries.insert') ORDER BY id").fetchall()
    assert audit == [("payments.update", "foreman", "checked bank evidence"), ("ledger_entries.insert", "foreman", "checked bank evidence")]
    statement = member_statement(db, "m1")
    assert statement[0]["status"] == status
    state = copy.deepcopy(EXAMPLES["state_response"][0])
    state["statement"] = statement
    validator_for("state_response").validate(state)
    with pytest.raises(ValueError):
        post_verified_payment(db, context, "p1", actor="foreman", reason="try to post")
    with pytest.raises(ValueError):
        review_payment(db, context, item_id="p1", decision=decision, actor="foreman", reason="again")


@pytest.mark.parametrize("change", [
    {"reason": ""}, {"reason": "   "}, {"actor": "member-1"},
    {"decision": "maybe"}, {"item_id": "missing"},
])
def test_invalid_review_makes_no_changes(store, change):
    db, context = store
    args = {"item_id": "p1", "decision": "approve", "actor": "foreman", "reason": "checked"} | change
    with pytest.raises(ValueError):
        review_payment(db, context, **args)
    assert db.execute("SELECT status FROM payments WHERE id='p1'").fetchone()[0] == "needs_review"
    assert db.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0] == 0


def test_ledger_failure_rolls_back_status_and_audit(store):
    db, context = store
    db.execute("CREATE TRIGGER reject_review BEFORE INSERT ON ledger_entries BEGIN SELECT RAISE(ABORT, 'fail'); END")
    before = db.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):
        review_payment(db, context, item_id="p1", decision="approve", actor="foreman", reason="checked")
    assert db.execute("SELECT status FROM payments WHERE id='p1'").fetchone()[0] == "needs_review"
    assert db.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == before
