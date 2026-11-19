"""Group settings; monetary values use integer paise and rates use basis points."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GroupConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    chit_value_paise: int = Field(gt=0)
    member_ids: tuple[str, ...] = Field(min_length=1)
    commission_basis_points: int = Field(ge=0, le=10000)
    due_date: date
    late_fee_type: Literal["flat", "percentage"]
    # Flat: paise. Percentage: basis points (100 = 1%).
    late_fee_value: int = Field(ge=0)
    max_discount_basis_points: int = Field(ge=0, le=10000)
    dividend_to_prized_members: bool

    @model_validator(mode="after")
    def validate_group(self):
        if any(not member.strip() for member in self.member_ids):
            raise ValueError("member IDs must not be blank")
        if len(set(self.member_ids)) != len(self.member_ids):
            raise ValueError("member IDs must be unique")
        return self
