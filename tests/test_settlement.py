from datetime import date

import pytest

from backend.chit_engine import settle_month
from backend.group_config import GroupConfig


@pytest.fixture
def group():
    return GroupConfig(chit_value_paise=10_000_000, member_ids=tuple(f"m{i}" for i in range(1, 21)), commission_basis_points=500, due_date=date(2026, 12, 1), late_fee_type="flat", late_fee_value=0, max_discount_basis_points=4000, dividend_to_prized_members=True)


def test_example_and_distinct_tagged_amounts(group):
    result = settle_month(group, winner_id="m7", discount_paise=1_600_000)
    assert (result.prize_paise, result.commission_paise, result.total_dividend_paise) == (8_400_000, 500_000, 1_100_000)
    assert len({d.tagged_due_paise for d in result.dues}) == 20
    assert all(d.dividend_paise == 55_000 and d.base_due_paise == 445_000 for d in result.dues)
    assert result.dues[6].tagged_due_paise == 445_007
    assert sum(d.base_due_paise for d in result.dues) == result.prize_paise + result.commission_paise
    assert sum(d.tagged_due_paise for d in result.dues) == result.prize_paise + result.commission_paise + result.total_tag_paise


@pytest.mark.parametrize("discount", [499_999, 4_000_001, -1, 1.5, True])
def test_invalid_discount_rejected(group, discount):
    with pytest.raises(ValueError):
        settle_month(group, winner_id="m7", discount_paise=discount)


def test_exact_rounding_and_member_validation(group):
    with pytest.raises(ValueError, match="dividend"):
        settle_month(group, winner_id="m7", discount_paise=1_600_001)
    with pytest.raises(ValueError, match="belong"):
        settle_month(group, winner_id="unknown", discount_paise=1_600_000)


def test_excluded_prized_members_get_no_dividend(group):
    config = group.model_copy(update={"dividend_to_prized_members": False})
    result = settle_month(config, winner_id="m7", discount_paise=501_800, previously_prized=("m1",))
    assert result.dues[0].dividend_paise == result.dues[6].dividend_paise == 0
    assert result.dues[1].dividend_paise == 100
    assert sum(d.base_due_paise for d in result.dues) == result.prize_paise + result.commission_paise
