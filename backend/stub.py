"""Disposable canned API for frontend development; never verifies payments."""

import copy
import json
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="ChitMirror stub")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CHITMIRROR_ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(","), allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
EXAMPLES = json.loads((Path(__file__).resolve().parent.parent / "contracts" / "examples.json").read_text(encoding="utf-8"))


def error(code, message, status):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return error("invalid_request", "Invalid request.", 422)


class Actor(BaseModel):
    actor: str = Field(min_length=1)


class Review(Actor):
    item_id: str = Field(min_length=1)
    decision: str
    reason: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/message")
async def message(sender: str = Form(..., min_length=1), text: str = Form(""), image: UploadFile | None = File(None)):
    if not text.strip() and image is None:
        return error("invalid_request", "Text or image is required.", 422)
    if image and image.content_type not in {"image/png", "image/jpeg", "image/webp"}:
        return error("invalid_request", "Unsupported image type.", 422)
    bubbles = EXAMPLES["message_response"][0]["bubbles"]
    # Deterministic selectors give frontend teams every card without real verification.
    choices = {bubble["status"]: bubble for bubble in bubbles if bubble["type"] == "result_card"}
    key = text.strip().removeprefix("stub:")
    if key in choices:
        return {"bubbles": [choices[key]]}
    if key == "review_request":
        return {"bubbles": [next(b for b in bubbles if b["type"] == "review_request")]}
    if key == "reminder":
        return {"bubbles": [next(b for b in bubbles if b["type"] == "reminder")]}
    return {"bubbles": [bubbles[0]]}


@app.post("/review")
def review(payload: Review):
    if payload.actor != "foreman" or payload.decision not in {"approve", "reject"} or not payload.reason.strip():
        return error("invalid_request", "Foreman, valid decision and reason are required.", 422)
    return {"item_id": payload.item_id, "decision": payload.decision}


@app.get("/state")
def state(role: str, member_id: str | None = None):
    if role not in {"foreman", "member"} or (role == "member" and not member_id):
        return error("invalid_request", "Valid role and member ID are required.", 422)
    result = copy.deepcopy(EXAMPLES["state_response"][0])
    if role == "member":
        result.update(flags=[], overdue=[], audit_log=[])
        if member_id != "member-7":
            result.update(statement=[], private_bubbles=[])
    else:
        result.update(statement=[], private_bubbles=[])
    return result


@app.post("/reminders/send")
def reminders(payload: Actor):
    if payload.actor != "foreman":
        return error("invalid_request", "Foreman required.", 422)
    return EXAMPLES["reminders_response"][0]


@app.post("/demo/load")
def demo_load(payload: Actor):
    if payload.actor != "foreman":
        return error("invalid_request", "Foreman required.", 422)
    return EXAMPLES["demo_load_response"][0]
