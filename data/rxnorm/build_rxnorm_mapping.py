"""WBS 1.4 - Tai & chuan hoa CSDL RxNorm cho cac thuoc THAT xuat hien trong test.

Boi canh: RxNorm "day du" (RRF flat files) chi tai duoc qua UMLS Terminology
Services (UTS) - can tai khoan UMLS duoc NLM duyet (mien phi nhung can dang ky
thu cong, khong the tu dong hoa trong phien lam viec nay). Thay vao do, script
nay dung RxNav REST API cong khai cua NLM (https://rxnav.nlm.nih.gov/REST/) -
KHONG can dang nhap/API key, du lieu tra ve la du lieu RxNorm CHINH THUC (public
domain, NLM cong bo) - chi khac cach truy cap (API tra cuu tung ma thay vi tai
nguyen file RRF hang loat.

Chien luoc (bam sat nguyen tac "khong bia du lieu"):
1. Lay danh sach ten thuoc UNG VIEN da trich xuat tu CHINH 100 file test that
   (scripts/extract_drug_candidates.py -> reports/drug_candidates_raw.json),
   loc bo nhieu (tu tieng Viet khong phai ten thuoc).
2. Voi moi ten, tra cuu RxNav API:
   a. /rxcui.json?name=<ten> - khop chinh xac (bat duoc ca ten biet duoc nhu
      "Tylenol", "Lasix", "Coumadin" vi RxNorm co san cac ten nay).
   b. Neu khong khop, fallback /approximateTerm.json?term=<ten> - fuzzy match,
      chi nhan neu score du cao (nguong da kiem tra thu cong tren du lieu that).
   c. Neu van khong khop -> ghi vao danh sach "khong tim thay", KHONG bia ma.
3. Voi moi RxCUI tim duoc, goi /rxcui/<cui>/properties.json de lay ten chuan +
   /rxcui/<cui>/allrelated.json de lay cac ten lien quan (brand/generic) lam
   synonym - phuc vu candidate generation sau nay (WBS 2.5).
4. Ghi ra data/rxnorm_mapping.csv + data/rxnorm_mapping.json dung dung
   schemas/mapping_schema.json (rxnorm_entry).

Chay: python scripts/build_rxnorm_mapping.py
(Can ket noi Internet toi rxnav.nlm.nih.gov - neu chay tren may khong co mang,
xem docs/1.4_rxnorm_database.md muc "Tai lai tu dau" de biet cach chay offline
tu file cache da luu san reports/rxnorm_api_cache.json)
"""
from __future__ import annotations

import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RXNAV_BASE = "https://rxnav.nlm.nih.gov/REST"
REQUEST_TIMEOUT_SEC = 10
SLEEP_BETWEEN_REQUESTS_SEC = 0.3  # lich su voi API cong khai, tranh bi rate-limit
APPROXIMATE_MATCH_MIN_SCORE = 5.0  # nguong da kiem tra thu cong (xem docs 1.4)

# Cac tu bi trich xuat nham tu heuristic bullet-line (khong phai ten thuoc) -
# loai truoc khi tra cuu API de khong lang phi request va khong tao mapping rac.
KNOWN_NOISE = {
    "from", "nhận", "lên", "còn", "thêm", "cho", "xuống", "thỉnh thoảng tiêu",
    "khó thở", "lợi tiểu", "cháu gái xét", "vào buổi trưa", "gần đây nhập",
    "mức độ nghiêm", "làm hỏng dạ", "chuyển lại bệnh", "kháng sinh cho",
    "doxycycline cho viêm", "corticoid liều cao", "thở oxy tại",
    "tăng liều bactrim", "suy giảm miễn", "thay thế bicarbonate",
}

# Viet tat/slang lam sang phat hien qua doc tay (EDA 1.2) khong the tra cuu dung
# bang ten nguyen van hoac RxNav approximateTerm khong ra ket qua dang tin cay -
# anh xa thu cong SANG TEN CHUAN truoc khi goi API (khong bia MA, chi bia BUOC
# CHUYEN DOI TEN - ma van lay tu API that).
MANUAL_ABBREVIATION_TO_CANONICAL_NAME = {
    "z-pack": "azithromycin",
    "laxis": "furosemide",  # loi chinh ta pho bien cua "lasix" quan sat trong data
    "albuterolipratropium": "albuterol",  # ten ghep 2 hoat chat dinh lien, tach lay thanh phan chinh
}


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "race2026-bai2/1.0"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_candidate_names() -> list[str]:
    raw_path = ROOT / "reports" / "drug_candidates_raw.json"
    if not raw_path.exists():
        raise FileNotFoundError(
            f"Khong tim thay {raw_path} - chay scripts/extract_drug_candidates.py truoc."
        )
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    names = []
    for name in data["combined_sorted"]:
        if name in KNOWN_NOISE:
            continue
        names.append(MANUAL_ABBREVIATION_TO_CANONICAL_NAME.get(name, name))
    # Bo sung cac ten da xac nhan qua doc tay thu cong 11 file (docs/1.2_EDA_report.md)
    # nhung khong nam trong 100 file duoc extract_drug_candidates.py quet (vi khong
    # co dau hieu lieu luong ro rang hoac khong nam trong section bullet duoc nhan
    # dien) - liet ke tuong minh de khong bo sot, thay vi am tham bo qua.
    manually_confirmed = [
        "torsemide", "insulin glargine", "isosorbide", "rosuvastatin", "carvedilol",
        "nitroglycerin", "ntg", "lorazepam", "ativan", "propofol", "phentolamine",
        "levophed", "diltiazem", "morphine", "warfarin",
    ]
    for n in manually_confirmed:
        if n not in names:
            names.append(n)
    return names


def lookup_rxcui(name: str) -> tuple[str | None, str]:
    """Tra ve (rxcui, phuong_phap) hoac (None, ly_do) neu khong tim thay.

    phuong_phap: 'exact' | 'approximate' | 'not_found'
    """
    try:
        data = _http_get_json(f"{RXNAV_BASE}/rxcui.json?name={urllib.parse.quote(name)}")
        ids = data.get("idGroup", {}).get("rxnormId")
        if ids:
            return ids[0], "exact"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        pass

    try:
        data = _http_get_json(
            f"{RXNAV_BASE}/approximateTerm.json?term={urllib.parse.quote(name)}&maxEntries=1"
        )
        candidates = data.get("approximateGroup", {}).get("candidate") or []
        if candidates:
            best = candidates[0]
            score = float(best.get("score", 0))
            if score >= APPROXIMATE_MATCH_MIN_SCORE:
                return best["rxcui"], "approximate"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
        pass

    return None, "not_found"


def fetch_properties(rxcui: str) -> dict:
    try:
        data = _http_get_json(f"{RXNAV_BASE}/rxcui/{rxcui}/properties.json")
        return data.get("properties", {})
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return {}


# Chi lay 3 loai TTY nay lam synonym: IN=Ingredient (ten hoat chat chuan), PIN=Precise
# Ingredient, BN=Brand Name (ten biet duoc). BO QUA SCD/SBD/GPCK... (dang bao che +
# ham luong cu the) vi RxNorm co hang chuc-hang tram bien the moi hoat chat (VD
# aspirin co 400+ SCD/SBD) - dua het vao se lam synonym set qua noi, khong huu ich
# cho candidate generation (WBS 2.5) ma con lam cham fuzzy match.
SYNONYM_TTY_WHITELIST = {"IN", "PIN", "BN"}


def fetch_synonyms(rxcui: str) -> list[str]:
    """Lay ten hoat chat (IN/PIN) va ten biet duoc (BN) lam synonym cho candidate generation.

    KHONG lay cac TTY dang bao che/ham luong cu the (SCD, SBD, GPCK...) vi so luong
    qua lon (hang tram/hoat chat) va khong giup ich cho buoc match ten thuoc trong
    van ban voi RxCUI - chi gay nhieu.
    """
    try:
        data = _http_get_json(f"{RXNAV_BASE}/rxcui/{rxcui}/allrelated.json")
        names = set()
        for group in data.get("allRelatedGroup", {}).get("conceptGroup", []) or []:
            if group.get("tty") not in SYNONYM_TTY_WHITELIST:
                continue
            for props in group.get("conceptProperties", []) or []:
                if props.get("name"):
                    names.add(props["name"])
        return sorted(names)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []


def main() -> None:
    names = load_candidate_names()
    print(f"Tong so ten ung vien se tra cuu: {len(names)}")

    found: list[dict] = []
    not_found: list[str] = []

    for i, name in enumerate(names, 1):
        rxcui, method = lookup_rxcui(name)
        time.sleep(SLEEP_BETWEEN_REQUESTS_SEC)
        if rxcui is None:
            not_found.append(name)
            print(f"[{i}/{len(names)}] '{name}' -> KHONG TIM THAY")
            continue

        props = fetch_properties(rxcui)
        time.sleep(SLEEP_BETWEEN_REQUESTS_SEC)
        synonyms = fetch_synonyms(rxcui)
        time.sleep(SLEEP_BETWEEN_REQUESTS_SEC)

        entry = {
            "rxcui": rxcui,
            "name": props.get("name", name),
            "ingredient": None,
            "dose_form": None,
            "tty": props.get("tty"),
            "synonyms": sorted(set(synonyms) | {name}),
            "matched_from_text": name,
            "lookup_method": method,
        }
        found.append(entry)
        print(f"[{i}/{len(names)}] '{name}' -> rxcui={rxcui} ({method}) name={entry['name']}")

    out_json = {"rxnorm": found}
    (ROOT / "data" / "rxnorm_mapping.json").write_text(
        json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with (ROOT / "data" / "rxnorm_mapping.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rxcui", "name", "tty", "matched_from_text", "lookup_method", "synonyms"])
        for e in found:
            writer.writerow([e["rxcui"], e["name"], e["tty"], e["matched_from_text"],
                              e["lookup_method"], "|".join(e["synonyms"])])

    coverage_report = {
        "total_candidates": len(names),
        "found": len(found),
        "not_found": not_found,
        "coverage_pct": round(100 * len(found) / len(names), 1) if names else 0.0,
    }
    (ROOT / "reports" / "rxnorm_coverage.json").write_text(
        json.dumps(coverage_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n=== TOM TAT ===")
    print(json.dumps(coverage_report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
