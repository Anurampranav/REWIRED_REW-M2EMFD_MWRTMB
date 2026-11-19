import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

CONTRACTS = Path(__file__).resolve().parent.parent / "contracts"
SCHEMA = json.loads((CONTRACTS / "schemas.json").read_text(encoding="utf-8"))
EXAMPLES = json.loads((CONTRACTS / "examples.json").read_text(encoding="utf-8"))


def validator_for(name):
    return Draft202012Validator({**SCHEMA, "$ref": f"#/$defs/{name}"}, format_checker=FormatChecker())


def test_schema_and_all_examples_validate():
    Draft202012Validator.check_schema(SCHEMA)
    assert set(EXAMPLES) == set(SCHEMA["$defs"]) - {"money", "utr", "status", "bubble", "member", "ledger_entry", "flag", "audit"}
    for name, examples in EXAMPLES.items():
        assert examples
        for example in examples:
            validator_for(name).validate(example)


@pytest.mark.parametrize("reason", ["", "  ", "\n"])
def test_review_requires_meaningful_reason(reason):
    request = {**EXAMPLES["review_request"][0], "reason": reason}
    assert list(validator_for("review_request").iter_errors(request))


def test_invalid_utr_and_fractional_money_are_rejected():
    bubble = EXAMPLES["message_response"][0]["bubbles"][1]
    assert list(validator_for("bubble").iter_errors({**bubble, "utr": "123"}))
    assert list(validator_for("bubble").iter_errors({**bubble, "amount_paise": 4450.07}))
