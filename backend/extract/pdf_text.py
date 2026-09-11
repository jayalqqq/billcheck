import re
import pdfplumber

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$|^\d{1,2}/\d{1,2}/\d{2,4}$")
MONEY_RE = re.compile(r"^-?\$?[\d,]+\.\d{2}$")
CDM_RE = re.compile(r"^\d{6,8}$")
CPT_RE = re.compile(r"^\d{5}$|^[A-Z]\d{4}$")   # 5 digits, or HCPCS like J1234
REV_RE = re.compile(r"^\d{3,4}$")


def extract_text_lines(pdf_path):
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines.extend(text.split("\n"))
    return lines


def parse_line(line):
    tokens = line.split()
    if len(tokens) < 4:
        return None
    if not DATE_RE.match(tokens[0]):
        return None
    if not MONEY_RE.match(tokens[-1]):
        return None

    item = {"date": tokens[0], "cdm": "", "cpt": "", "rev": "",
            "description": "", "qty": 1, "amount": 0.0}

    item["amount"] = float(tokens[-1].replace("$", "").replace(",", ""))
    rest = tokens[1:-1]

    # quantity is the integer right before the amount, if there is one
    if rest and rest[-1].isdigit():
        item["qty"] = int(rest[-1])
        rest = rest[:-1]

    # peel codes off the front until we hit a word that isn't a code
    while rest:
        tok = rest[0]
        if CDM_RE.match(tok) and not item["cdm"]:
            item["cdm"] = tok
        elif CPT_RE.match(tok) and not item["cpt"]:
            item["cpt"] = tok
        elif REV_RE.match(tok) and not item["rev"]:
            item["rev"] = tok
        else:
            break
        rest = rest[1:]

    item["description"] = " ".join(rest)
    return item


def extract_line_items(pdf_path):
    items = []
    for line in extract_text_lines(pdf_path):
        parsed = parse_line(line)
        if parsed:
            items.append(parsed)
    return items


if __name__ == "__main__":
    import sys, json
    for it in extract_line_items(sys.argv[1]):
        print(json.dumps(it))