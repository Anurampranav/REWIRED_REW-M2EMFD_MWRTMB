from datetime import date
import sqlite3

import pytest

from backend.database import audited_transaction, connect
from backend.group_config import GroupConfig
from backend.ledger import post_verified_payment
from backend.payout import register_settlement, unlock_payout


@pytest.fixture
def pool(tmp_path):
    db, context = connect(tmp_path / "pool.db")
    members = tuple(f"m{i:02d}" for i in range(1, 21))
    config = GroupConfig(chit_value_paise=10000000, member_ids=members, commission_basis_points=500,
                         due_date=date(2026, 12, 1), late_fee_type="flat", late_fee_value=0,
                         max_discount_basis_points=4000, dividend_to_prized_members=True)
    with audited_transaction(db, context, actor="foreman", reason="setup"):
        db.executemany("INSERT INTO members VALUES (?, ?)", [(member, member) for member in members])
        db.execute("INSERT INTO months VALUES (1, '2026-12-01')")
    settlement = register_settlement(db, context, month=1, config=config, winner_id="m07",
                                     discount_paise=1600000, actor="foreman", reason="winning bid")
    yield db, context, config, settlement
    db.close()


def pay(db, context, due, *, status="verified", adjustment=0):
    payment_id = f"payment-{due.member_id}"
    with audited_transaction(db, context, actor="verifier", reason="bank check"):
        db.execute("INSERT INTO payments VALUES (?, ?, 1, ?, ?, ?)",
                   (payment_id, due.member_id, due.tagged_due_paise + adjustment, f"{int(due.member_id[1:]):012d}", status))
    if status == "verified":
        post_verified_payment(db, context, payment_id, actor="verifier", reason="bank match")


def test_locked_until_all_verified_and_then_idempotent(pool):
    db, context, _, settlement = pool
    for due in settlement.dues[:-1]:
        pay(db, context, due)
    args = dict(month=1, actor="foreman", reason="pool complete")
    assert unlock_payout(db, context, **args) == {"unlocked": False, "already_recorded": False, "missing_members": ["m20"]}
    assert db.execute("SELECT COUNT(*) FROM ledger_entries WHERE kind IN ('prize', 'dividend')").fetchone()[0] == 0
    pay(db, context, settlement.dues[-1])
    assert unlock_payout(db, context, **args)["unlocked"] is True
    assert db.execute("SELECT member_id, amount_paise FROM ledger_entries WHERE kind='prize'").fetchone() == ("m07", 8400000)
    assert db.execute("SELECT COUNT(*), SUM(amount_paise) FROM ledger_entries WHERE kind='dividend'").fetchone() == (20, 1100000)
    assert unlock_payout(db, context, **args)["already_recorded"] is True
    assert db.execute("SELECT COUNT(*) FROM ledger_entries WHERE kind='dividend'").fetchone()[0] == 20


def test_manual_approval_and_wrong_amount_never_unlock(pool):
    db, context, _, settlement = pool
    for due in settlement.dues[:-2]:
        pay(db, context, due)
    pay(db, context, settlement.dues[-2], status="manual_approved")
    pay(db, context, settlement.dues[-1], adjustment=1)
    result = unlock_payout(db, context, month=1, actor="foreman", reason="test")
    assert result["unlocked"] is False
    assert result["missing_members"] == ["m19", "m20"]


def test_snapshot_is_immutable_and_foreman_only(pool):
    db, context, config, _ = pool
    with pytest.raises(sqlite3.IntegrityError):
        with audited_transaction(db, context, actor="foreman", reason="test"):
            db.execute("UPDATE settlements SET prize_paise = 1 WHERE month = 1")
    with pytest.raises(ValueError, match="foreman"):
        unlock_payout(db, context, month=1, actor="m01", reason="test")
    with pytest.raises(sqlite3.IntegrityError):
        register_settlement(db, context, month=1, config=config, winner_id="m07", discount_paise=1600000, actor="foreman", reason="again")


def test_late_fee_blocks_payout(pool):
    db, context, _, settlement = pool
    for due in settlement.dues:
        pay(db, context, due)
    with audited_transaction(db, context, actor="foreman", reason="fee"):
        db.execute("INSERT INTO ledger_entries VALUES ('fee', 'm01', 1, 'payment-m01', 100, 'late_fee')")
    with pytest.raises(ValueError, match="late fees"):
        unlock_payout(db, context, month=1, actor="foreman", reason="test")
    assert db.execute("SELECT COUNT(*) FROM ledger_entries WHERE kind='prize'").fetchone()[0] == 0


def test_payout_failure_rolls_back_all_entries(pool):
    db, context, _, settlement = pool
    for due in settlement.dues:
        pay(db, context, due)
    db.execute("CREATE TRIGGER fail_dividend BEFORE INSERT ON ledger_entries WHEN NEW.kind = 'dividend' BEGIN SELECT RAISE(ABORT, 'failure'); END")
    with pytest.raises(sqlite3.IntegrityError):
        unlock_payout(db, context, month=1, actor="foreman", reason="test")
    assert db.execute("SELECT COUNT(*) FROM ledger_entries WHERE kind IN ('prize', 'dividend')").fetchone()[0] == 0


def test_existing_dividend_is_not_duplicated(pool):
    db, context, _, settlement = pool
    for due in settlement.dues:
        pay(db, context, due)
    with audited_transaction(db, context, actor="foreman", reason="existing credit"):
        db.execute("INSERT INTO ledger_entries VALUES ('div', 'm01', 1, NULL, 55000, 'dividend')")
    with pytest.raises(ValueError, match="dividend already"):
        unlock_payout(db, context, month=1, actor="foreman", reason="test")
    assert db.execute("SELECT COUNT(*) FROM ledger_entries WHERE kind='prize'").fetchone()[0] == 0


def test_changed_group_stays_locked(pool):
    db, context, _, _ = pool
    with audited_transaction(db, context, actor="foreman", reason="new member"):
        db.execute("INSERT INTO members VALUES ('extra', 'Extra')")
    with pytest.raises(ValueError, match="member set"):
        unlock_payout(db, context, month=1, actor="foreman", reason="test")
