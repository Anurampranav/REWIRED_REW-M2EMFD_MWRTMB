"""Development entry point; business endpoints belong to their own issues."""

from pathlib import Path
import json
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="ChitMirror", version="0.0.1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config.js")
def frontend_config():
    api_base = os.environ.get("CHITMIRROR_API_BASE", "")
    return Response(f"window.CHITMIRROR_API_BASE = {json.dumps(api_base)};", media_type="application/javascript", headers={"Cache-Control": "no-store"})


# Independent pages on one development origin avoid unnecessary CORS setup.
app.mount("/chat", StaticFiles(directory=ROOT / "chat-ui", html=True), name="chat")
app.mount("/dashboard", StaticFiles(directory=ROOT / "dashboard", html=True), name="dashboard")
