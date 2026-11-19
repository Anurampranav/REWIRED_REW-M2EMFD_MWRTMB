# ChitMirror five-minute demo script

**Status:** Draft for the current repository snapshot (2026-11-19). This is a truthful product narrative and rehearsal plan, not acceptance of the final real-flow demo. Issues #24–#27 are still open; the checked-in backend has only `/health`. No screenshot verification, reminder, late-fee, payout, or populated dashboard flow can currently be demonstrated against the application.

**Presenter setup:** Start the FastAPI app using the README command, open `/chat/` and `/dashboard/` in separate tabs, and keep this script visible. The chat page expects `/state` and `/message`, which are not provided by this backend; expect an API-unavailable state. Do not route requests to a success stub and present it as a real backend result. Use the labelled conceptual diagram in `assets/workflow.svg` if the live flow is unavailable.

## Scene 1 — The problem (0:00–0:35, 35 seconds)

**Presenter:** “A chit group can have twenty members paying every month, but the evidence arrives in a dozen conversations. A foreman may be matching a name, month and amount across messages, screenshots and a manually maintained ledger. When a member asks whether a payment was counted, the group needs a clear record and a way to explain the decision.”

**Screen/action:** Show the title slide, then the problem slide. No app interaction is needed.

**Expected result:** Audience sees the coordination problem, not a claim that ChitMirror already processes live messages.

**API/backend:** None.

**If it fails:** Continue with the spoken example; these slides are static.

**Fallback:** Keep the synthetic chat clearly labelled as an illustration, not a captured user conversation.

## Scene 2 — Messy chat to structured information (0:35–1:10, 35 seconds)

**Presenter:** “Here is a synthetic example: ‘Ravi — March instalment ₹4,450.07 sent; foreman discount ₹550 noted.’ A useful workflow would extract the member, month, amount and discount, then ask the foreman to resolve ambiguity. The current repository has a chat composer and a sender picker, but no extraction service or working `/message` route, so this example is conceptual.”

**Screen/action:** Show the synthetic conversation on the workflow slide. Optionally open `/chat/` and point to the composer and sender picker; do not submit it expecting a processed response.

**Expected result:** Current page renders its chat shell, but displays an unavailable API message because `/state` is absent. No extracted fields appear.

**API/backend:** Chat JavaScript is configured to request `GET /state` and `POST /message`; the checked-in app implements neither.

**If it fails:** Stay on the slide and name the missing route plainly.

**Fallback:** Use the synthetic message as a problem illustration only. Do not stage a fake extraction result.

## Scene 3 — Payment verification (1:10–2:10, 60 seconds)

**Presenter:** “A screenshot is a claim, not proof that money reached the group account. The intended checks compare extracted payment details against independent bank CSV evidence. A matching credit may support verification; a UTR absent from the CSV, a reused UTR, or a wrong amount should be flagged for review or rejected according to the implemented rules. A screenshot that looks genuine can still be manipulated. Those are the scenarios the product must distinguish; this checkout does not contain the verifier, bank CSV, or screenshot set, so I cannot show real outcomes.”

**Screen/action:** Show the trust slide and the labelled scenario matrix. Keep all four cases labelled “expected test case — not run in this build.”

**Expected result:** Audience understands the evidence model and sees that no result is being asserted.

**API/backend:** No verification endpoint is present in this backend snapshot. The shared contract directory and #4 fixtures are absent from this checkout.

**If it fails:** Do not upload an actual or synthetic image expecting a verified status.

**Fallback:** Explain the independent-evidence principle with the conceptual workflow diagram. Never label an illustrative row as a bank transaction.

## Scene 4 — Late fees and reminders (2:10–2:50, 40 seconds)

**Presenter:** “A late-fee calculation needs a due date, a bank credit time and a configured fee rule. A reminder should be visible as a product event without implying that WhatsApp is connected. The repository does not yet include the #25 late-fee or #27 reminders implementation, so there is no calculation or reminder result to demonstrate.”

**Screen/action:** Show the operations slide, with the fee and reminder paths marked “pending dependency.”

**Expected result:** The planned inputs and missing implementation are clear.

**API/backend:** `POST /reminders/send` is described in the issue contract, but no such route is implemented in this checkout. No fee rule is present.

**If it fails:** No live action is expected; do not imply an outbound notification occurred.

**Fallback:** State the prerequisites in plain terms: due date, verified bank credit timestamp, configured fee policy, and a backend-generated reminder record.

## Scene 5 — Pool completion and payout unlock (2:50–3:35, 45 seconds)

**Presenter:** “A payout should unlock only when the backend confirms the required member verification state. If one member remains unpaid or unverified, the pool should remain locked. Issue #26 describes that rule, but it is still open and no ledger or payout endpoint exists in this checkout. There is no unlocked payout to show.”

**Screen/action:** Show the state diagram on the operations slide; point to the locked state as a rule, not a live application result.

**Expected result:** The audience sees a conceptual gate with the explicit label “planned; not implemented here.”

**API/backend:** No pool settlement or payout route is present.

**If it fails:** Do not stage a success state or edit data to suggest a payout is available.

**Fallback:** Explain the issue’s acceptance condition: locked with one unpaid member; unlock only after the backend confirms all required verifications.

## Scene 6 — Member experience (3:35–4:25, 50 seconds)

**Presenter:** “Members need to see what the group records: payment status, month, instalment, any applicable fee and the reason a payment needs review. The chat page and dashboard are separate static frontends, each configured with an API base URL. In this repository the dashboard is only a workspace placeholder, and the chat cannot load member state because `/state` is missing.”

**Screen/action:** Open `/dashboard/`, then `/chat/`. Show the dashboard placeholder and chat API-unavailable message without disguising either one.

**Expected result:** Two independent pages load. The dashboard reports backend health; it does not show a populated ledger. Chat indicates the missing API.

**API/backend:** Dashboard calls `GET /health`; chat calls `GET /state`. Only `/health` is implemented.

**If it fails:** Return to the slide and report the observed error.

**Fallback:** Use the workflow diagram to explain the intended member view, labelled conceptual. Do not claim member statements are available.

## Scene 7 — Closing pitch (4:25–5:00, 35 seconds)

**Presenter:** “ChitMirror is aimed at a practical problem: turning scattered payment claims into a transparent group record. Its differentiator is an evidence-based trust model: a screenshot starts a review; independent bank evidence is needed before verification. The current repository is an early UI shell, not an end-to-end verifier. The next milestone is to merge the verification and integration dependencies, then rehearse every result against the real backend.”

**Screen/action:** End on the closing slide. State the current implementation boundary and next milestone.

**Expected result:** A clear, credible product direction with no unsupported success claim.

**API/backend:** None.

**If it fails:** Close with the evidence rule and dependency status.

**Fallback:** Use the static closing slide; do not claim a production deployment, verified ledger, or completed payout.

## Rehearsal acceptance

Two full recordings and manual result checks are required by issue #30. None are included with this draft. Keep that acceptance item pending until two recordings exist and each scripted outcome has been checked against a real application build after #24 and relevant #25–#27 paths are merged.
