import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from extract.pdf_text import extract_line_items
from match.matcher import match_items

BILLS_DIR = Path(__file__).parent / "bills"


def run(bill_id):
    truth = json.load(open(BILLS_DIR / f"{bill_id}.json"))
    items = extract_line_items(BILLS_DIR / f"{bill_id}.pdf")
    matched = match_items(items, truth["hospital_id"])

    hits = 0
    for m, t in zip(matched, truth["lines"]):
        ok = m["matched_cdm"] == t["cdm"]
        hits += ok
        print(f"{'OK ' if ok else 'BAD'} {m['match_method']:<11} {m['confidence']:<6} "
              f"{m['match_score']:>3}  {m['description'][:28]:<28} -> {m['matched_description'][:28]:<28} "
              f"gross={m['gross_charge']}")
    print(f"\n{bill_id}: {hits}/{len(truth['lines'])} matched to the correct CDM "
          f"({100*hits/len(truth['lines']):.0f}%)")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "bill_01")
