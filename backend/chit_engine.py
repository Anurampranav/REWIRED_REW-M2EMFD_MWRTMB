"""Pure settlement calculations; all monetary values are integer paise."""

from dataclasses import dataclass

from backend.group_config import GroupConfig


@dataclass(frozen=True)
class MemberDue:
    member_id: str
    dividend_paise: int
    base_due_paise: int
    tag_paise: int
    tagged_due_paise: int


@dataclass(frozen=True)
class Settlement:
    winner_id: str
    discount_paise: int
    prize_paise: int
    commission_paise: int
    total_dividend_paise: int
    total_tag_paise: int
    dues: tuple[MemberDue, ...]


def _exact_divide(value: int, divisor: int, field: str) -> int:
    quotient, remainder = divmod(value, divisor)
    if remainder:
        raise ValueError(f"{field} cannot be represented exactly in paise")
    return quotient


def settle_month(
    config: GroupConfig,
    *,
    winner_id: str,
    discount_paise: int,
    previously_prized: tuple[str, ...] = (),
) -> Settlement:
    """Calculate, without posting or paying, a month's settlement and tags."""
    members = config.member_ids
    if winner_id not in members or any(member not in members for member in previously_prized):
        raise ValueError("winner and previously prized members must belong to the group")
    if len(members) > 99:
        raise ValueError("paise tags support at most 99 members")
    if type(discount_paise) is not int or discount_paise < 0:
        raise ValueError("discount must be a non-negative integer number of paise")
    if discount_paise > config.chit_value_paise:
        raise ValueError("discount cannot exceed chit value")
    if discount_paise * 10000 > config.chit_value_paise * config.max_discount_basis_points:
        raise ValueError("discount exceeds configured cap")
    commission = _exact_divide(config.chit_value_paise * config.commission_basis_points, 10000, "commission")
    if discount_paise < commission:
        raise ValueError("discount cannot be below commission")
    instalment = _exact_divide(config.chit_value_paise, len(members), "instalment")
    surplus = discount_paise - commission
    excluded = set(previously_prized) | {winner_id} if not config.dividend_to_prized_members else set()
    eligible = tuple(member for member in members if member not in excluded)
    if not eligible:
        raise ValueError("no members are eligible for the dividend")
    dividend = _exact_divide(surplus, len(eligible), "dividend")
    dues = []
    for index, member in enumerate(members, 1):
        member_dividend = dividend if member in eligible else 0
        base_due = instalment - member_dividend
        if base_due < 0:
            raise ValueError("dividend exceeds an eligible member's instalment")
        dues.append(MemberDue(member, member_dividend, base_due, index, base_due + index))
    if len({due.tagged_due_paise for due in dues}) != len(dues):
        raise ValueError("tagged amounts collide for this settlement")
    prize = config.chit_value_paise - discount_paise
    if sum(due.base_due_paise for due in dues) != prize + commission:
        raise ValueError("settlement invariant failed")
    return Settlement(winner_id, discount_paise, prize, commission, surplus, sum(d.tag_paise for d in dues), tuple(dues))
