# ChitMirror

Screenshot in, verified ledger out. A four-person, six-hour hackathon project.
A payment screenshot is a claim; bank CSV evidence is required for verification.

## Run locally

Use Python 3.12 or newer. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m uvicorn backend.main:app --reload
```

On macOS/Linux use `.venv/bin/python` in place of `.\.venv\Scripts\python`.
Open http://127.0.0.1:8000/chat/ and http://127.0.0.1:8000/dashboard/.
API docs: http://127.0.0.1:8000/docs. No Node build step is required.

Both pages call the backend directly. Each owns its `config.js`; set
`window.CHITMIRROR_API_BASE` to switch its backend URL (empty means same origin).
The shared API contract and examples are in `contracts/`. A separate canned
stub is available for UI work; it does not perform payment verification.
Separate origins require backend CORS configuration.

## Stub API

Start the stub with `python -m uvicorn backend.stub:app --port 8001`.
Start the frontend server with `CHITMIRROR_API_BASE` set to the desired backend
URL (empty selects the same origin). For example, in PowerShell:

```powershell
$env:CHITMIRROR_API_BASE = "http://127.0.0.1:8001"
.\.venv\Scripts\python -m uvicorn backend.main:app --reload
```

The stub permits the local frontend origins on port 8000; set its
`CHITMIRROR_ALLOWED_ORIGINS` to a comma-separated list for other origins. For
canned message results, send `stub:verified`, `stub:duplicate`,
`stub:wrong_amount`, `stub:needs_review`, `stub:review_request`, or
`stub:reminder` in the multipart text field. Other messages return a text bubble.
Responses use T01 examples until T04's shared fixtures are available. The stub
does not persist state, actually send reminders, reset data, or verify screenshots.

## Team folders

| Owner | Workspace |
| --- | --- |
| A | Reader and verification modules under `backend/`; tests under `tests/` |
| B | `backend/`: contract, services, storage, API and engine integration |
| C | `chat-ui/`: independent chat page; demo script and pitch |
| D | `dashboard/` and `data/`: independent dashboard, fixtures and scenario |

The existing `chit_engine.py` and `chitmirror_final.mermaid` were not present in
the empty repository. Their owner should supply the originals; do not recreate
the completed engine or diagram. Integration belongs to T09.

## Tests

```powershell
.\.venv\Scripts\python -m pytest tests/test_app.py
.\.venv\Scripts\python -m playwright install chromium
```

With the development server running, in a second terminal:

```powershell
.\.venv\Scripts\python -m pytest tests/ui --base-url http://127.0.0.1:8000
```

CI runs backend checks and Chromium smoke tests. Manual checklist for UI PRs:
open both pages, confirm backend connection, inspect a phone-width chat and
projector-width dashboard, and confirm a stopped backend produces a readable error.

## Working agreement

One issue and branch per person (`T##-short-name`), maximum four issues in flight.
PRs reference `Closes #<issue>` and get a teammate review; keep main green.
Merge dependencies first unless the issue permits fixtures/stubs. Freeze at
hour 4:30; then only bug fixes. Follow the issue plan for business features.

Copy `.env.example` to `.env` when needed. Keys are blank and no provider calls
are made by this scaffold. Future services must load their environment explicitly;
the current app does not read `.env`.
