from __future__ import annotations

import argparse
import csv
import io
import json
import re
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from unicodedata import normalize as unicode_normalize


DEFAULT_SOURCE_URL = (
    "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/"
    "ICD10CM/2027/icd10cm-code-descriptions-2027.zip"
)
DEFAULT_INNER_TXT = "icd10cm-code-descriptions-2027/icd10cm-codes-2027.txt"


def normalize_code(code: str) -> str:
    """Normalize ICD code to dotted uppercase style (e.g., A010 -> A01.0)."""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", code).upper()
    if len(cleaned) <= 3:
        return cleaned
    return f"{cleaned[:3]}.{cleaned[3:]}"


def normalize_text(text: str) -> str:
    """Normalize spacing/unicode to keep consistent lexical forms."""
    text = unicode_normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_code_lines(raw_text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = re.split(r"\s+", line, maxsplit=1)
        if len(parts) != 2:
            continue

        raw_code, raw_name = parts
        code = normalize_code(raw_code)
        name_en = normalize_text(raw_name)

        if not code or not name_en:
            continue

        rows.append((code, name_en))

    return rows


def deduplicate(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
    # Keep the first occurrence per code to preserve official ordering.
    seen: dict[str, str] = {}
    for code, name in rows:
        if code not in seen:
            seen[code] = name
    return list(seen.items())


def download_zip(source_url: str) -> bytes:
    with urllib.request.urlopen(source_url) as response:
        return response.read()


def load_inner_text(zip_bytes: bytes, inner_txt: str) -> str:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        with zf.open(inner_txt) as fp:
            return fp.read().decode("utf-8", errors="replace")


def write_catalog_csv(rows: list[tuple[str, str]], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "disease_name_vi", "disease_name_en"])
        for code, name_en in rows:
            writer.writerow([code, "", name_en])


def write_metadata(
    output_json: Path,
    source_url: str,
    inner_txt: str,
    row_count: int,
) -> None:
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_url": source_url,
        "source_inner_file": inner_txt,
        "row_count": row_count,
        "notes": [
            "This file is catalog-only (no synonym mapping yet).",
            "Disease names are currently English from ICD-10-CM source.",
            "Vietnamese names can be enriched in a later mapping step.",
        ],
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run(source_url: str, inner_txt: str, output_csv: Path, metadata_json: Path) -> None:
    zip_bytes = download_zip(source_url)
    raw_text = load_inner_text(zip_bytes, inner_txt)

    parsed = parse_code_lines(raw_text)
    deduped = deduplicate(parsed)

    write_catalog_csv(deduped, output_csv)
    write_metadata(metadata_json, source_url, inner_txt, len(deduped))

    print(f"Wrote {len(deduped)} rows -> {output_csv}")
    print(f"Wrote metadata -> {metadata_json}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download and normalize ICD-10 catalog from public source.",
    )
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--inner-txt", default=DEFAULT_INNER_TXT)
    parser.add_argument(
        "--output-csv",
        default="data/icd10/icd10_catalog_normalized.csv",
        help="Output catalog CSV path.",
    )
    parser.add_argument(
        "--metadata-json",
        default="data/icd10/icd10_catalog_normalized.meta.json",
        help="Metadata JSON path.",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    run(
        source_url=args.source_url,
        inner_txt=args.inner_txt,
        output_csv=Path(args.output_csv),
        metadata_json=Path(args.metadata_json),
    )


if __name__ == "__main__":
    main()
