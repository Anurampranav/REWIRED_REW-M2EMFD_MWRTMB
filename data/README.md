# T06 demo chit and evidence fixtures

Everything in this folder is synthetic. `demo_chit.json` defines the ₹1,00,000 chit, 20 members, 5% commission, ₹5,000 base instalment, 5 November 2026 due date, and a non-routable `.invalid` UPI placeholder. Money fields ending in `_paise` are integer paise, matching the shared T01 contract.

`bank.csv` contains one settled row per member. Its 12-digit UTRs are invented test values; all rows are tagged `monthly_instalment`, with scenario tags for the genuine, reused-source, wrong-amount-source, and late-payer rows. The fake UTR appears only in `scenarios.json`, never in the bank evidence.

`scenarios.json` gives each synthetic screenshot fixture's fields and exact expected result card and ledger action:

| Screenshot fixture | Expected result | Ledger |
| --- | --- | --- |
| `receipt-genuine-on-time` | `verified` | Record on time |
| `receipt-reused-utr` | `duplicate` | Do not add a second payment |
| `receipt-fake-utr` | `needs_review`; return `utr: null` | Do not record |
| `receipt-wrong-amount` | `wrong_amount` | Do not record |
| `receipt-late-payer` | `verified`, timing `late` | Record and flag late; fee stays unset |

The late case matches CSV evidence dated after the due date. No late-fee policy is invented. The manifest maps screenshot IDs to scenarios; this issue provides screenshot claims and metadata, not payment images.

Run `python -m scripts.validate_demo_data` from the repository root. It checks the row count, 12-digit unique UTRs, all 20 members, tagged instalment amounts, receiver, planted failures, manifest links and late-payment rule.

