from __future__ import annotations

import copy
import json
import re
import time
from pathlib import Path

from playwright.sync_api import expect


ROOT = Path(__file__).resolve().parents[2]
STATE_FIXTURE = ROOT / "data" / "fixtures" / "state_foreman.json"


def test_ledger_grid_updates_cell_colour_within_two_seconds(page, base_url):
    initial = json.loads(STATE_FIXTURE.read_text(encoding="utf-8"))
    changed = copy.deepcopy(initial)
    entry = next(item for item in changed["ledger"] if item["member_id"] == "member-20" and item["month"] == 4)
    entry["status"] = "overdue"
    changed["counters"]["overdue"] += 1
    changed["overdue"].append({key: entry[key] for key in ("member_id", "month", "status", "amount_paise", "utr")})
    calls = 0

    def state_stub(route):
        nonlocal calls
        calls += 1
        payload = initial if calls == 1 else changed
        route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

    page.route(re.compile(r".*/state\?role=foreman$"), state_stub)
    page.goto(f"{base_url}/dashboard/")
    grid = page.get_by_test_id("ledger-grid")
    cell = page.get_by_test_id("ledger-cell-member-20-month-4")
    expect(grid.locator("tbody tr")).to_have_count(20)
    expect(grid.locator("thead th")).to_have_count(5)
    expect(cell).to_have_attribute("data-status", "pending")
    before = cell.evaluate("element => getComputedStyle(element).backgroundColor")

    started = time.monotonic()
    expect(cell).to_have_attribute("data-status", "overdue", timeout=1800)
    elapsed = time.monotonic() - started
    after = cell.evaluate("element => getComputedStyle(element).backgroundColor")

    assert elapsed < 2.0
    assert before != after
    expect(cell).to_have_attribute("title", re.compile(r"Overdue.*UTR: —"))
    assert calls >= 2

