import csv
import json
from pathlib import Path

HOSPITAL_ID = "san_ramon"
HOSPITAL_NAME = "San Ramon Regional Medical Center"

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "san_ramon.json"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "san_ramon.csv"

COLUMNS = ["hospital_id", "code", "code_type", "cdm_code", "rev_code",
           "description", "gross_charge", "discounted_cash", "setting"]


def load():
    with open(RAW_PATH) as f:
        data = json.load(f)

    rows = []
    for item in data["standard_charge_information"]:
        # pull the three kinds of codes apart
        code = code_type = cdm_code = rev_code = ""
        for c in item.get("code_information", []):
            if c["type"] in ("CPT", "HCPCS"):
                code, code_type = c["code"], c["type"]
            elif c["type"] == "CDM":
                cdm_code = c["code"]
            elif c["type"] == "RC":
                rev_code = c["code"]

        for sc in item.get("standard_charges", []):
            if "gross_charge" not in sc:
                continue  # payer-only entries are no use for overcharge checks
            rows.append({
                "hospital_id": HOSPITAL_ID,
                "code": code,
                "code_type": code_type,
                "cdm_code": cdm_code,
                "rev_code": rev_code,
                "description": item["description"],
                "gross_charge": sc["gross_charge"],
                "discounted_cash": sc.get("discounted_cash", ""),
                "setting": sc.get("setting", ""),
            })
    return rows


def save(rows):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    rows = load()
    save(rows)
    print(f"wrote {len(rows)} rows to {OUT_PATH}")