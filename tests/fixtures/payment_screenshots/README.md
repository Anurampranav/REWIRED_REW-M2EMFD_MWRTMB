# Payment screenshot test dataset

## Purpose

This dataset drives ChitMirror screenshot-verification tests. An image is a
**claim**, never independent bank confirmation. The expected result for every
image is derived from the backend contract in `contracts/` plus independent bank
CSV evidence, not from the screenshot alone.

**Dependency status:** Issue #6 is open/unmerged. There is no merged demo chit,
bank CSV or due-date rule in this checkout. Everything here is labelled
`PROVISIONAL` and uses the fictional CSV
`PROVISIONAL_bank_evidence_T06_NOT_MERGED.csv` and due date `2026-03-10`.
These are test doubles, not a replacement for the #6 scenario. Regenerate and
revalidate against the real #6 assets after #6 merges. No genuine user
contributions are included.

## Current contents

| Category | Images |
|---|---:|
| genuine | 12 |
| fake | 8 |
| reused | 7 |
| wrong_amount | 7 |
| late | 6 |
| **Total** | **40** |

All 40 images are synthetic mock payment interfaces with a prominent
`SYNTHETIC — TEST ONLY` watermark. There are **0 genuine masked contributions**
so far. Each of the four app layouts is represented in every category.

| Layout | Images |
|---|---:|
| gpay | 11 |
| phonepe | 10 |
| paytm | 10 |
| bank_app | 9 |

## Folder structure

```text
tests/fixtures/payment_screenshots/
├── README.md
├── manifest.json
├── PROVISIONAL_bank_evidence_T06_NOT_MERGED.csv
├── genuine/{gpay,phonepe,paytm,bank_app}/
├── fake/{gpay,phonepe,paytm,bank_app}/
├── reused/{gpay,phonepe,paytm,bank_app}/
├── wrong_amount/{gpay,phonepe,paytm,bank_app}/
└── late/{gpay,phonepe,paytm,bank_app}/
```

Filenames use `<category>/<app_layout>/t07-<category>-<layout>-<nnn>.png`.

## Manifest fields

| Field | Meaning |
|---|---|
| `image_id` | Stable unique identifier for the fixture. |
| `filename` | Path relative to this folder; folder names must match `category`/`app_layout`. |
| `app_layout` | One of `gpay`, `phonepe`, `paytm`, `bank_app`. |
| `category` | One of `genuine`, `fake`, `reused`, `wrong_amount`, `late`. |
| `synthetic` | `true` for generated mock images; `false` only for real masked contributions. |
| `expected_status` | Contract result-card status: `verified`, `duplicate`, `wrong_amount` or `needs_review`. |
| `expected_reason` | Contract-compatible reason text for that result. |
| `expected_amount` | Authoritative amount in **paise** from independent bank evidence, including wrong-amount cases. |
| `claimed_amount` | Amount visible in the screenshot claim (differs from `expected_amount` for wrong-amount cases). |
| `expected_month` | Chit month under test. |
| `expected_utr_reference` | 12-digit reference claimed by the screenshot; for `fake` this is deliberately absent from the CSV. It is not the result-card UTR when the backend nullifies an unmatched reference. |
| `corresponding_bank_csv_reference` | CSV used to check the claim, including for `fake` cases where it proves the UTR is absent. |
| `scenario_id` | Links the fixture to a scenario; provisional IDs are prefixed `PROVISIONAL-T06-`. |
| `claimed_date` | Date visible in the claim; `late` cases must be after the configured due date. |

Top-level fields record categories, layouts, allowed statuses, the provisional
due date and the dependency caveat.

## Contributing genuine screenshots

1. Contribute **five screenshots from your own phone**, never from someone
   else's account.
2. Give explicit written permission in the PR description to use the images for
   ChitMirror testing, and state which device/app layout produced them.
3. Mask or crop **all** names, account numbers, phone numbers, UPI handles, QR
   codes, balances, transaction credentials, addresses and any other personal
   or financial detail. Keep only the amount, reference, date and app-style
   layout needed by the test.
4. Place masked images under `genuine/<app_layout>/` and add one manifest entry
   per image with `synthetic: false` and a real `scenario_id` from the merged
   #6 plan.
5. Add the independent bank CSV row that confirms the claim. A screenshot alone
   must never produce `verified`.
6. Never commit an unmasked financial or personal image, even by accident. If
   in doubt, regenerate a synthetic fixture instead.

## Synthetic-data rules

- Use `scripts/generate_synthetic_screenshots.py` or the helper in
  `scripts/screenshot_fixture_tools.py`; output is deterministic.
- Every synthetic image must carry the visible `SYNTHETIC — TEST ONLY`
  watermark, PNG metadata `Synthetic: true`, and a `Watermark` metadata label.
- Use fictional references and amounts only. Do not imitate a real bank's
  official proof-of-payment document, use real UPI IDs, QR codes, credentials
  or customer details, or create a fake receipt intended to pass as real.
- Synthetic images are clearly mock app interfaces and are never accepted as
  independent bank evidence.

## Validation and tests

From the repository root:

```powershell
python scripts/validate_screenshot_manifest.py
python -m pytest tests/test_screenshot_dataset.py
python -m pytest tests/test_app.py tests/test_contract.py tests/test_screenshot_dataset.py
python -m pytest
```

The validator checks JSON validity, image existence, one entry per image,
unique IDs and filenames, category/layout coverage, the 40-image minimum,
contract statuses and reasons, synthetic labelling and visible watermarks, CSV
references and evidence consistency, and personal-information exposure in
synthetic metadata. It exits nonzero with one line per problem.

Related regression assets: `tests/test_contract.py` validates the shared #1
schemas, `tests/test_app.py` covers backend health and both independent
frontends, and `tests/ui/` holds browser smoke tests. Both frontends call the
same backend contract; this dataset adds no frontend-to-frontend traffic and
changes no production API behaviour.
