"""Development entry point; business endpoints belong to their own issues."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="ChitMirror", version="0.0.1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Independent pages on one development origin avoid unnecessary CORS setup.
app.mount("/chat", StaticFiles(directory=ROOT / "chat-ui", html=True), name="chat")
app.mount("/dashboard", StaticFiles(directory=ROOT / "dashboard", html=True), name="dashboard")
