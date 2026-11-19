import pytest
from fastapi.testclient import TestClient

from backend.stub import app
from test_contract import validator_for

client = TestClient(app)


def test_browser_cors_preflight():
    response = client.options("/message", headers={"Origin": "http://127.0.0.1:8000", "Access-Control-Request-Method": "POST"})
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:8000"


@pytest.mark.parametrize("status", ["verified", "duplicate", "wrong_amount", "needs_review"])
def test_each_result_is_contract_valid(status):
    response = client.post("/message", data={"sender": "member-7", "text": f"stub:{status}"})
    assert response.status_code == 200
    validator_for("message_response").validate(response.json())
    assert response.json()["bubbles"][0]["status"] == status


@pytest.mark.parametrize("kind", ["review_request", "reminder"])
def test_other_bubble_types(kind):
    response = client.post("/message", data={"sender": "foreman", "text": f"stub:{kind}"})
    validator_for("message_response").validate(response.json())
    assert response.json()["bubbles"][0]["type"] == kind


def test_image_upload_and_missing_input():
    response = client.post("/message", data={"sender": "member-7", "text": ""}, files={"image": ("test.png", b"sample", "image/png")})
    assert response.status_code == 200
    validator_for("message_response").validate(response.json())
    response = client.post("/message", data={"sender": "member-7"})
    assert response.status_code == 422
    validator_for("error_response").validate(response.json())


def test_review_and_controls():
    payload = {"actor": "foreman", "item_id": "review-1", "decision": "approve", "reason": "checked"}
    response = client.post("/review", json=payload)
    validator_for("review_response").validate(response.json())
    response = client.post("/review", json={**payload, "reason": "  "})
    assert response.status_code == 422
    validator_for("error_response").validate(response.json())
    for path, schema in [("/reminders/send", "reminders_response"), ("/demo/load", "demo_load_response")]:
        response = client.post(path, json={"actor": "foreman"})
        assert response.status_code == 200
        validator_for(schema).validate(response.json())


def test_state_contract_and_private_filtering():
    for query in ["role=foreman", "role=member&member_id=member-7", "role=member&member_id=member-8"]:
        response = client.get("/state?" + query)
        assert response.status_code == 200
        validator_for("state_response").validate(response.json())
    member = client.get("/state?role=member&member_id=member-8").json()
    assert not any(member[key] for key in ("flags", "audit_log", "statement", "private_bubbles"))
