import json
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

BILLS_DIR = Path(__file__).parent / "bills"


def make_pdf(bill_id):
    bill = json.load(open(BILLS_DIR / f"{bill_id}.json"))
    out_path = BILLS_DIR / f"{bill_id}.pdf"

    c = canvas.Canvas(str(out_path), pagesize=letter)
    width, height = letter
    y = height - 60

    # header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, bill["hospital_name"])
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "ITEMIZED STATEMENT")
    y -= 24
    c.drawString(50, y, f"Patient: {bill['patient_name']}")
    c.drawString(350, y, f"Account: {bill['account_number']}")
    y -= 14
    c.drawString(50, y, f"Date of Service: {bill['date_of_service']}")
    y -= 30

    # column headers
    c.setFont("Helvetica-Bold", 9)
    cols = [(50, "DATE"), (115, "CDM"), (175, "CPT"), (220, "REV"),
            (255, "DESCRIPTION"), (450, "QTY"), (500, "AMOUNT")]
    for x, label in cols:
        c.drawString(x, y, label)
    y -= 6
    c.line(50, y, 560, y)
    y -= 14

    # line items
    c.setFont("Helvetica", 9)
    total = 0
    for line in bill["lines"]:
        c.drawString(50, y, line["date"])
        c.drawString(115, y, line["cdm"])
        c.drawString(175, y, line["cpt"])
        c.drawString(220, y, line["rev"])
        c.drawString(255, y, line["description"])
        c.drawRightString(470, y, str(line["qty"]))
        c.drawRightString(560, y, f"{line['amount']:,.2f}")
        total += line["amount"]
        y -= 14

    # total
    y -= 6
    c.line(50, y, 560, y)
    y -= 16
    c.setFont("Helvetica-Bold", 10)
    c.drawString(255, y, "TOTAL CHARGES")
    c.drawRightString(560, y, f"{total:,.2f}")

    c.save()
    print(f"wrote {out_path}")


if __name__ == "__main__":
    make_pdf(sys.argv[1] if len(sys.argv) > 1 else "bill_01")