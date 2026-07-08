from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


def clean_text(value: str | None) -> str:
    return (value or "").strip()


def parse_synonyms(raw: str, vi_name: str, en_name: str) -> list[str]:
    tokens = [token.strip() for token in raw.split("|") if token.strip()]

    # Keep explicit names inside synonym list so linker can hit exact string faster.
    if vi_name:
        tokens.append(vi_name)
    if en_name:
        tokens.append(en_name)

    deduped: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        key = token.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(token)
    return deduped


def build_mapping(csv_path: Path) -> tuple[list[dict], dict]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    required_cols = {"code", "tên bệnh VI", "tên bệnh EN", "synonym"}
    actual_cols = set(rows[0].keys()) if rows else set()
    if not required_cols.issubset(actual_cols):
        missing = sorted(required_cols - actual_cols)
        raise ValueError(f"CSV missing required columns: {missing}")

    entries: list[dict] = []
    duplicate_codes: list[str] = []
    seen_codes: set[str] = set()

    empty_vi = 0
    empty_en = 0
    empty_synonym = 0
    rows_with_single_or_no_synonym = 0

    code_counter = Counter(clean_text(row.get("code")) for row in rows)
    duplicate_codes = sorted([code for code, count in code_counter.items() if code and count > 1])

    for line_no, row in enumerate(rows, start=2):
        code = clean_text(row.get("code"))
        vi_name = clean_text(row.get("tên bệnh VI"))
        en_name = clean_text(row.get("tên bệnh EN"))
        raw_synonym = clean_text(row.get("synonym"))

        if not code:
            continue

        if not vi_name:
            empty_vi += 1
        if not en_name:
            empty_en += 1
        if not raw_synonym:
            empty_synonym += 1

        synonyms = parse_synonyms(raw_synonym, vi_name, en_name)
        if len(synonyms) <= 1:
            rows_with_single_or_no_synonym += 1

        entry = {
            "code": code,
            "disease_name_vi": vi_name,
            "disease_name_en": en_name,
            "synonyms": synonyms,
            "source_csv_line": line_no,
        }
        entries.append(entry)

        if code in seen_codes:
            continue
        seen_codes.add(code)

    stats = {
        "row_count": len(rows),
        "entry_count": len(entries),
        "unique_code_count": len(seen_codes),
        "duplicate_code_count": len(duplicate_codes),
        "duplicate_codes": duplicate_codes,
        "empty_vi_count": empty_vi,
        "empty_en_count": empty_en,
        "empty_synonym_count": empty_synonym,
        "rows_with_single_or_no_synonym_count": rows_with_single_or_no_synonym,
    }
    return entries, stats


def write_json(output_json: Path, entries: list[dict]) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {"icd10": entries}
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_meta(meta_json: Path, source_csv: Path, stats: dict) -> None:
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_csv": str(source_csv).replace("\\", "/"),
        "schema": {
            "top_level": "icd10",
            "fields": ["code", "disease_name_vi", "disease_name_en", "synonyms", "source_csv_line"],
        },
        "stats": stats,
    }
    meta_json.parent.mkdir(parents=True, exist_ok=True)
    meta_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build ICD-10 mapping JSON (and metadata) from CSV mapping file.",
    )
    parser.add_argument(
        "--input-csv",
        default="data/icd10/icd10_mapping.csv",
        help="Path to input ICD-10 mapping CSV.",
    )
    parser.add_argument(
        "--output-json",
        default="data/icd10/icd10_mapping.json",
        help="Path to output ICD-10 mapping JSON.",
    )
    parser.add_argument(
        "--meta-json",
        default="data/icd10/icd10_mapping.meta.json",
        help="Path to output metadata JSON.",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    input_csv = Path(args.input_csv)
    output_json = Path(args.output_json)
    meta_json = Path(args.meta_json)

    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    entries, stats = build_mapping(input_csv)
    write_json(output_json, entries)
    write_meta(meta_json, input_csv, stats)

    print(f"Wrote {len(entries)} ICD-10 entries -> {output_json}")
    print(f"Wrote metadata -> {meta_json}")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
