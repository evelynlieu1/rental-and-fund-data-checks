"""Phase 5a: ask Claude to extract the schema fields from every document of one fund, with page and quote.

The model (Claude Haiku 4.5 on AWS Bedrock, Australian route, same setup as project 1) reads the
page text from data/processed/pages.parquet, up to 50 pages per request, and returns JSON rows:
field, sub_field, value_raw, value_norm, unit, basis, as_at, value_type, pdf_page, quote, confidence.

The field lists are schema.md (LF1) and schema-funds.md (MXT, MA1, REV) WITHOUT their numbers: the model gets
the same instructions a human labeller gets, but never the answers it is scored on.

Run:  python src/3_extract.py LF1           (skips chunks already saved; fund is LF1, MXT, MA1 or REV)
      python src/3_extract.py LF1 --rerun   (calls the model again for every chunk)
Needs AWS credentials with Bedrock access (for example, set AWS_PROFILE). Writes outputs/<fund>/extract/raw/<doc>_<chunk>.json and .../prompt.txt.
The evidence check and the scores are in src/4_score.py.

LF1 run 1 (8 Nov) is kept in outputs/lf1/extract/run1/. 38 of its 139 rows failed the quote check; about 30 of those
quoted the right words but cited the page number PRINTED on the page (PDS 78 for pdf page 80, annual report
29 for 33). Run 2 adds the pdf_page warning, a 12-word quote limit and the category rule below.
"""
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from anthropic import AnthropicBedrock

PROJECT = Path(__file__).resolve().parents[1]

MODEL = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
CHUNK_PAGES = 50  # the 123-page PDS goes in 3 requests; shorter context reads more carefully

FIELDS = """
Background: LF1 (La Trobe Private Credit Fund, ASX:LF1) is a listed trust that invests in two funds:
- 12MIA: the 12 Month Investment Account (called the "12 Month Term Account" before 2026), one account of the
  La Trobe Australian Credit Fund (Australian mortgages). Figures for the whole Credit Fund, or its other
  accounts, are NOT 12MIA figures.
- USPC: the La Trobe US Private Credit Fund, which invests mainly in LGAM Private Credit LLC (US loans).
- plus cash.
The Responsible Entity (RE) and the Manager are two different companies. The word "Fund" means LF1 in the PDS and
the LF1 annual report, but can mean another vehicle elsewhere: decide the vehicle from the context.

Fields (name: vehicle, unit, sub_fields, what to capture, traps):
1. re_identity: the RE. sub_fields legal_name, acn, afsl. Normalise the AFSL/ACN to digits only. An ACL is a credit
   licence, not an AFSL. Don't take roles from structure-diagram text.
2. manager_payment: how the Manager is paid. sub_fields paid_directly_by_lf1 (value_norm: yes / no) and paid_by
   (value_norm exactly one of: "RE out of its own fee", "no fee payable by RE"). unit "category".
3. lf1_re_fee_pct_pa: the RE's own fee on LF1, % p.a. No sub_field. value_type: current rate / estimate /
   constitutional maximum. Not the total fees and costs, not recoverable or indirect costs.
4. lf1_total_fees_and_costs_pct_pa: LF1's management fees and costs. sub_fields re_fee, recoverable, indirect, total.
   Record the basis as printed (NAV or NTA). A 3-month return is not a fee.
5. lgam_performance_fee_pct_of_lf1_nav: the performance fee LF1 bears through LGAM, % p.a. of LF1 NAV.
   sub_fields with_waiver, without_waiver, assumed_uspc_weighting.
6. 12mia_rebate_to_lf1_pct_pa: the rebate the 12MIA's responsible entity pays LF1, % p.a. No sub_field.
   basis "not stated" unless the page says what it is a % of.
7. 12mia_management_costs_pct_pa: the 12MIA's management costs or ICR, % p.a., with the period. No sub_field.
   In a table with one column per account, use the 12 Month Investment Account column, not Total Fund.
8. uspc_lgam_management_fees_pct_pa: sub_fields uspc_fee, uspc_constitutional_max, lgam_base_fee, lgam_recoverable.
9. lf1_target_distribution: sub_field margin_over_rba_pct (the margin over the RBA cash rate); basis = what it is
   net of, as printed. The 12MIA's own benchmark is not LF1's target.
10. lf1_allocation_limits: permitted range of LF1's assets in each holding. sub_fields 12mia_range, uspc_range,
   cash_range. value_norm "min-max", e.g. "10-90"; "no limit" is "0-unlimited". A target weighting is not a limit.
11. lf1_allocation_actual_pct: actual % of LF1 in each holding, with date. sub_fields 12mia, uspc, cash.
   Write "approximately" as "~" in value_norm. Don't derive % from dollar amounts.
12. lf1_investment_in_12mia_aud: LF1's investment in the 12MIA in whole AUD, with date. No sub_field.
   Convert $'000 and $m tables to whole dollars. A loan to buy LF1 units is not this.
13. 12mia_weighted_avg_lvr_pct: the 12MIA's (weighted) average loan-to-value ratio, %, with date. No sub_field.
   Not the whole Credit Fund's LVR, not the US portfolio's LTV.
14. 12mia_max_lvr_pct: the 12MIA's stated maximum LVR, %. No sub_field. The size of an LVR bucket (such as the
   share of loans above some LVR) is not a maximum. An impairment-review trigger is not a lending limit.
15. 12mia_loan_count: number of loans or mortgages in the 12MIA, with date. No sub_field. Not the whole Credit Fund.
16. uspc_weighted_avg_ltv_pct: weighted average loan-to-value of the US portfolio, %, with date. No sub_field.
   Footnote numbers can be fused to the value ("38%7" is 38 with footnote 7); look up the footnote's date.
17. lf1_buyback_policy: sub_fields quarterly_offer_pct, cap_12m_pct, approval_can_lift_cap (yes/no), price_basis
   (text). Put the qualifier ("intends", "up to") in notes. An on-market buy-back is a separate programme.
18. underlying_redemption_cap_pct_per_quarter: redemption cap per quarter of the vehicles LF1 invests in.
   sub_fields uspc, lgam. basis = % of what (units, interests).
"""

SYSTEM = "You extract facts from fund documents for a research analyst. You copy, you never calculate or guess."

PROMPT = """Below are pages {first} to {last} of one document: {doc_name}. Each page starts with <page n=...>, its page
number in the PDF file.

{fields}

Rules:
- One row per value occurrence: if a field appears on several pages, give up to 3 rows for it, the clearest pages.
- value_raw: the value exactly as printed on the page, copied character for character. For a yes/no or category
  sub_field, value_raw is the printed words that show it, and value_norm is the category.
- value_norm: the value cleaned: digits only for numbers (percent points, so 7.5 not 0.075; money in whole AUD),
  or the category text the field asks for.
- quote: at most 12 consecutive words from ONE page that contain value_raw, copied character for character
  (you may drop line breaks). It is checked by code against the page text, so never paraphrase, shorten or join
  words from different places.
- pdf_page: the n in the <page n=...> tag the quote sits under. NOT the page number printed in the page text or in
  a table of contents: those often differ from n, and a wrong page fails the check.
- as_at: YYYY-MM-DD of the date the value describes, if the page or its footnote gives one; otherwise "".
  Never use the document's own date unless the page states it for that value.
- value_type: target, estimate, actual, actual for a period, policy limit, constitutional maximum, current rate,
  or marketing claim. confidence: high, medium or low.
- Only the numbered fields above. Leave out anything you can't quote. If a field isn't in these pages, leave it out:
  never write a "not found" row.

Reply with JSON only, no other text:
{{"extractions": [{{"field": "", "sub_field": "", "vehicle": "", "value_raw": "", "value_norm": "", "unit": "", "basis": "",
"as_at": "", "value_type": "", "pdf_page": 0, "quote": "", "confidence": "", "notes": ""}}]}}

{pages}"""


def parse_json(text):
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


def fields_for(fund):
    if fund == "LF1":
        return FIELDS
    from fund_fields import BACKGROUND, GENERIC_FIELDS  # src/fund_fields.py: the generic schema without numbers
    return BACKGROUND[fund] + GENERIC_FIELDS


def main():
    fund = sys.argv[1].upper() if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "LF1"
    rerun = "--rerun" in sys.argv
    out_dir = PROJECT / "outputs" / fund.lower() / "extract"
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    fields = fields_for(fund)
    (out_dir / "prompt.txt").write_text(f"MODEL: {MODEL}\n\nSYSTEM:\n{SYSTEM}\n\nPROMPT (pages filled in per chunk):\n"
                                        + PROMPT.replace("{fields}", fields), encoding="utf-8")

    profile = None if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") else os.environ.get("AWS_PROFILE")
    client = AnthropicBedrock(aws_region="ap-southeast-2", aws_profile=profile)

    pages = pd.read_parquet(PROJECT / "data" / "processed" / "pages.parquet")
    pages = pages[pages.fund == fund]
    for doc_code, doc in pages.groupby("doc", sort=False):
        doc = doc.sort_values("pdf_page")
        for start in range(0, len(doc), CHUNK_PAGES):
            chunk = doc.iloc[start:start + CHUNK_PAGES]
            first, last = int(chunk.pdf_page.min()), int(chunk.pdf_page.max())
            out = raw_dir / f"{doc_code}_{first:03d}-{last:03d}.json"
            if out.exists() and not rerun:
                print(f"{out.name}: saved already, skipped")
                continue
            page_text = "\n".join(f"<page n={r.pdf_page}>\n{r.text}" for r in chunk.itertuples())
            prompt = PROMPT.format(first=first, last=last,
                                   doc_name=f"{fund} {chunk.doc_type.iloc[0]} ({chunk.file.iloc[0]})",
                                   fields=fields, pages=page_text)
            t0 = time.time()
            msg = client.messages.create(model=MODEL, max_tokens=16000, temperature=0, system=SYSTEM,
                                         messages=[{"role": "user", "content": prompt}])
            reply = msg.content[0].text
            try:
                rows = parse_json(reply)["extractions"]
                error = None
            except Exception as e:  # keep the reply so the failure can be read
                rows, error = [], f"{type(e).__name__}: {e}"
            out.write_text(json.dumps({
                "fund": fund, "doc": doc_code, "doc_type": chunk.doc_type.iloc[0], "file": chunk.file.iloc[0],
                "pages": [first, last], "model": MODEL, "stop_reason": msg.stop_reason,
                "usage": {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens},
                "seconds": round(time.time() - t0, 1), "parse_error": error, "extractions": rows, "raw_reply": reply,
            }, indent=1, ensure_ascii=False), encoding="utf-8")
            print(f"{out.name}: {len(rows)} rows, {msg.usage.input_tokens} in / {msg.usage.output_tokens} out tokens, "
                  f"stop={msg.stop_reason}{', PARSE ERROR ' + error if error else ''}")


if __name__ == "__main__":
    main()
