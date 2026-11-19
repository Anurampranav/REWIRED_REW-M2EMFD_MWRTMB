# ChitMirror Roadmap and Open Questions

**Tracking issue:** [#33 — T33 Roadmap and open questions](https://github.com/Dhyan-S-Kanapadi/REWIRED_REW-M2EMFD_MWRTMB/issues/33)  
**Milestone:** M3 Demo  
**Scope:** Documentation and tracking only

## Product direction

ChitMirror is intended to turn a payment claim into a transparently recorded outcome:

> Screenshot or evidence upload → independent verification → verified ledger output

A screenshot is a claim. It does not independently prove that a bank transaction occurred. Verification requires independent bank CSV evidence. Missing, invalid, or inconsistent evidence must not be represented as verified.

This describes the product direction and trust boundary; it does not claim that every step is currently implemented.

## Architecture boundaries

- The Chat UI and Dashboard UI remain independent applications.
- Each frontend communicates with the backend through the shared API contract.
- Shared API schemas define request and response formats.
- Frontend-specific UI logic stays within its own application; there is no direct frontend-to-frontend communication.
- Demonstrations use synthetic or masked data only.
- No real bank or WhatsApp service is connected within this scope.

## Deferred features

These items are out of scope for the current M3 Demo milestone. Listing them here does not imply they are implemented. Reconsider them only after explicit approval and assignment to a future milestone.

1. Voice-note bidding.
2. OTP-based login.
3. PDF or CSV statement export.
4. Group setup wizard.
5. Reports and analytics.
6. Members trend screen.
7. Gate role and related access workflows.
8. Real bank integration.
9. Real payment gateway integration.
10. Real WhatsApp group membership integration.
11. Legal chit registration.

## Open product and business questions

| Question | Current status | Decision needed |
| --- | --- | --- |
| What is the legally applicable maximum discount cap? | Unverified | Confirm against applicable law and the group agreement before treating a cap as a rule. |
| Is the engine’s 40% maximum discount placeholder correct? | Unverified placeholder | Verify independently; do not present 40% as a confirmed legal limit. |
| Do prized members receive dividends? | Configurable; business decision pending | Decide and document the group policy before using it as a final rule. |
| What happens in a no-bid month? | Product decision pending | Define the allowed outcome and its effect on settlement before implementation. |

No legal determination is made by this document.

## Evidence and demonstration rules

- An uploaded screenshot is a payment claim, not independent proof of payment.
- Independent bank CSV evidence is required to verify a transaction.
- Invalid, missing, or inconsistent evidence must not be treated as verified.
- Demonstrations use synthetic or masked data; synthetic records must be labelled synthetic.
- Do not connect to real banking, payment gateway, or WhatsApp services in this scope.
- Never describe an upload as a successful payment merely because the file was accepted.

## Roadmap

### Current milestone: M3 Demo

- Maintain the shared backend contract.
- Keep both frontends independent and use the contract as their only communication boundary.
- Document exclusions and unresolved product decisions.
- Validate only the demo paths that are actually implemented, using synthetic or masked data.
- Preserve the screenshot-versus-independent-evidence trust boundary in product copy and demonstrations.

### Deferred

All features listed under **Deferred features** remain outside the current scope until explicitly approved and assigned to a future milestone.

### Pending decisions

Resolve the four questions above before treating the related business rules as final. In particular, the 40% placeholder must remain labelled unverified until the applicable law and group agreement are reviewed by the responsible parties.

## Acceptance checklist

- [x] All 11 out-of-scope features are listed.
- [x] All four open questions are listed with their current status.
- [x] The 40% discount cap is explicitly marked unverified and not a confirmed legal limit.
- [x] Independent bank CSV evidence is required for transaction verification.
- [x] Synthetic or masked demonstration data is required.
- [x] No real bank, gateway, or WhatsApp integration is implied.
- [x] The frontends are documented as independent applications.
- [x] The shared backend contract is documented as their communication boundary.
- [x] Documentation manually reviewed against issue #33 and the current implementation.
- [ ] Applicable CI checks pass.
- [ ] PR reviewed and merged into healthy `main`.

## Scope control

This issue tracks roadmap decisions and documents boundaries. It does not authorize implementing deferred features, changing payment verification, making legal conclusions, or adding external integrations.

