# ChitMirror API contract (T01)

`schemas.json` is JSON Schema draft 2020-12; `examples.json` maps each
definition to example instances. Amounts are integer paise; timestamps are RFC
3339 with offsets. IDs are opaque strings. JSON requests and responses use
`application/json` unless specified below. Successful responses are 200;
validation errors are 422, missing items 404, conflicting operations 409, and
server failures 500, all using `error_response`.

| Endpoint | Input | Output |
| --- | --- | --- |
| POST /message | multipart/form-data: `sender`, `text`, optional binary `image` (PNG/JPEG/WebP); at least text or image must be present | `message_response` |
| POST /review | `review_request`; foreman only, nonblank reason | `review_response` |
| GET /state?role=foreman | no body | `state_response` |
| GET /state?role=member&member_id=member-7 | no body; member_id required | `state_response` |
| POST /reminders/send | `reminders_request`; foreman only | `reminders_response` |
| POST /demo/load | `demo_load_request`; foreman only; demo environment only | `demo_load_response` |

Demo identities are selectors, not authentication. The backend filters state:
members receive the group ledger, their own statement and private bubbles; flags,
overdue details and audit log are empty for members. Foreman receives all panels;
statement and private bubbles are empty unless a member context is requested.
Private bubbles must never be broadcast to other members. This demo has no OTP
and this selector cannot enforce privacy against a malicious caller.

An image is a claim, not proof. `verified` requires matching independent bank
evidence and all checks. Not found, low confidence or reader disagreement means
`needs_review`; duplicate and wrong amount are distinct results. A manual
approval must remain auditable and distinguishable from bank verification.
T15 keeps the detailed OCR/check classification record in backend audit handling;
the public message response remains a `result_card` so both frontends consume
one shared contract. A result is `verified` only after a sufficiently confident
claim passes every deterministic check and matches independent settled bank
evidence. OCR confidence alone never proves payment.
Use member IDs as `sender`, and `foreman` for the foreman. Message bubbles are
returned only to that sender; review requests are retrieved through the foreman
state flag queue. An invalid UTR is represented as null in the result card and
explained in `reason` (raw reader output is not exposed by this contract).

The API base URL is configurable independently in each UI. The stub and real
API must implement this same contract. T04 expands examples into shared
20-member/four-month fixtures. `GET /state` is polled every 1–2 seconds. Demo
loading resets demo data, so must not be enabled against real records. Actor
fields identify the selector for demo audit purposes, not authenticated users.
