# BillCheck Architecture

Last updated: end of Week 1 (Sep 10, 2026)

## What it does
Patient uploads an itemized hospital bill. BillCheck extracts the line items,
matches each one against the hospital's federally required price-transparency
file, flags likely errors, and generates a dispute letter.

## Components (so far)

### backend/ (Python 3.14, FastAPI)
- `main.py` — FastAPI app. One endpoint, `/health`. CORS allows the Vite dev
  server (localhost:5173) to call it.
- `loaders/san_ramon.py` — reads the hospital's CMS-format JSON price file
  from `data/raw/` and writes a normalized CSV to `data/processed/`.
  Every hospital loader must produce the same columns:
  `hospital_id, code, code_type, cdm_code, rev_code, description,
  gross_charge, discounted_cash, setting`.
- `extract/pdf_text.py` — line-item parser for text-based PDFs (pdfplumber).
  A line is a charge if it starts with a date and ends with a money amount.
  Codes are identified by shape (7 digits = CDM, 5 = CPT, 3 = revenue code),
  not by column position, so empty columns don't shift the parse.
- `tests/bills/bill_XX.json` — synthetic bills as ground truth, with an
  `expected` label on every line.
- `tests/make_bill_pdf.py` — renders a bill JSON into a PDF (reportlab).

### frontend/ (React + Vite, plain CSS)
- `src/App.jsx` — placeholder page that calls `/health` and shows the result.

## Data flow (target)
PDF/photo -> extract line items -> user reviews table -> match against
price CSV -> flag rules -> results page -> dispute letter.

## Decisions and why
- **San Ramon Regional first.** Newest file (Apr 2026), JSON, 40 MB. John Muir
  (335 MB zipped CSV) is hospital #2 to prove the loader handles both formats.
- **Only rows with a gross charge are kept** (6,284 of 19,951). The rest are
  insurer-negotiated rates only and can't be used for overcharge checks.
- **Match on CDM first, then CPT/HCPCS, then fuzzy description.** Two reasons:
  4,244 of 6,284 chargemaster rows have no CPT at all (drugs, supplies), and
  the same CPT appears on multiple rows with different prices (e.g. 85025 is
  $1,117 on one CDM and $475 on another). CDM is the hospital's real key.
- **Dedupe on CDM when matching.** Drugs appear twice (rev codes 250 and 637)
  with identical prices.
- **Raw price files are git-ignored** (`data/raw/`). Processed CSVs are
  committed so the deployed app needs no downloads.
- **Synthetic bills are built from real chargemaster rows** with planted
  errors, so every flag has a known correct answer.
- **No LLM anywhere in the pipeline.** Deterministic rules and templates only,
  so every result can be explained.

## Known risks
- Parser assumes one charge per line, amount last. Real bills that wrap
  descriptions or print the date once at the top will need the
  word-coordinate approach (Week 2).
- The planted unbundling pair (96360 + 96374) is unverified until the real
  NCCI table is loaded in Week 3.
- Python 3.14 is very new; if a package fails to install, fall back to 3.12.

## Libraries and why
- fastapi / uvicorn — web framework and server
- pdfplumber — text and coordinates out of text-based PDFs
- reportlab — generate synthetic test bills (test-only)