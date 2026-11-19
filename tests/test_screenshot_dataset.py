import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from screenshot_fixture_tools import DATASET_DIR, read_png, render_fixture_image, write_png
from validate_screenshot_manifest import validate

MANIFEST_PATH = DATASET_DIR / "manifest.json"


def copy_dataset(tmp_path: Path) -> Path:
    destination = tmp_path / "payment_screenshots"
    shutil.copytree(DATASET_DIR, destination)
    return destination


def read_manifest(dataset_dir: Path) -> dict:
    return json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))


def save_manifest(dataset_dir: Path, manifest: dict) -> None:
    (dataset_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def test_valid_manifest_passes_validation():
    assert validate(MANIFEST_PATH) == []


def test_missing_image_is_reported(tmp_path):
    dataset_dir = copy_dataset(tmp_path)
    entry = read_manifest(dataset_dir)["images"][0]
    (dataset_dir / entry["filename"]).unlink()
    errors = validate(dataset_dir / "manifest.json")
    assert any("manifest entry points to a missing image file" in error for error in errors)


def test_duplicate_image_id_is_reported(tmp_path):
    dataset_dir = copy_dataset(tmp_path)
    manifest = read_manifest(dataset_dir)
    first = manifest["images"][0]
    duplicate = dict(first)
    duplicate["filename"] = f"{first['category']}/{first['app_layout']}/duplicate-id.png"
    shutil.copyfile(dataset_dir / first["filename"], dataset_dir / duplicate["filename"])
    manifest["images"].append(duplicate)
    save_manifest(dataset_dir, manifest)
    errors = validate(dataset_dir / "manifest.json")
    assert any("duplicate image_id" in error for error in errors)


def test_duplicate_filename_is_reported(tmp_path):
    dataset_dir = copy_dataset(tmp_path)
    manifest = read_manifest(dataset_dir)
    first = manifest["images"][0]
    duplicate = dict(first)
    duplicate["image_id"] = f"{first['image_id']}-COPY"
    manifest["images"].append(duplicate)
    save_manifest(dataset_dir, manifest)
    errors = validate(dataset_dir / "manifest.json")
    assert any("duplicate filename" in error for error in errors)


def test_invalid_category_is_reported(tmp_path):
    dataset_dir = copy_dataset(tmp_path)
    manifest = read_manifest(dataset_dir)
    manifest["images"][0]["category"] = "not-a-category"
    save_manifest(dataset_dir, manifest)
    errors = validate(dataset_dir / "manifest.json")
    assert any("invalid category" in error for error in errors)


def test_missing_expected_result_is_reported(tmp_path):
    dataset_dir = copy_dataset(tmp_path)
    manifest = read_manifest(dataset_dir)
    del manifest["images"][0]["expected_status"]
    save_manifest(dataset_dir, manifest)
    errors = validate(dataset_dir / "manifest.json")
    assert any("missing required field 'expected_status'" in error for error in errors)


def test_invalid_csv_reference_is_reported(tmp_path):
    dataset_dir = copy_dataset(tmp_path)
    manifest = read_manifest(dataset_dir)
    manifest["images"][0]["corresponding_bank_csv_reference"] = "MISSING_EVIDENCE.csv"
    save_manifest(dataset_dir, manifest)
    errors = validate(dataset_dir / "manifest.json")
    assert any("bank CSV reference points to a missing file" in error for error in errors)


def test_missing_watermark_on_synthetic_image_is_reported(tmp_path):
    dataset_dir = copy_dataset(tmp_path)
    entry = read_manifest(dataset_dir)["images"][0]
    render_fixture_image(
        dataset_dir / entry["filename"],
        layout=entry["app_layout"],
        category=entry["category"],
        image_id=entry["image_id"],
        utr=entry["expected_utr_reference"],
        claim_amount=entry["claimed_amount"],
        claimed_date=entry["claimed_date"],
        draw_watermark=False,
    )
    errors = validate(dataset_dir / "manifest.json")
    assert any("visible test-only watermark" in error for error in errors)


def test_dataset_below_forty_images_is_reported(tmp_path):
    dataset_dir = copy_dataset(tmp_path)
    manifest = read_manifest(dataset_dir)
    removed = manifest["images"].pop()
    (dataset_dir / removed["filename"]).unlink()
    save_manifest(dataset_dir, manifest)
    errors = validate(dataset_dir / "manifest.json")
    assert any("dataset has 39 images" in error for error in errors)


def test_personal_information_in_synthetic_image_is_reported(tmp_path):
    dataset_dir = copy_dataset(tmp_path)
    entry = read_manifest(dataset_dir)["images"][0]
    path = dataset_dir / entry["filename"]
    image = read_png(path)
    texts = dict(image.texts)
    texts["Fixture"] = texts["Fixture"] + " contact 9876543210"
    write_png(path, image.width, image.height, image.pixels, texts)
    errors = validate(dataset_dir / "manifest.json")
    assert any("personal information" in error or "unrecognised long number" in error for error in errors)


def test_manifest_expected_results_use_shared_contract_statuses():
    manifest = read_manifest(DATASET_DIR)
    schema = json.loads((ROOT / "contracts" / "schemas.json").read_text(encoding="utf-8"))
    allowed = set(schema["$defs"]["status"]["enum"])
    assert set(manifest["allowed_statuses"]) == allowed
    assert {entry["expected_status"] for entry in manifest["images"]} <= allowed
