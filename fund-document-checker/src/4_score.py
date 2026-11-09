"""Phase 5b: check the AI's evidence in plain Python, then score it against the answer key (LF1 only: gold/lf1.csv).

Evidence check (a row that fails is dropped; case, spaces, line breaks and punctuation are ignored):
  1. the quote appears, word for word, in that document
  2. it is on the page the model cited ("pass"); or, if not, on exactly one other page, which is then used
     ("pass (page fixed)"). Run 1 showed the model often cites the page number PRINTED on the page, so the
     page is taken from code, never from the model.
  3. value_raw appears inside the quote
  A weaker pass, "pass (table)", added 8 Nov for the three other funds: a quote that is only a short label plus
  the value (8 words or fewer), where the PDF text puts the label and the number apart, passes if the value is
  on the page and every label word is within 300 characters of it. These rows are kept apart in the counts.
One planted fake row per fund (a real value with an invented quote) proves the check catches what it should.

Scores (only rows that pass the check):
  recall     of the answer-key rows, how many the AI found (same field, sub_field and document, same value).
             For a "not stated" key row, a hit means the AI returned nothing there.
  precision  of the AI rows on a page the answer key covers for that field, how many have the key's value.
             AI rows on other pages can't be scored against this key and are counted as "unscored".

Run:  python src/4_score.py LF1                              (the latest run, outputs/lf1/extract/raw)
      python src/4_score.py LF1 outputs/lf1/extract/run1     (an earlier run kept in its own folder)
      python src/4_score.py MXT                              (no answer key: evidence check only)
Writes extractions.csv (every row with its check result), scores_by_field.csv, gold_hits.csv and summary.json
in the run's folder. cited_page is what the model said; pdf_page is the page the code found.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
NO_SUB_FIELD = {"lf1_re_fee_pct_pa", "12mia_rebate_to_lf1_pct_pa", "12mia_management_costs_pct_pa",
                "lf1_investment_in_12mia_aud", "12mia_weighted_avg_lvr_pct", "12mia_max_lvr_pct",
                "12mia_loan_count", "uspc_weighted_avg_ltv_pct"}


def squash(s):
    """Lowercase letters, digits, % and . only: 'AFSL 222 213' and 'afsl222213' compare equal."""
    s = unicodedata.normalize("NFKC", str(s)).lower()
    return re.sub(r"[^a-z0-9%.]", "", s)


def numbers(s):
    """'~59' -> [59.0]; '20-100' -> [20.0, 100.0]; '110,200,000' -> [110200000.0]; 'no' -> []."""
    return [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", str(s))]


def same_value(a, b):
    na, nb = numbers(a), numbers(b)
    if na or nb:
        return len(na) == len(nb) and all(abs(x - y) <= 1e-6 * max(1, abs(y)) for x, y in zip(na, nb))
    return str(a).strip().lower() == str(b).strip().lower()


try:
    from fund_fields import NO_SUB_FIELD_GENERIC
    NO_SUB_FIELD |= NO_SUB_FIELD_GENERIC
except ImportError:
    pass


def key_sub(field, sub_field):
    return "" if field in NO_SUB_FIELD else str(sub_field or "").strip().lower()


def load_ai(run, fund):
    rows = []
    for path in sorted((run / "raw").glob("*.json")):
        chunk = json.loads(path.read_text(encoding="utf-8"))
        for r in chunk["extractions"]:
            rows.append({"doc": chunk["doc"], "chunk": path.name, **r})
    ai = pd.DataFrame(rows).fillna("")
    if fund == "LF1":  # a true value (the PDS's 80% maximum LVR) with a quote the page doesn't contain
        fake = {"doc": "pds", "chunk": "PLANTED", "field": "12mia_max_lvr_pct", "sub_field": "", "value_raw": "80%",
                "value_norm": "80", "unit": "%", "pdf_page": 48, "quote": "the maximum LVR on any single loan is 80%",
                "confidence": "high", "notes": "planted by hand to test the check"}
    else:  # the first value the model returned, with an invented sentence around it
        first = ai.iloc[0]
        fake = {**first.to_dict(), "chunk": "PLANTED", "notes": "planted by hand to test the check",
                "quote": f"the trust confirms the figure is {first.value_raw} for this measure"}
    return pd.concat([ai, pd.DataFrame([fake])], ignore_index=True).fillna("")


def table_match(quote, value_raw, page):
    """A table cell: the quote is a short label plus the value, but the extracted text separates the two.
    Passes if the value is on the page and every label word is within 300 characters of it."""
    v = squash(value_raw)
    if not re.search(r"\d", v) or v not in squash(quote):
        return False
    label = re.sub(re.escape(str(value_raw)), " ", str(quote), flags=re.I)
    if not 1 <= len(label.split()) <= 8:
        return False
    words = [squash(w) for w in re.findall(r"[A-Za-z]{3,}", label)]
    start = page.find(v)
    while start != -1:
        window = page[max(0, start - 300):start + len(v) + 300]
        if all(w in window for w in words):
            return True
        start = page.find(v, start + 1)
    return False


def evidence_check(ai, pages):
    """The page comes from code, not from the model: the model often cites the page number printed on the page."""
    docs = {d: list(zip(g.pdf_page.astype(int), g.text.map(squash))) for d, g in pages.groupby("doc")}
    checks, final_pages = [], []
    for r in ai.itertuples():
        q = squash(r.quote)
        on = [n for n, t in docs[r.doc] if q and q in t]
        try:
            cited = int(r.pdf_page)
        except (TypeError, ValueError):
            cited = None
        page = None
        table_on = [] if (on or not q) else [n for n, t in docs[r.doc] if table_match(r.quote, r.value_raw, t)]
        if not q:
            check = "fail: no quote"
        elif not on and cited in table_on:
            check, page = "pass (table)", cited
        elif not on and len(table_on) == 1:
            check, page = "pass (table, page fixed)", table_on[0]
        elif not on:
            check = "fail: quote not in document"
        elif cited in on:
            check, page = "pass", cited
        elif len(on) == 1:
            check, page = "pass (page fixed)", on[0]
        else:
            check = "fail: wrong page, quote on several pages"
        if page is not None and squash(r.value_raw) not in q:
            check = "fail: value not in quote"
        checks.append(check)
        final_pages.append(page if page is not None else "")
    ai["cited_page"] = ai["pdf_page"]
    ai["pdf_page"] = final_pages
    ai["check"] = checks
    ai["quote_words"] = ai["quote"].str.split().str.len()
    return ai


def score(ai, gold):
    ok = ai[ai.check.str.startswith("pass")].copy()
    ok["key"] = [f"{f}|{key_sub(f, s)}|{d}" for f, s, d in zip(ok.field, ok.sub_field, ok.doc)]
    gold = gold.copy()
    gold["key"] = [f"{f}|{key_sub(f, s)}|{d}" for f, s, d in zip(gold.field, gold.sub_field, gold.doc)]

    # recall: one line per answer-key row
    hits = []
    for g in gold.itertuples():
        cand = ok[ok.key == g.key]
        if g.status == "not stated":
            hit, got = cand.empty, "; ".join(cand.value_norm.astype(str))
        else:
            match = cand[[same_value(v, g.value_norm) for v in cand.value_norm]]
            hit, got = not match.empty, "; ".join(f"{v} (p{p})" for v, p in zip(cand.value_norm, cand.pdf_page))
        hits.append({"row": g.row, "field": g.field, "sub_field": g.sub_field, "doc": g.doc, "pdf_page": g.pdf_page,
                     "gold_value": g.value_norm if g.status == "found" else "not stated",
                     "labelled_by": g.labelled_by, "ai_values_for_field_and_doc": got, "hit": hit})
    hits = pd.DataFrame(hits)

    # precision: AI rows on a page the key covers for that field and document, or on a "not stated" key.
    # Also wrong: a value the key holds for a DIFFERENT field on the same page (the AI filed it under the wrong field),
    # except the RE fee, which is legitimately both its own field and the re_fee part of the total.
    gold_pages = {(k, str(p)) for k, p, s in zip(gold.key, gold.pdf_page, gold.status) if s == "found"}
    not_stated = {k for k, s in zip(gold.key, gold.status) if s == "not stated"}
    same_thing = {"lf1_re_fee_pct_pa", "lf1_total_fees_and_costs_pct_pa|re_fee"}
    judged, why = [], []
    for r in ok.itertuples():
        if r.key in not_stated:
            judged.append(False); why.append("key says not stated")
        elif (r.key, str(r.pdf_page)) in gold_pages:
            values = gold[(gold.key == r.key) & (gold.pdf_page.astype(str) == str(r.pdf_page))].value_norm
            good = any(same_value(r.value_norm, v) for v in values)
            judged.append(good); why.append("correct" if good else "wrong value")
        else:
            page = gold[(gold.doc == r.doc) & (gold.pdf_page.astype(str) == str(r.pdf_page)) & (gold.field != r.field)
                        & (gold.status == "found")]
            mine = r.field if r.field in NO_SUB_FIELD else f"{r.field}|{r.sub_field}"
            clash = [g for g in page.itertuples() if same_value(r.value_norm, g.value_norm)
                     and not {mine, g.field if g.field in NO_SUB_FIELD else f"{g.field}|{g.sub_field}"} <= same_thing]
            if clash:
                judged.append(False); why.append(f"wrong field: the key has this value as {clash[0].field}")
            else:
                judged.append(None); why.append("unscored (page not in the key)")
    ok["correct"], ok["judgement"] = judged, why
    return ok, hits


def main():
    args = [a for a in sys.argv[1:]]
    fund = args[0].upper() if args else "LF1"
    run = PROJECT / args[1] if len(args) > 1 else PROJECT / "outputs" / fund.lower() / "extract"
    pages = pd.read_parquet(PROJECT / "data" / "processed" / "pages.parquet")
    pages = pages[pages.fund == fund]
    ai = evidence_check(load_ai(run, fund), pages)
    real = ai[ai.chunk != "PLANTED"]
    summary = {
        "fund": fund,
        "ai_rows": len(real),
        "check": real.check.value_counts().to_dict(),
        "planted_fake": ai[ai.chunk == "PLANTED"].check.iloc[0],
        "quotes_over_15_words": int((real.quote_words >= 15).sum()),
    }
    gold_file = PROJECT / "gold" / f"{fund.lower()}.csv"
    if not gold_file.exists():
        ai.to_csv(run / "extractions.csv", index=False, encoding="utf-8-sig")
        summary["scores"] = "no answer key for this fund"
        (run / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
        print(json.dumps(summary, indent=1))
        return

    gold = pd.read_csv(gold_file, dtype=str, encoding="utf-8-sig").fillna("")
    ok, hits = score(ai, gold)
    ai = ai.join(ok[["correct", "judgement"]])
    ai.to_csv(run / "extractions.csv", index=False, encoding="utf-8-sig")
    hits.to_csv(run / "gold_hits.csv", index=False, encoding="utf-8-sig")
    scored = ok[ok.correct.notna()]

    by_field = []
    for field in gold.field.unique():
        h, s = hits[hits.field == field], scored[scored.field == field]
        by_field.append({"field": field, "key_rows": len(h), "found": int(h.hit.sum()),
                         "recall": round(h.hit.mean(), 2), "ai_rows_scored": len(s),
                         "ai_rows_correct": int(s.correct.sum()),
                         "precision": round(s.correct.mean(), 2) if len(s) else None})
    by_field = pd.DataFrame(by_field)
    by_field.to_csv(run / "scores_by_field.csv", index=False)

    summary.update({
        "recall_all": f"{int(hits.hit.sum())}/{len(hits)} = {hits.hit.mean():.0%}",
        "recall_evelyn_rows": f"{int(hits[hits.labelled_by == 'evelyn'].hit.sum())}/{(hits.labelled_by == 'evelyn').sum()}",
        "recall_claude_rows": f"{int(hits[hits.labelled_by == 'claude'].hit.sum())}/{(hits.labelled_by == 'claude').sum()}",
        "precision": f"{int(scored.correct.sum())}/{len(scored)} = {scored.correct.mean():.0%}",
        "ai_rows_unscored": int(ok.correct.isna().sum()),
    })
    (run / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    print(by_field.to_string(index=False))
    print("\nMissed answer-key rows:")
    print(hits[~hits.hit][["row", "field", "sub_field", "doc", "gold_value", "ai_values_for_field_and_doc"]].to_string(index=False))
    print("\nWrong AI rows (scored):")
    print(scored[scored.correct == False][["field", "sub_field", "doc", "pdf_page", "value_norm", "judgement"]].to_string(index=False))


if __name__ == "__main__":
    main()
