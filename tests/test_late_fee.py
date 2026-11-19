from datetime import date, datetime, timezone

import pytest

from backend.database import audited_transaction, connect
from backend.group_config import GroupConfig
from backend.late_fee import calculate_late_fee, record_late_fee
from backend.ledger import member_statement, post_verified_payment


@pytest.fixture
def config():
    return GroupConfig(chit_value_paise=10_000_000, member_ids=("m1",), commission_basis_points=500,
                       due_date=date(2026, 12, 1), late_fee_type="flat", late_fee_value=10000,
                       max_discount_basis_points=4000, dividend_to_prized_members=True)


@pytest.mark.parametrize("credit,expected", [
    ("2026-12-01T18:29:59+00:00", 0),
    ("2026-12-01T18:30:00+00:00", 10000),
    ("2026-12-01T23:59:59+05:30", 0),
])
def test_due_date_cutoff_uses_bank_credit_in_india(config, credit, expected):
    assert calculate_late_fee(config, bank_credit_time=datetime.fromisoformat(credit), base_due_paise=445000) == expected


def test_percentage_and_exact_rounding(config):
    percent = config.model_copy(update={"late_fee_type": "percentage", "late_fee_value": 200})
    credit = datetime(2026, 12, 2, tzinfo=timezone.utc)
    assert calculate_late_fee(percent, bank_credit_time=credit, base_due_paise=445000) == 8900
    with pytest.raises(ValueError, match="exactly"):
        calculate_late_fee(percent, bank_credit_time=credit, base_due_paise=445001)
    with pytest.raises(ValueError, match="timezone"):
        calculate_late_fee(config, bank_credit_time=datetime(2026, 12, 2), base_due_paise=445000)


def test_record_fee_once_in_statement_and_audit(tmp_path, config):
    db, context = connect(tmp_path / "fees.db")
    with audited_transaction(db, context, actor="foreman", reason="setup"):
        db.execute("INSERT INTO members VALUES ('m1', 'Ravi')")
        db.execute("INSERT INTO months VALUES (1, '2026-12-01')")
        db.execute("INSERT INTO payments VALUES ('p1', 'm1', 1, 445001, '123456789012', 'verified')")
    post_verified_payment(db, context, "p1", actor="verifier", reason="bank match")
    args = dict(payment_id="p1", config=config, bank_credit_time=datetime(2026, 12, 2, tzinfo=timezone.utc), base_due_paise=445000, actor="verifier", reason="bank credit checked")
    assert record_late_fee(db, context, **args) == 10000
    assert member_statement(db, "m1")[0]["late_fee_paise"] == 10000
    reason = db.execute("SELECT reason FROM audit_log WHERE action='ledger_entries.insert' ORDER BY id DESC LIMIT 1").fetchone()[0]
    assert "bank credit 2026-12-02T00:00:00+00:00" in reason
    with pytest.raises(ValueError, match="already recorded"):
        record_late_fee(db, context, **args)
    assert db.execute("SELECT COUNT(*) FROM ledger_entries WHERE kind='late_fee'").fetchone()[0] == 1
    db.close()


def test_unverified_and_wrong_date_cannot_record(tmp_path, config):
    db, context = connect(tmp_path / "fees.db")
    with audited_transaction(db, context, actor="foreman", reason="setup"):
        db.execute("INSERT INTO members VALUES ('m1', 'Ravi')")
        db.execute("INSERT INTO months VALUES (1, '2026-12-02')")
        db.execute("INSERT INTO payments VALUES ('p1', 'm1', 1, 445001, NULL, 'needs_review')")
    args = dict(payment_id="p1", config=config, bank_credit_time=datetime(2026, 12, 3, tzinfo=timezone.utc), base_due_paise=445000, actor="verifier", reason="bank credit")
    with pytest.raises(ValueError, match="verified"):
        record_late_fee(db, context, **args)
    assert db.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0] == 0
    with audited_transaction(db, context, actor="verifier", reason="matched"):
        db.execute("UPDATE payments SET status='verified' WHERE id='p1'")
    post_verified_payment(db, context, "p1", actor="verifier", reason="matched")
    with pytest.raises(ValueError, match="due date"):
        record_late_fee(db, context, **args)
    assert db.execute("SELECT COUNT(*) FROM ledger_entries WHERE kind='late_fee'").fetchone()[0] == 0
    db.close()
