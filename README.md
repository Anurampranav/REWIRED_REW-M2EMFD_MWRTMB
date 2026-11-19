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
The backend currently exposes only `/health`; the shared API contract and
examples are in `contracts/`, and implementation of the stub remains T03 work.
Separate origins require backend CORS configuration.

## Team folders

| Owner | Workspace |
| --- | --- |
| A | Reader and verification modules under `backend/`; tests under `tests/` |
| B | `backend/`: contract, services, storage, API and engine integration |
| C | `chat-ui/`: independent chat page; demo script and pitch |
| D | `dashboard/` and `data/`: independent dashboard, fixtures and scenario |

The original engine and diagram were not present in the repository. A replacement
pure settlement engine is provided in `backend/chit_engine.py`; the diagram is
still missing. Amounts are integer paise. The engine rejects fractional-paise
commission, instalments or dividends rather than silently rounding. Tags are
additional reconciliation amounts and their sum is reported separately; how
to account for or return tag surplus is an open product decision. No dividend
or payout is posted by settlement. If prized members are excluded, the caller
must supply prior winners; the current winner is also excluded. This policy and
the maximum discount require confirmation against the chit agreement.

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
