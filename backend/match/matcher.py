import csv
from pathlib import Path

from rapidfuzz import fuzz, process

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"


class PriceFile:
    def __init__(self, hospital_id):
        path = PROCESSED_DIR / f"{hospital_id}.csv"
        with open(path) as f:
            self.rows = list(csv.DictReader(f))

        # one row per CDM (drugs appear twice with identical prices)
        self.by_cdm = {}
        for r in self.rows:
            if r["cdm_code"] and r["cdm_code"] not in self.by_cdm:
                self.by_cdm[r["cdm_code"]] = r

        # a CPT can map to several rows with different prices
        self.by_cpt = {}
        for r in self.rows:
            if r["code"]:
                self.by_cpt.setdefault(r["code"], []).append(r)

        # descriptions for fuzzy search, deduped by CDM
        self.desc_rows = list(self.by_cdm.values())
        self.desc_list = [r["description"] for r in self.desc_rows]

    def best_by_description(self, description, candidates=None):
        rows = candidates if candidates is not None else self.desc_rows
        choices = [r["description"] for r in rows]
        if not choices:
            return None, 0
        result = process.extractOne(description, choices, scorer=fuzz.token_sort_ratio)
        if result is None:
            return None, 0
        _, score, idx = result
        return rows[idx], score


def match_item(item, price):
    """Return the bill item with match fields added."""
    out = dict(item)
    out.update({"match_method": "none", "confidence": "none", "match_score": 0,
                "matched_cdm": "", "matched_description": "",
                "gross_charge": None, "discounted_cash": None})

    row = None

    # 1. exact CDM: the hospital's own key, best case
    if item.get("cdm") and item["cdm"] in price.by_cdm:
        row = price.by_cdm[item["cdm"]]
        out.update(match_method="cdm", confidence="high", match_score=100)

    # 2. CPT: if several rows share it, pick by description similarity
    elif item.get("cpt") and item["cpt"] in price.by_cpt:
        candidates = price.by_cpt[item["cpt"]]
        if len(candidates) == 1:
            row, score = candidates[0], 100
        else:
            row, score = price.best_by_description(item["description"], candidates)
        out.update(match_method="cpt", confidence="medium", match_score=round(score))

    # 3. fuzzy description across the whole chargemaster
    elif item.get("description"):
        row, score = price.best_by_description(item["description"])
        if score >= 85:
            out.update(match_method="description", confidence="medium", match_score=round(score))
        elif score >= 70:
            out.update(match_method="description", confidence="low", match_score=round(score))
        else:
            row = None

    if row:
        out["matched_cdm"] = row["cdm_code"]
        out["matched_description"] = row["description"]
        out["gross_charge"] = float(row["gross_charge"])
        out["discounted_cash"] = float(row["discounted_cash"]) if row["discounted_cash"] else None

    return out


def match_items(items, hospital_id):
    price = PriceFile(hospital_id)
    return [match_item(it, price) for it in items]