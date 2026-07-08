"""Trich xuat danh sach ten thuoc UNG VIEN tu toan bo 100 file test that.

Muc dich: co 1 danh sach ten thuoc thuc te xuat hien trong data (khong bia), lam
dau vao cho buoc tra cuu RxNorm (WBS 1.4, scripts/build_rxnorm_mapping.py).

Chien luoc trich xuat (heuristic, khong phai NER hoan chinh - se duoc thay bang
model o WBS 2.3):
1. Dung rule_extractors.extract_drug_mentions() de bat cum "ten + lieu + don vi".
2. Quet cac dong bullet ("- ...") nam duoi cac tieu de lien quan thuoc (VD "Thuoc
   truoc khi nhap vien", "Cac thuoc da thuc hien") - lay cum tu dau dong truoc dau
   phay/ngoac/dong dung lam ten thuoc ung vien.
Ca 2 nguon deu la HEURISTIC, khong phai ground truth - can Trong (NER, WBS 2.3)
kiem tra lai bang model/gan nhan tay khi co du lieu training.

Output: reports/drug_candidates_raw.json (danh sach ten tho, chua chuan hoa) +
in ra console danh sach da khu trung, sap xep theo tan suat.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skills.medical_text_processing.rule_extractors import extract_drug_mentions  # noqa: E402

INPUT_DIR = ROOT / "input" / "input"

DRUG_SECTION_HEADERS = re.compile(
    r"(thuốc trước khi nhập viện|các thuốc đã thực hiện|thuốc đã thực hiện|"
    r"thuốc đã dùng|các thuốc|được (cho|dùng)|đã (cho|dùng)|dùng thêm)",
    re.IGNORECASE,
)

# Cum dau dong bullet, lay phan truoc dau phay/ngoac/hai cham/so lieu lam ten ung vien
_BULLET_NAME_RE = re.compile(
    r"^-?\s*(?:được (?:cho|dùng)|đã (?:cho|dùng)|dùng|nhận)?\s*"
    r"([A-Za-zÀ-ỹ][A-Za-zÀ-ỹ\-]{2,}(?:\s+[A-Za-zÀ-ỹ\-]{2,}){0,2})",
)

_STOPWORDS = {
    "được", "đã", "dùng", "cho", "nhận", "thêm", "và", "các", "thuốc", "bệnh",
    "nhân", "iv", "po", "bid", "tid", "qid", "prn", "once", "trong", "khi",
    "không", "có", "là", "kết", "quả", "sau", "để", "với", "vì", "đến",
}


def _clean_candidate(raw: str) -> str | None:
    raw = raw.strip().strip(".,;:-")
    if not raw:
        return None
    first_word = raw.split()[0].lower()
    if first_word in _STOPWORDS:
        return None
    if len(raw) < 3:
        return None
    return raw


def extract_from_dose_patterns() -> Counter:
    counts: Counter = Counter()
    for f in sorted(INPUT_DIR.glob("*.txt"), key=lambda p: int(p.stem)):
        text = f.read_text(encoding="utf-8")
        for m in extract_drug_mentions(text):
            name = m.text.split()[0]
            counts[name.lower()] += 1
    return counts


def extract_from_bullet_lines() -> Counter:
    counts: Counter = Counter()
    for f in sorted(INPUT_DIR.glob("*.txt"), key=lambda p: int(p.stem)):
        lines = f.read_text(encoding="utf-8").splitlines()
        in_drug_section = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r"^\d+\.\s|^[A-ZĐ]", stripped) and not stripped.startswith("-"):
                in_drug_section = bool(DRUG_SECTION_HEADERS.search(stripped))
                continue
            if stripped.startswith("-") and (in_drug_section or DRUG_SECTION_HEADERS.search(stripped)):
                body = stripped.lstrip("- ").split(":")[0]
                body = re.split(r"[,(]", body)[0]
                m = _BULLET_NAME_RE.match(body)
                if m:
                    cand = _clean_candidate(m.group(1))
                    if cand:
                        counts[cand.lower()] += 1
    return counts


def main() -> None:
    dose_counts = extract_from_dose_patterns()
    bullet_counts = extract_from_bullet_lines()

    combined = Counter()
    combined.update(dose_counts)
    combined.update(bullet_counts)

    result = {
        "from_dose_pattern": dict(dose_counts.most_common()),
        "from_bullet_lines": dict(bullet_counts.most_common()),
        "combined_sorted": [name for name, _ in combined.most_common()],
    }
    out_path = ROOT / "reports" / "drug_candidates_raw.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Tu dose pattern: {len(dose_counts)} ten khac nhau")
    print(f"Tu bullet lines: {len(bullet_counts)} ten khac nhau")
    print(f"Tong hop (khu trung): {len(combined)} ten khac nhau")
    print(json.dumps(combined.most_common(60), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
