# T04 shared synthetic fixtures

All identifiers, names, UTRs, dates and evidence rows in this directory are
synthetic. `build_fixtures.py` deterministically regenerates the checked-in
files; it is not a production data loader.

- `state_foreman.json` validates as T01 `state_response`. It contains 20
  members, months 1–4, 80 ledger entries, flags, overdue entries and audit
  events.
- `result_examples.json` supplies every T01 response and bubble/result type.
- `financial_schedule.csv` holds the chit group, cycle, winner and financial
  calculation data that T01 deliberately does not model in JSON.
- `bank_evidence.csv` contains only independent synthetic evidence for
  `verified` ledger entries. It has no row for screenshot-only, pending,
  overdue, rejected or needs-review entries.

The fixture uses a ₹1,00,000 chit (10,000,000 paise), 20 members and a 5%
commission (500,000 paise). Each monthly expected pool reconciles exactly to
its prize plus commission. A screenshot-only payment is never marked
`verified`.
