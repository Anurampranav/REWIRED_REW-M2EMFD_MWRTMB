from datetime import date

import pytest
from pydantic import ValidationError

from backend.group_config import GroupConfig


@pytest.fixture
def config():
    return dict(
        chit_value_paise=10_000_000,
        member_ids=tuple(f"member-{i}" for i in range(1, 21)),
        commission_basis_points=500,
        due_date=date(2026, 12, 1),
        late_fee_type="flat",
        late_fee_value=10000,
        max_discount_basis_points=4000,
        dividend_to_prized_members=True,
    )


def test_demo_configuration(config):
    group = GroupConfig(**config)
    assert group.chit_value_paise == 10_000_000
    assert len(group.member_ids) == 20
    assert group.commission_basis_points == 500


@pytest.mark.parametrize("change", [
    {"chit_value_paise": -1},
    {"member_ids": ("member-1", "member-1")},
    {"member_ids": (" ",)},
    {"commission_basis_points": 10001},
    {"max_discount_basis_points": -1},
    {"late_fee_value": -1},
    {"chit_value_paise": 1.5},
])
def test_invalid_configuration_is_rejected(config, change):
    with pytest.raises(ValidationError):
        GroupConfig(**(config | change))
