"""Phase 2: turn each fund PDF into page-by-page text.

One row per page: fund, doc, doc_type, doc_date, file, pdf_page, printed_page, n_chars, text.
All four funds (LF1, MXT, MA1, REV) go in one file; filter by fund.
pdf_page counts from 1 in the PDF file; printed_page is the number printed on the page
(often different, because covers and contents pages are unnumbered), or blank if none was found.

Run:  python src/2_pages.py
Writes data/processed/pages.parquet. The text is copied from copyright documents, so it
stays in data/ (never committed) and data/NOSYNC.txt keeps it off the public bucket.
"""
import re
from pathlib import Path

import fitz  # PyMuPDF

DATA = Path(__file__).resolve().parents[1] / "data"

# fund, short doc code, doc_type, the date the document speaks for, expected pages. VERSIONS.md explains the
# LF1 roadshow date. The doc code is what every later script and output uses ("pds", "ar", "monthly_08"...).
DOCS = {
    "raw/lf1/lf1_pds_2025-05-26.pdf": ("LF1", "pds", "pds", "2025-05-26", 123),
    "raw/lf1/lf1_tmd_2025-05-26.pdf": ("LF1", "tmd", "tmd", "2025-05-26", 7),
    "raw/lf1/lf1_faqs.pdf": ("LF1", "faqs", "faqs", None, 4),
    "raw/lf1/lf1_monthly_fund_profile_2026-08.pdf": ("LF1", "profile", "monthly_profile", "2026-08-31", 6),
    "raw/lf1/lf1_annual_report_fy2026.pdf": ("LF1", "ar", "annual_report", "2026-06-30", 44),
    "raw/lf1/la_trobe_australian_credit_fund_annual_report_latest.pdf": ("LF1", "uar", "underlying_fund_annual_report", "2026-06-30", 48),
    "raw/lf1/lf1_roadshow_deck_2026-07.pdf": ("LF1", "deck", "roadshow_deck", "2026-10", 18),
    # Added 8 Nov 2026: the other three funds
    "raw/mxt/mxt_pds_2020-01-24_with_spds.pdf": ("MXT", "pds", "pds_with_spds", "2020-01-24", 127),
    "raw/mxt/mxt_tmd_2025-10-10.pdf": ("MXT", "tmd", "tmd", "2025-10-10", 7),
    "raw/mxt/mxt_monthly_report_2026-06.pdf": ("MXT", "monthly_06", "monthly_report", "2026-06-30", 2),
    "raw/mxt/mxt_monthly_report_2026-07.pdf": ("MXT", "monthly_07", "monthly_report", "2026-07-31", 2),
    "raw/mxt/mxt_monthly_report_2026-08.pdf": ("MXT", "monthly_08", "monthly_report", "2026-08-31", 2),
    "raw/mxt/mxt_portfolio_report_2026-06.pdf": ("MXT", "portfolio", "portfolio_report", "2026-06-30", 22),
    "raw/ma1/ma1_pds_2025-01-20.pdf": ("MA1", "pds", "pds", "2025-01-20", 120),
    "raw/ma1/ma1_supplementary_pds_2025-02-07.pdf": ("MA1", "spds", "supplementary_pds", "2025-02-07", 15),
    "raw/ma1/ma1_investor_update_2026-09.pdf": ("MA1", "update", "investor_update", "2026-09-30", 47),
    "raw/ma1/ma1_appendix4e_annual_report_fy2026.pdf": ("MA1", "ar", "annual_report", "2026-06-30", 51),
    "raw/rev/rev_pds_2025-08-19.pdf": ("REV", "pds", "pds", "2025-08-19", 124),
    "raw/rev/rev_factsheet_2025-08.pdf": ("REV", "factsheet", "factsheet", "2025-08", 5),
    "raw/rev/rev_investment_report_2026-09.pdf": ("REV", "report", "investment_report", "2026-09-30", 10),
    "raw/rev/rev_rg240_report_2026-06.pdf": ("REV", "rg240", "rg240_update", "2026-06-30", 2),
}


def printed_page_number(text):
    """A page number printed alone on one of the first or last 3 lines, if any."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[-3:] + lines[:3]:
        m = re.fullmatch(r"(?:Page\s+)?(\d{1,3})", line, flags=re.I)
        if m:
            return m.group(1)
    return None


def page_rows(path, file):
    """The rows for one PDF. Also used by the AWS watcher (aws/watch.py), which has no pandas."""
    fund, doc, doc_type, doc_date, _ = DOCS[file]
    rows = []
    with fitz.open(path) as pdf:
        for i, page in enumerate(pdf, start=1):
            text = page.get_text("text")
            rows.append({"fund": fund, "doc": doc, "doc_type": doc_type, "doc_date": doc_date, "file": file,
                         "pdf_page": i, "printed_page": printed_page_number(text),
                         "n_chars": len(text.strip()), "text": text})
    return rows


def main():
    import pandas as pd  # imported here so the AWS watcher can use page_rows without pandas

    rows = []
    for file, (fund, doc, doc_type, doc_date, expected) in DOCS.items():
        doc_rows = page_rows(DATA / file, file)
        rows += doc_rows
        flag = "ok" if len(doc_rows) == expected else f"EXPECTED {expected}"
        print(f"{fund:4} {doc:11} {len(doc_rows):4} pages  {flag}")

    pages = pd.DataFrame(rows)
    out = DATA / "processed" / "pages.parquet"
    out.parent.mkdir(exist_ok=True)
    pages.to_parquet(out, index=False)

    nearly_empty = pages[pages["n_chars"] < 100]
    print(f"\n{len(pages)} pages saved to {out.relative_to(DATA.parent)}")
    print(f"{len(nearly_empty)} pages with under 100 characters (images or scans?): "
          f"{nearly_empty.groupby(['fund', 'doc'])['pdf_page'].apply(list).to_dict()}")
    print(f"printed page number found on {pages['printed_page'].notna().sum()} of {len(pages)} pages")


if __name__ == "__main__":
    main()
