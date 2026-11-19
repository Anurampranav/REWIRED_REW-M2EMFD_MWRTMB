# Rehearsal checklist

**Current status:** Draft only. The repository snapshot has no real `/state`, `/message`, verifier, ledger, late-fee, reminder, payout, or member-statement routes. Issues #24–#27 are open; #24–#27 are marked blocked on GitHub. Do not record a claimed end-to-end demonstration against a mocked success response.

## Before scheduling final rehearsals

- [ ] #24 merged and its real-flow acceptance tested.
- [ ] The relevant #25 late-fee, #26 pool/payout and #27 reminder paths merged and tested before demonstrating those scenes.
- [ ] #1 shared contract is present; #4 shared fixtures and #6/#7 scenario assets are present and validated.
- [ ] Confirm both frontends use their independent `config.js` values and communicate only through the shared backend contract.
- [ ] Confirm a synthetic bank CSV and masked synthetic screenshots are clearly identified as test data. Never introduce real member or bank information.
- [ ] Start backend from the repository root: `python -m uvicorn backend.main:app --reload`.
- [ ] Check `GET /health` returns `{"status":"ok"}`. Confirm the actual demo API routes respond before inviting the audience.
- [ ] Open `/chat/` and `/dashboard/` in separate tabs using the README local URL. Test desktop/projector and a phone-width viewport.
- [ ] Verify screen sharing shows only synthetic data. Close unrelated tabs and hide secrets/notifications.
- [ ] Confirm no real WhatsApp or bank integration is implied.

## Current checkout smoke sequence (does not count as final rehearsal)

- [ ] Open `/chat/`; observe the chat shell.
- [ ] Observe API unavailable because `/state` is not implemented.
- [ ] Open `/dashboard/`; observe the T20 placeholder and health connection only.
- [ ] Stop here. Do not claim message processing, screenshot verification, a populated ledger, reminder delivery, or payout unlock.

## Final action sequence after dependencies land

Fill in exact synthetic member names/IDs, amounts, dates, scenario filenames and expected status values from the merged fixtures/contracts before recording.

- [ ] Scene 1: problem framing, 0:00–0:35.
- [ ] Scene 2: synthetic chat and actual extracted fields/review action, 0:35–1:10.
- [ ] Scene 3: genuine, fake/unmatched, reused and wrong-amount cases; compare results with independent synthetic bank CSV, 1:10–2:10.
- [ ] Scene 4: actual due date, credit timestamp, configured late fee and reminder record; say no WhatsApp is sent, 2:10–2:50.
- [ ] Scene 5: show locked state with unpaid member, then backend-confirmed eligibility only if test data reaches it, 2:50–3:35.
- [ ] Scene 6: switch to member-facing view and verify displayed state from the same backend contract, 3:35–4:25.
- [ ] Scene 7: close with limitations and evidence model, 4:25–5:00.
- [ ] Record rehearsal 1 end-to-end and review every result against the application/API response.
- [ ] Fix issues; record rehearsal 2 end-to-end and review every result independently.
- [ ] Store recordings in an approved location, not in the repository if they contain personal or identifying information. Record safe references and review notes here.

## Recovery and known limits

- If `/health` fails, stop; restart backend and recheck.
- If a needed API route fails, show the observed error, return to the labelled conceptual workflow, and do not substitute a successful mock as product evidence.
- If synthetic data is missing, postpone the real-flow rehearsal. Do not make replacement bank statements that look real.
- If a screenshot result differs from the expected fixture result, capture the discrepancy and stop the scene. Never narrate the expected result as if it occurred.
- If a feature remains unimplemented, leave its scene explicitly pending and keep the final real-flow acceptance incomplete.

## Recording log

| Rehearsal | Date | Recording reference | Manual review complete | Differences/fixes |
| --- | --- | --- | --- | --- |
| 1 | Pending | Pending | No | Final real-flow dependencies are not merged. |
| 2 | Pending | Pending | No | Final real-flow dependencies are not merged. |
