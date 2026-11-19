import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from screenshot_fixture_tools import (
    ALLOWED_STATUSES,
    APP_LAYOUTS,
    CATEGORIES,
    DATASET_DIR,
    IMAGE_SUFFIXES,
    MANIFEST_NAME,
    MIN_IMAGES,
    REASON_BY_CATEGORY,
    REQUIRED_ENTRY_FIELDS,
    STATUS_BY_CATEGORY,
    WATERMARK_PIXEL,
    WATERMARK_TEXT,
    count_pixel,
    find_personal_information,
    read_png,
)

MIN_WATERMARK_PIXELS = 200
CSV_COLUMNS = {"utr", "amount_paise", "month", "credit_date"}


def load_manifest(manifest_path: Path):
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [f"cannot read manifest {manifest_path}: {exc}"]
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [f"manifest JSON is invalid: {exc}"]
    if not isinstance(manifest, dict):
        return None, ["manifest JSON must be an object"]
    return manifest, []


def load_bank_rows(path: Path):
    errors = []
    try:
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            missing = CSV_COLUMNS - set(reader.fieldnames or [])
            if missing:
                return {}, [f"bank CSV {path.name} is missing columns: {', '.join(sorted(missing))}"]
            rows = {}
            for line_number, row in enumerate(reader, start=2):
                utr = (row.get("utr") or "").strip()
                if not utr:
                    continue
                if utr in rows:
                    errors.append(f"bank CSV {path.name} has duplicate UTR {utr} on line {line_number}")
                rows[utr] = row
            return rows, errors
    except OSError as exc:
        return {}, [f"cannot read bank CSV {path.name}: {exc}"]


def validate(manifest_path: Path = DATASET_DIR / MANIFEST_NAME) -> list[str]:
    manifest, errors = load_manifest(manifest_path)
    if errors:
        return errors
    root = manifest_path.resolve().parent
    entries = manifest.get("images")
    if not isinstance(entries, list):
        return ["manifest field 'images' must be a list"]

    due_date = manifest.get("provisional_due_date")
    if not isinstance(due_date, str) or not due_date:
        errors.append("manifest field 'provisional_due_date' is required")
        due_date = ""

    allowed_utrs = {
        entry.get("expected_utr_reference")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("expected_utr_reference"), str)
    }
    listed_files = []
    image_ids = []
    filenames = []
    csv_cache: dict[str, dict[str, dict[str, str]]] = {}

    for index, entry in enumerate(entries):
        label = f"images[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label}: entry must be an object")
            continue
        image_id = entry.get("image_id")
        if isinstance(image_id, str) and image_id:
            image_ids.append(image_id)
            label = f"images[{index}] ({image_id})"

        for field in REQUIRED_ENTRY_FIELDS:
            if field not in entry:
                errors.append(f"{label}: missing required field '{field}'")

        category = entry.get("category")
        layout = entry.get("app_layout")
        if category not in CATEGORIES:
            errors.append(f"{label}: invalid category {category!r}; expected one of {', '.join(CATEGORIES)}")
        if layout not in APP_LAYOUTS:
            errors.append(f"{label}: invalid app_layout {layout!r}; expected one of {', '.join(APP_LAYOUTS)}")

        status = entry.get("expected_status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{label}: invalid expected_status {status!r}; expected one of {', '.join(ALLOWED_STATUSES)}")
        elif category in STATUS_BY_CATEGORY and status != STATUS_BY_CATEGORY[category]:
            errors.append(f"{label}: expected_status {status!r} does not match category {category!r}")

        reason = entry.get("expected_reason")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"{label}: missing or empty expected_reason")
        elif category in REASON_BY_CATEGORY:
            expected_reason = (
                f"Expected {entry.get('expected_amount')} paise."
                if category == "wrong_amount"
                else REASON_BY_CATEGORY[category]
            )
            if reason != expected_reason:
                errors.append(f"{label}: expected_reason {reason!r} does not match {expected_reason!r}")

        amount = entry.get("expected_amount")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            errors.append(f"{label}: expected_amount must be a positive integer in paise")
        month = entry.get("expected_month")
        if not isinstance(month, int) or isinstance(month, bool) or month < 1:
            errors.append(f"{label}: expected_month must be a positive integer")

        utr = entry.get("expected_utr_reference")
        if not isinstance(utr, str) or len(utr) != 12 or not utr.isdigit():
            errors.append(f"{label}: expected_utr_reference must be a 12-digit string")
        if not isinstance(entry.get("synthetic"), bool):
            errors.append(f"{label}: synthetic must be a boolean")
        if not isinstance(entry.get("scenario_id"), str) or not entry["scenario_id"].strip():
            errors.append(f"{label}: scenario_id must be a non-empty string")

        claimed_amount = entry.get("claimed_amount")
        if claimed_amount is not None:
            if not isinstance(claimed_amount, int) or isinstance(claimed_amount, bool) or claimed_amount <= 0:
                errors.append(f"{label}: claimed_amount must be a positive integer in paise")
            elif isinstance(amount, int):
                if category == "wrong_amount" and claimed_amount == amount:
                    errors.append(f"{label}: wrong_amount case must claim an amount different from expected_amount")
                if category != "wrong_amount" and claimed_amount != amount:
                    errors.append(f"{label}: claimed_amount must equal expected_amount for category {category!r}")

        claimed_date = entry.get("claimed_date")
        if category == "late" and (not isinstance(claimed_date, str) or not claimed_date):
            errors.append(f"{label}: late category requires claimed_date")
        elif isinstance(claimed_date, str) and claimed_date and due_date:
            if category == "late" and claimed_date <= due_date:
                errors.append(f"{label}: claimed_date {claimed_date} is not after due date {due_date}")
            if category == "genuine" and claimed_date > due_date:
                errors.append(f"{label}: genuine claimed_date {claimed_date} is after due date {due_date}")

        csv_ref = entry.get("corresponding_bank_csv_reference")
        csv_rows = None
        if not isinstance(csv_ref, str) or not csv_ref.strip():
            errors.append(f"{label}: corresponding_bank_csv_reference is required")
        else:
            if csv_ref not in csv_cache:
                csv_path = root / csv_ref
                if not csv_path.is_file():
                    csv_cache[csv_ref] = None
                    errors.append(f"{label}: bank CSV reference points to a missing file: {csv_ref}")
                else:
                    rows, csv_errors = load_bank_rows(csv_path)
                    csv_cache[csv_ref] = rows
                    errors.extend(f"{label}: {csv_error}" for csv_error in csv_errors)
            csv_rows = csv_cache[csv_ref]
            if csv_rows is not None and isinstance(utr, str):
                if category == "fake":
                    if utr in csv_rows:
                        errors.append(f"{label}: fake UTR {utr} unexpectedly exists in bank CSV {csv_ref}")
                elif category in {"genuine", "reused", "wrong_amount", "late"} and utr not in csv_rows:
                    errors.append(f"{label}: UTR {utr} is absent from bank CSV {csv_ref}")
                elif utr in csv_rows:
                    row = csv_rows[utr]
                    try:
                        bank_amount = int(row["amount_paise"])
                    except (KeyError, TypeError, ValueError):
                        errors.append(f"{label}: bank CSV amount for UTR {utr} is not an integer")
                    else:
                        if isinstance(amount, int) and bank_amount != amount:
                            errors.append(f"{label}: bank CSV amount {bank_amount} differs from expected_amount {amount}")
                    try:
                        bank_month = int(row["month"])
                    except (KeyError, TypeError, ValueError):
                        errors.append(f"{label}: bank CSV month for UTR {utr} is not an integer")
                    else:
                        if isinstance(month, int) and bank_month != month:
                            errors.append(f"{label}: bank CSV month {bank_month} differs from expected_month {month}")
                    bank_date = row.get("credit_date", "")
                    if category == "late" and bank_date <= due_date:
                        errors.append(f"{label}: bank credit date {bank_date} is not after due date {due_date}")

        filename = entry.get("filename")
        if not isinstance(filename, str) or not filename:
            errors.append(f"{label}: filename is required")
        else:
            relative = Path(filename)
            filenames.append(relative.name)
            if relative.is_absolute() or ".." in relative.parts:
                errors.append(f"{label}: filename must be a relative path: {filename}")
            else:
                listed_files.append(relative.as_posix())
                image_path = root / relative
                if not image_path.is_file():
                    errors.append(f"{label}: manifest entry points to a missing image file: {filename}")
                else:
                    if image_path.suffix.lower() not in IMAGE_SUFFIXES:
                        errors.append(f"{label}: unsupported image extension: {image_path.suffix}")
                    if len(relative.parts) >= 2 and (relative.parts[0] != category or relative.parts[1] != layout):
                        errors.append(f"{label}: filename folder {relative.parts[0]}/{relative.parts[1]} does not match category/layout")
                    if image_path.suffix.lower() == ".png":
                        try:
                            image = read_png(image_path)
                        except (OSError, ValueError) as exc:
                            if entry.get("synthetic") is True:
                                errors.append(f"{label}: cannot inspect synthetic image: {exc}")
                        else:
                            marker = image.texts.get("Synthetic", "")
                            if marker.lower() == "true" and entry.get("synthetic") is not True:
                                errors.append(f"{label}: image is marked synthetic but manifest says otherwise")
                            if entry.get("synthetic") is True:
                                if marker.lower() != "true":
                                    errors.append(f"{label}: synthetic image is not marked synthetic in its metadata")
                                if image.texts.get("Watermark") != WATERMARK_TEXT:
                                    errors.append(f"{label}: synthetic image is missing the test-only watermark label")
                                if count_pixel(image, WATERMARK_PIXEL) < MIN_WATERMARK_PIXELS:
                                    errors.append(f"{label}: synthetic image is missing a visible test-only watermark")
                                for finding in find_personal_information(image.texts, allowed_utrs):
                                    errors.append(f"{label}: {finding}")
                    elif entry.get("synthetic") is True:
                        errors.append(f"{label}: cannot verify watermark on non-PNG synthetic image")

    for image_id, count in sorted(Counter(image_ids).items()):
        if count > 1:
            errors.append(f"duplicate image_id '{image_id}' appears {count} times")
    for filename, count in sorted(Counter(filenames).items()):
        if count > 1:
            errors.append(f"duplicate filename '{filename}' appears {count} times")

    disk_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    }
    for filename, count in sorted(Counter(listed_files).items()):
        if count > 1:
            errors.append(f"image '{filename}' has {count} manifest entries; expected exactly one")
    for filename in sorted(disk_files - set(listed_files)):
        errors.append(f"image on disk has no manifest entry: {filename}")

    present_categories = {entry.get("category") for entry in entries if isinstance(entry, dict)}
    present_layouts = {entry.get("app_layout") for entry in entries if isinstance(entry, dict)}
    for category in CATEGORIES:
        if category not in present_categories:
            errors.append(f"required category is not represented: {category}")
    for layout in APP_LAYOUTS:
        if layout not in present_layouts:
            errors.append(f"required app layout is not represented: {layout}")

    if len(disk_files) < MIN_IMAGES:
        errors.append(f"dataset has {len(disk_files)} images; at least {MIN_IMAGES} are required")
    if len(entries) < MIN_IMAGES:
        errors.append(f"manifest has {len(entries)} entries; at least {MIN_IMAGES} are required")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the ChitMirror payment screenshot manifest")
    parser.add_argument("--manifest", type=Path, default=DATASET_DIR / MANIFEST_NAME)
    args = parser.parse_args(argv)
    errors = validate(args.manifest)
    if errors:
        print(f"FAILED: {len(errors)} manifest validation error(s)")
        for error in errors:
            print(f" - {error}")
        return 1
    print(f"OK: manifest valid; {len(load_manifest(args.manifest)[0]['images'])} images checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
