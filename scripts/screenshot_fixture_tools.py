import json
import re
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "payment_screenshots"
MANIFEST_NAME = "manifest.json"
PROVISIONAL_CSV = "PROVISIONAL_bank_evidence_T06_NOT_MERGED.csv"
PROVISIONAL_DUE_DATE = "2026-03-10"
WATERMARK_TEXT = "SYNTHETIC — TEST ONLY"
WATERMARK_PIXEL = (255, 0, 255)
MIN_IMAGES = 40
CATEGORIES = ("genuine", "fake", "reused", "wrong_amount", "late")
APP_LAYOUTS = ("gpay", "phonepe", "paytm", "bank_app")
ALLOWED_STATUSES = ("verified", "duplicate", "wrong_amount", "needs_review")
STATUS_BY_CATEGORY = {
    "genuine": "verified",
    "fake": "needs_review",
    "reused": "duplicate",
    "wrong_amount": "wrong_amount",
    "late": "verified",
}
REASON_BY_CATEGORY = {
    "genuine": "Matched bank credit.",
    "fake": "UTR not found in bank CSV.",
    "reused": "UTR already used.",
    "late": "Matched bank credit after due date; ledger status overdue.",
}
REQUIRED_ENTRY_FIELDS = (
    "image_id",
    "filename",
    "app_layout",
    "category",
    "synthetic",
    "expected_status",
    "expected_reason",
    "expected_amount",
    "expected_month",
    "expected_utr_reference",
    "corresponding_bank_csv_reference",
    "scenario_id",
)
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}

FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000",) * 7,
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
}

LAYOUT_COLORS = {
    "gpay": ((245, 247, 250), (66, 133, 244), (52, 168, 83)),
    "phonepe": ((245, 240, 250), (95, 37, 147), (126, 55, 174)),
    "paytm": ((240, 248, 255), (0, 120, 215), (0, 150, 190)),
    "bank_app": ((240, 245, 240), (27, 94, 60), (45, 130, 85)),
}

PII_PATTERNS = (
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
    r"aadhaar",
    r"account\s*(no|number)",
    r"ifsc",
    r"pan\s*card",
    r"\+91",
)


@dataclass(frozen=True)
class PngImage:
    width: int
    height: int
    pixels: bytearray
    texts: dict[str, str]


def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png(path: Path, width: int, height: int, pixels: bytearray, texts: dict[str, str]) -> None:
    raw = bytearray()
    row_length = width * 3
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * row_length:(y + 1) * row_length])
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    chunks = [b"\x89PNG\r\n\x1a\n", _chunk(b"IHDR", ihdr)]
    for key, value in texts.items():
        data = key.encode("ascii") + b"\x00\x00\x00\x00\x00" + value.encode("utf-8")
        chunks.append(_chunk(b"iTXt", data))
    chunks.append(_chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
    chunks.append(_chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(chunks))


def read_png(path: Path) -> PngImage:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not a PNG file")
    offset = 8
    idat = bytearray()
    texts: dict[str, str] = {}
    width = height = 0
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        tag = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        offset += 12 + length
        if tag == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if depth != 8 or color != 2 or compression or filtering or interlace:
                raise ValueError("unsupported PNG encoding")
        elif tag == b"IDAT":
            idat.extend(payload)
        elif tag == b"iTXt":
            keyword, rest = payload.split(b"\x00", 1)
            if len(rest) >= 2 and rest[0] == 0 and rest[1] == 0:
                fields = rest[2:].split(b"\x00", 2)
                if len(fields) == 3:
                    texts[keyword.decode("ascii")] = fields[2].decode("utf-8")
        elif tag == b"tEXt":
            key, _, value = payload.partition(b"\x00")
            texts[key.decode("ascii")] = value.decode("latin-1")
        elif tag == b"IEND":
            break
    if not width or not height or not idat:
        raise ValueError("incomplete PNG file")
    decoded = zlib.decompress(bytes(idat))
    stride = width * 3
    if len(decoded) != height * (stride + 1):
        raise ValueError("unexpected PNG image data length")
    if all(decoded[y * (stride + 1)] == 0 for y in range(height)):
        pixels = bytearray()
        for y in range(height):
            source_offset = y * (stride + 1)
            pixels.extend(decoded[source_offset + 1:source_offset + 1 + stride])
        return PngImage(width, height, pixels, texts)

    pixels = bytearray(height * stride)
    previous = bytearray(stride)
    for y in range(height):
        source_offset = y * (stride + 1)
        filter_type = decoded[source_offset]
        scanline = decoded[source_offset + 1:source_offset + 1 + stride]
        target_offset = y * stride
        for x in range(stride):
            left = pixels[target_offset + x - 3] if x >= 3 else 0
            up = previous[x]
            upper_left = previous[x - 3] if x >= 3 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                candidate = left + up - upper_left
                distances = (abs(candidate - left), abs(candidate - up), abs(candidate - upper_left))
                predictor = (left, up, upper_left)[distances.index(min(distances))]
            else:
                raise ValueError("unsupported PNG filter")
            pixels[target_offset + x] = (scanline[x] + predictor) & 0xFF
        previous = pixels[target_offset:target_offset + stride]
    return PngImage(width, height, pixels, texts)


def count_pixel(image: PngImage, color: tuple[int, int, int]) -> int:
    needle = bytes(color)
    data = bytes(image.pixels)
    count = 0
    offset = data.find(needle)
    while offset != -1:
        if offset % 3 == 0:
            count += 1
        offset = data.find(needle, offset + 1)
    return count


def _fill_rect(pixels: bytearray, width: int, x: int, y: int, w: int, h: int, color: tuple[int, int, int]) -> None:
    for row in range(y, y + h):
        for column in range(x, x + w):
            offset = (row * width + column) * 3
            pixels[offset:offset + 3] = bytes(color)


def draw_text(pixels: bytearray, width: int, text: str, x: int, y: int, color: tuple[int, int, int], scale: int = 2) -> None:
    for char in text.upper():
        glyph = FONT.get(char, FONT[" "])
        for row, bits in enumerate(glyph):
            for column, bit in enumerate(bits):
                if bit == "1":
                    _fill_rect(pixels, width, x + column * scale, y + row * scale, scale, scale, color)
        x += 6 * scale


def render_fixture_image(
    path: Path,
    *,
    layout: str,
    category: str,
    image_id: str,
    utr: str,
    claim_amount: int,
    claimed_date: str,
    draw_watermark: bool = True,
) -> None:
    width, height = 360, 640
    background, header, accent = LAYOUT_COLORS[layout]
    pixels = bytearray(background * (width * height))
    _fill_rect(pixels, width, 0, 0, width, 84, header)
    _fill_rect(pixels, width, 20, 112, width - 40, 300, (255, 255, 255))
    _fill_rect(pixels, width, 20, 112, width - 40, 8, accent)
    draw_text(pixels, width, layout.upper(), 28, 24, (255, 255, 255), 3)
    draw_text(pixels, width, "DEMO PAYMENT INTERFACE", 28, 58, (255, 255, 255), 2)
    draw_text(pixels, width, "PAYMENT CLAIM", 40, 150, (30, 30, 30), 3)
    draw_text(pixels, width, f"AMOUNT INR {claim_amount / 100:.2f}", 40, 210, (30, 30, 30), 2)
    draw_text(pixels, width, f"REF {utr}", 40, 256, (30, 30, 30), 2)
    draw_text(pixels, width, f"DATE {claimed_date}", 40, 302, (30, 30, 30), 2)
    draw_text(pixels, width, f"CATEGORY {category.upper()}", 40, 348, (90, 90, 90), 2)
    if draw_watermark:
        _fill_rect(pixels, width, 16, 436, width - 32, 160, (245, 245, 245))
        draw_text(pixels, width, "SYNTHETIC", 52, 456, WATERMARK_PIXEL, 4)
        draw_text(pixels, width, "TEST ONLY", 60, 512, WATERMARK_PIXEL, 4)
        draw_text(pixels, width, "NOT A REAL PAYMENT", 36, 584, (120, 0, 0), 2)
    fixture = {
        "image_id": image_id,
        "app_layout": layout,
        "category": category,
        "utr": utr,
        "amount_paise": claim_amount,
        "claimed_date": claimed_date,
    }
    texts = {
        "Synthetic": "true",
        "Watermark": WATERMARK_TEXT,
        "Fixture": json.dumps(fixture, sort_keys=True),
    }
    write_png(path, width, height, pixels, texts)


def find_personal_information(texts: dict[str, str], allowed_utrs: set[str]) -> list[str]:
    combined = " ".join(texts.values())
    findings: list[str] = []
    for pattern in PII_PATTERNS:
        for match in re.finditer(pattern, combined, re.IGNORECASE):
            findings.append(f"personal information pattern in image metadata: {match.group(0)}")
    for number in re.findall(r"\b\d{10,13}\b", combined):
        if number not in allowed_utrs:
            findings.append(f"unrecognised long number in image metadata: {number}")
    return findings
