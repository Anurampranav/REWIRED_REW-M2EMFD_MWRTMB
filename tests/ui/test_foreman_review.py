import copy
import json
import re
from pathlib import Path

from playwright.sync_api import expect


ROOT = Path(__file__).resolve().parents[2]
STATE_FIXTURE = ROOT / "data" / "fixtures" / "state_foreman.json"


def state_route(payload):
    body = json.dumps(payload)
    return lambda route: route.fulfill(status=200, content_type="application/json", body=body)


def test_command_hints_and_server_review_bubble(page, base_url):
    state = json.loads(STATE_FIXTURE.read_text(encoding="utf-8"))
    page.route(re.compile(r".*/state\?role=foreman$"), state_route(state))
    page.route(
        re.compile(r".*/message$"),
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"bubbles": [{
                "type": "review_request",
                "item_id": "review-from-server",
                "reason": "Check the transfer evidence.",
            }]}),
        ),
    )
    page.goto(f"{base_url}/chat/")
    page.get_by_label("Message or foreman command").fill(
        "Month 3, Name: Ravi K., Discount ₹12,000"
    )
    hints = page.get_by_test_id("command-hints")
    expect(hints).to_contain_text("Hints only")
    expect(hints).to_contain_text("Month 3")
    expect(hints).to_contain_text("Name Ravi K.")
    expect(hints).to_contain_text("Discount ₹12000")

    page.get_by_role("button", name="Send message").click()
    card = page.locator('[data-item-id="review-from-server"]')
    expect(card).to_be_visible()
    expect(card).to_contain_text("Check the transfer evidence.")
    expect(card.get_by_role("button", name="Approve")).to_be_visible()
    expect(card.get_by_role("button", name="Reject")).to_be_visible()


def test_review_reasons_are_required_and_payloads_match_contract(page, base_url):
    state = json.loads(STATE_FIXTURE.read_text(encoding="utf-8"))
    current_flags = list(state["flags"])
    review_calls = []

    def serve_state(route):
        snapshot = copy.deepcopy(state)
        snapshot["flags"] = copy.deepcopy(current_flags)
        route.fulfill(status=200, content_type="application/json", body=json.dumps(snapshot))

    def serve_review(route):
        payload = route.request.post_data_json
        review_calls.append(payload)
        current_flags[:] = [flag for flag in current_flags if flag["item_id"] != payload["item_id"]]
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"item_id": payload["item_id"], "decision": payload["decision"]}),
        )

    page.route(re.compile(r".*/state\?role=foreman$"), serve_state)
    page.route(re.compile(r".*/review$"), serve_review)
    page.goto(f"{base_url}/chat/")

    first_id = current_flags[0]["item_id"]
    first = page.locator('[data-item-id="' + first_id + '"]')
    first.get_by_test_id("review-reason-" + first_id).fill("Matched bank record.")
    first.get_by_test_id("review-approve-" + first_id).click()
    expect(first).to_have_count(0)
    assert len(review_calls) == 1
    assert review_calls[0] == {
        "item_id": first_id,
        "decision": "approve",
        "reason": "Matched bank record.",
        "actor": "foreman",
    }

    second_id = current_flags[0]["item_id"]
    second = page.locator('[data-item-id="' + second_id + '"]')
    second.get_by_test_id("review-reject-" + second_id).click()
    expect(second.get_by_text("Enter a reason before approving or rejecting.")).to_be_visible()
    assert len(review_calls) == 1
    second.get_by_test_id("review-reason-" + second_id).fill("Evidence does not match.")
    second.get_by_test_id("review-reject-" + second_id).click()
    expect(second).to_have_count(0)
    assert len(review_calls) == 2
    assert review_calls[1] == {
        "item_id": second_id,
        "decision": "reject",
        "reason": "Evidence does not match.",
        "actor": "foreman",
    }
