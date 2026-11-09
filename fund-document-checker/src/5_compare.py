"""Phase 6: compare what one fund's documents say and raise a flag wherever they disagree.

Input: the AI extractions that passed the evidence check (outputs/<fund>/extract/extractions.csv), the ASX
Investment Products report (Sep 2026) and the ASIC AFS licensee register (Oct 2026).

Five kinds of rule:
  1. same field, different value: any two occurrences of a field (across documents, or two pages of one
     document) whose values differ. Two values with different known dates are a time series, not a
     disagreement: they're logged in checks.csv but not flagged.
  2. limit against actual: e.g. the 12MIA's LVR against its stated maximum; allocation against its limits.
  3. ASX report against the fund's documents: MER, the outperformance-fee column, and (generic funds) NTA per unit.
  4. feeder against underlying: rule 1 where one side is an underlying fund's own document (LF1: uar).
  5. entities against the ASIC register: the RE's AFSL and name; the Manager's name or licence.

Every flag gets a stable id. Labels are reviewed by hand and kept in flag_labels.csv (flag_id, label, reason),
so re-running this script never loses them. Labels: real disagreement, extraction error, level mismatch,
date mismatch, no real difference.

Run:  python src/5_compare.py LF1      (or MXT, MA1, REV)
Writes outputs/<fund>/checks.csv (every comparison made) and outputs/<fund>/flags.csv (the disagreements, labelled).
"""
import hashlib
import itertools
import re
import os
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
LABELS = PROJECT / "flag_labels.csv"
ID_SUBFIELDS = {"afsl", "acn", "licence_number"}

# Per fund: which fields feed which rule. LF1 keeps the field names of schema.md; the others use schema-funds.md.
GENERIC = {
    "underlying_docs": set(),
    "skip": {("liquidity_or_buyback", "price_basis")},
    "limits": [("largest_exposure_pct", "actual", "largest_exposure_pct", "limit"),
               ("leverage", "actual", "leverage", "limit"),
               ("offshore_pct", "actual", "offshore_pct", "limit")],
    "range_pairs": ("strategy_mix_pct", "strategy_limits"),  # each strategy's actual against its "min-max" range
    "total_fees": ("total_fees_and_costs_pct_pa", "total"),
    "perf_fee": ("performance_fee", "estimated_pct_pa"),
    "nta": "nta_per_unit",
    "manager": None,  # taken from the manager_identity rows
}
CONFIG = {
    "LF1": {
        "underlying_docs": {"uar"},
        # LF1's field names already carry the vehicle (12mia_, uspc_, lf1_), and its older extractions have no
        # vehicle column; grouping by vehicle would stop a re-extracted document being compared with the rest.
        "group_by_vehicle": False,
        "skip": {("lf1_buyback_policy", "price_basis")},
        "limits": [("12mia_weighted_avg_lvr_pct", "", "12mia_max_lvr_pct", "")]
                  + [("lf1_allocation_actual_pct", h, "lf1_allocation_limits", f"{h}_range") for h in ("12mia", "uspc", "cash")],
        "total_fees": ("lf1_total_fees_and_costs_pct_pa", "total"),
        "perf_fee": ("lgam_performance_fee_pct_of_lf1_nav", "with_waiver"),
        "nta": None,
        "manager": ("La Trobe Financial Services Pty Limited", "pds", 2, "Manager La Trobe Financial Services Pty Limited"),
    },
    "MXT": GENERIC, "MA1": GENERIC, "REV": GENERIC,
}


def numbers(s):
    return [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", str(s))]


def value_key(field, sub_field, v):
    """What two values must share to count as the same."""
    if sub_field in ID_SUBFIELDS:
        digits = re.sub(r"\D", "", str(v))
        # An ABN printed where the ACN should be: an ABN is 2 check digits plus the 9-digit ACN
        return digits[-9:] if sub_field == "acn" and len(digits) == 11 else digits
    n = numbers(v)
    if n:
        return "|".join(f"{x:g}" for x in n)
    t = str(v).lower().replace(" ltd", " limited")
    return re.sub(r"[^a-z0-9]", "", t)


def short(q, words=14):
    w = str(q).split()
    return " ".join(w[:words]) + (" ..." if len(w) > words else "")


def side(prefix, r):
    return {f"{prefix}_doc": r.doc, f"{prefix}_page": r.pdf_page, f"{prefix}_value": r.value_norm,
            f"{prefix}_as_at": r.as_at, f"{prefix}_vehicle": getattr(r, "vehicle", ""), f"{prefix}_quote": short(r.quote)}


class Run:
    def __init__(self, fund):
        self.fund, self.cfg = fund, CONFIG[fund]
        self.checks, self.flags = [], []

    def fid(self, *parts):
        parts = parts if self.fund == "LF1" else (self.fund, *parts)  # LF1 ids predate the other funds
        return "F" + hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:6]

    def check(self, rule, field, sub, result, detail=""):
        self.checks.append({"rule": rule, "field": field, "sub_field": sub, "result": result, "detail": detail})

    def flag(self, rule, field, sub, fid, a, b):
        self.flags.append({"flag_id": fid, "rule": rule, "field": field, "sub_field": sub, **a, **b})
        self.check(rule, field, sub, f"FLAG {fid}")

    # 1 and 4
    def same_field(self, ok):
        under = self.cfg["underlying_docs"]
        ok = ok[[(f, s) not in self.cfg["skip"] for f, s in zip(ok.field, ok.sub_field)]]
        ok = ok.drop_duplicates(["field", "sub_field", "vnorm", "doc", "vkey", "as_at"])
        # Values for different vehicles (the trust against an underlying fund) are never compared with each other.
        # LF1's extraction has no vehicle column, so vnorm is blank there and nothing changes.
        for (field, sub, _), g in ok.groupby(["field", "sub_field", "vnorm"]):
            agreed = set()
            for a, b in itertools.combinations(g.itertuples(), 2):
                if a.vkey == b.vkey:
                    docs = tuple(sorted({a.doc, b.doc}))
                    if len(docs) == 2 and docs not in agreed:  # log one agreement per pair of documents
                        agreed.add(docs)
                        rule = "feeder vs underlying" if under & set(docs) else "same field, different documents"
                        self.check(rule, field, sub, "same",
                                   f"{a.doc} p{a.pdf_page} and {b.doc} p{b.pdf_page}: {a.value_norm} ({a.as_at or 'undated'})")
                    continue
                if a.as_at and b.as_at and a.as_at != b.as_at:
                    self.check("same field", field, sub, "different dates, not compared",
                               f"{a.doc} p{a.pdf_page} {a.value_norm} ({a.as_at}) / {b.doc} p{b.pdf_page} {b.value_norm} ({b.as_at})")
                    continue
                if under & {a.doc, b.doc} and a.doc != b.doc:
                    rule = "feeder vs underlying"
                elif a.doc == b.doc:
                    rule = "same document, different pages"
                else:
                    rule = "same field, different documents"
                fid = self.fid(rule, field, sub, a.doc, a.pdf_page, a.vkey, b.doc, b.pdf_page, b.vkey)
                self.flag(rule, field, sub, fid, side("a", a), side("b", b))

    # 2
    def limits(self, ok):
        pairs = list(self.cfg["limits"])
        if self.cfg.get("range_pairs"):  # each strategy's actual against the range with the same strategy code
            act_f, lim_f = self.cfg["range_pairs"]
            codes = sorted(set(ok[ok.field == act_f].sub_field) & set(ok[ok.field == lim_f].sub_field))
            pairs += [(act_f, c, lim_f, c) for c in codes]
        for act_f, act_s, lim_f, lim_s in pairs:
            acts = ok[(ok.field == act_f) & (ok.sub_field.fillna("") == act_s)]
            lims = ok[(ok.field == lim_f) & (ok.sub_field.fillna("") == lim_s)].drop_duplicates("vkey")
            for a, l in itertools.product(acts.itertuples(), lims.itertuples()):
                x, n = numbers(a.value_norm), numbers(l.value_norm)
                if not x or not n:
                    continue
                lo, hi = (0.0, n[0]) if len(n) == 1 else (n[0], n[1])
                if "unlimited" in str(l.value_norm):
                    hi = float("inf")
                detail = f"{a.doc} p{a.pdf_page} actual {a.value_norm} ({a.as_at}) against {l.doc} p{l.pdf_page} limit {l.value_norm}"
                if lo <= x[0] <= hi:
                    self.check("limit vs actual", act_f, act_s, "within limit", detail)
                else:
                    fid = self.fid("limit", act_f, act_s, a.doc, a.pdf_page, a.vkey, l.doc, l.pdf_page, l.vkey)
                    self.flags.append({"flag_id": fid, "rule": "limit vs actual", "field": act_f, "sub_field": act_s,
                                       **side("a", a), **side("b", l)})
                    self.check("limit vs actual", act_f, act_s, f"FLAG {fid}", detail)

    # 3
    def asx(self, ok):
        # The newest ASX report: the AWS watcher sets ASX_FILE and ASX_AS_AT when a new month is published
        asx_file = os.environ.get("ASX_FILE", "raw/asx/asx-investment-products-sep-2026-abs.xlsx")
        asx_as_at = os.environ.get("ASX_AS_AT", "2026-09-30")
        df = pd.read_excel(PROJECT / "data" / asx_file, "Spotlight LIC List", header=9)
        df.columns = [" ".join(str(c).split()) for c in df.columns]  # header names, not positions: there are blank columns
        row = df[df["ASX Code"] == self.fund].iloc[0]
        nta_date = str(row["NTA Date"])[:10]
        b = lambda v, what, as_at=asx_as_at: {"b_doc": "asx", "b_page": "Spotlight LIC List", "b_value": v,
                                                 "b_as_at": as_at, "b_quote": what}
        f, s = self.cfg["total_fees"]
        for r in ok[(ok.field == f) & (ok.sub_field == s)].itertuples():
            detail = f"{r.doc} p{r.pdf_page} {r.value_norm} against ASX MER {row['MER (% p.a)']}"
            if numbers(r.value_norm)[:1] == numbers(row["MER (% p.a)"]):
                self.check("ASX vs PDS", "MER", s, "same", detail)
            else:
                fid = self.fid("asx", "mer", r.doc, r.pdf_page, r.vkey)
                self.flags.append({"flag_id": fid, "rule": "ASX vs PDS", "field": f, "sub_field": s,
                                   **side("a", r), **b(row["MER (% p.a)"], "MER (% p.a) column")})
                self.check("ASX vs PDS", "MER", s, f"FLAG {fid}", detail)
        f, s = self.cfg["perf_fee"]
        outperf = str(row["Outperf Fee"]).strip().lower()
        for r in ok[(ok.field == f) & (ok.sub_field == s)].drop_duplicates("vkey").itertuples():
            if outperf == "no" and numbers(r.value_norm) and numbers(r.value_norm)[0] > 0:
                fid = self.fid("asx", "outperf", r.doc, r.pdf_page, r.vkey)
                self.flags.append({"flag_id": fid, "rule": "ASX vs PDS", "field": f, "sub_field": s,
                                   **side("a", r), **b(row["Outperf Fee"], "Outperf Fee column")})
                self.check("ASX vs PDS", "outperformance fee", "", f"FLAG {fid}",
                           f"{r.doc} p{r.pdf_page} {r.value_norm}% against ASX '{row['Outperf Fee']}'")
        if self.cfg["nta"]:
            asx_nta = row["NTA Price"]
            for r in ok[(ok.field == self.cfg["nta"]) & (ok.as_at == nta_date)].itertuples():
                detail = f"{r.doc} p{r.pdf_page} {r.value_norm} at {r.as_at} against ASX NTA price {asx_nta}"
                mine, theirs = numbers(r.value_norm)[:1], numbers(asx_nta)[:1]
                places = len(str(r.value_norm).split(".")[1]) if "." in str(r.value_norm) else 0
                if mine and theirs and round(theirs[0], places) == mine[0]:  # $2.00 printed for 2.0017 is the same
                    self.check("ASX vs PDS", "NTA per unit", "", "same", detail)
                else:
                    fid = self.fid("asx", "nta", r.doc, r.pdf_page, r.vkey)
                    self.flags.append({"flag_id": fid, "rule": "ASX vs PDS", "field": self.cfg["nta"], "sub_field": "",
                                       **side("a", r), **b(asx_nta, "NTA Price column", nta_date)})
                    self.check("ASX vs PDS", "NTA per unit", "", f"FLAG {fid}", detail)
        disc = row["Prem/Disc % NTA (pre-tax) at NTA Date"]
        self.check("ASX vs PDS", "ASX extras", "", "recorded",
                   f"MER {row['MER (% p.a)']}, outperformance fee {row['Outperf Fee']}, NTA price {row['NTA Price']}, "
                   f"premium/discount to NTA {disc:.1%} at {nta_date}" if isinstance(disc, float)
                   else f"Premium/discount to NTA {disc} at {nta_date}")

    # 5
    def asic(self, ok):
        reg = pd.read_csv(PROJECT / "data/raw/asic/afs_lic_202610.csv", dtype=str, encoding="utf-8-sig").fillna("")
        b = lambda v, what: {"b_doc": "asic", "b_page": "afs_lic_202610.csv", "b_value": v, "b_as_at": "2026-10",
                             "b_quote": what}
        key = lambda n: value_key("re_identity", "legal_name", n)
        names = ok[(ok.field == "re_identity") & (ok.sub_field == "legal_name")]
        for r in ok[(ok.field == "re_identity") & (ok.sub_field == "afsl")].drop_duplicates(["doc", "vkey"]).itertuples():
            hit = reg[reg.AFS_LIC_NUM.str.lstrip("0") == r.vkey.lstrip("0")]
            if hit.empty:
                fid = self.fid("asic", "missing", r.doc, r.vkey)
                self.flags.append({"flag_id": fid, "rule": "entity vs ASIC register", "field": "re_identity",
                                   "sub_field": "afsl", **side("a", r), **b("", "no licence with this number")})
                self.check("entity vs ASIC register", "re_identity", "afsl", f"FLAG {fid}", r.vkey)
                continue
            reg_name = hit.AFS_LIC_NAME.iloc[0]
            doc_names = names[names.doc == r.doc]
            same = doc_names.empty or any(key(n) == key(reg_name) for n in doc_names.value_norm)
            self.check("entity vs ASIC register", "re_identity", "afsl",
                       "current licence, name matches" if same else "name differs",
                       f"{r.doc} p{r.pdf_page} AFSL {r.vkey}: register name {reg_name}, licensed since {hit.AFS_LIC_START_DT.iloc[0]}")
            if not same:
                fid = self.fid("asic", "name", r.doc, r.vkey)
                self.flags.append({"flag_id": fid, "rule": "entity vs ASIC register", "field": "re_identity",
                                   "sub_field": "legal_name", **side("a", doc_names.iloc[0]), **b(reg_name, f"AFSL {r.vkey}")})
        if self.cfg["manager"]:  # LF1: the Manager's name as printed in the PDS
            name, doc, page, quote = self.cfg["manager"]
            managers = [(name, {"a_doc": doc, "a_page": page, "a_value": name, "a_as_at": "", "a_quote": quote}, "")]
        else:  # one row per distinct manager name the AI extracted, with any licence number on the same page
            mrows = ok[ok.field == "manager_identity"]
            managers = []
            for r in mrows[mrows.sub_field == "legal_name"].drop_duplicates("vkey").itertuples():
                lic = mrows[(mrows.sub_field == "licence_number") & (mrows.doc == r.doc) & (mrows.pdf_page == r.pdf_page)]
                managers.append((r.value_norm, side("a", r), lic.vkey.iloc[0] if len(lic) else ""))
        for name, a, lic in managers:
            by_name = reg[reg.AFS_LIC_NAME.map(key) == key(name)]
            by_num = reg[reg.AFS_LIC_NUM.str.lstrip("0") == lic.lstrip("0")] if lic else reg.iloc[0:0]
            if not by_name.empty or not by_num.empty:
                hit = by_name if not by_name.empty else by_num
                self.check("entity vs ASIC register", "manager", "", "current licence",
                           f"{name}: AFSL {hit.AFS_LIC_NUM.iloc[0]} {hit.AFS_LIC_NAME.iloc[0]}")
                continue
            fid = self.fid("asic", "manager", name)
            self.flags.append({"flag_id": fid, "rule": "entity vs ASIC register", "field": "manager_identity",
                               "sub_field": "legal_name", **a, **b("", "no AFS licensee with this name")})
            self.check("entity vs ASIC register", "manager", "", f"FLAG {fid}", name)


def main():
    fund = sys.argv[1].upper() if len(sys.argv) > 1 else "LF1"
    out = PROJECT / "outputs" / fund.lower()
    ext = pd.read_csv(out / "extract" / "extractions.csv", dtype=str, encoding="utf-8-sig").fillna("")
    ok = ext[ext.check.str.startswith("pass") & (ext.chunk != "PLANTED")].copy()
    ok["vkey"] = [value_key(f, s, v) for f, s, v in zip(ok.field, ok.sub_field, ok.value_norm)]
    ok = ok[ok.vkey != ""]  # a passing quote with no normalised value can't be compared
    use_vehicle = CONFIG[fund].get("group_by_vehicle", True) and "vehicle" in ok
    vehicle = ok["vehicle"] if use_vehicle else pd.Series("", index=ok.index)
    ok["vnorm"] = [re.sub(r"[^a-z0-9]", "", str(v).lower()) for v in vehicle]

    run = Run(fund)
    run.same_field(ok)
    run.limits(ok)
    run.asx(ok)
    run.asic(ok)

    flags = pd.DataFrame(run.flags).drop_duplicates("flag_id")
    if LABELS.exists():
        labels = pd.read_csv(LABELS, dtype=str, encoding="utf-8-sig").fillna("")
        flags = flags.merge(labels[["flag_id", "label", "reason", "reviewed_by"]], on="flag_id", how="left")
    else:
        flags["label"], flags["reason"], flags["reviewed_by"] = "", "", ""
    flags[["label", "reason", "reviewed_by"]] = flags[["label", "reason", "reviewed_by"]].fillna("")
    flags.insert(0, "fund", fund)
    flags.to_csv(out / "flags.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(run.checks).to_csv(out / "checks.csv", index=False, encoding="utf-8-sig")

    print(f"{fund}: {len(run.checks)} comparisons, {len(flags)} flags")
    print(flags.groupby("rule").size().to_string())
    unlabelled = flags[flags.label == ""]
    if len(unlabelled):
        print(f"\n{len(unlabelled)} flags still need a label in flag_labels.csv")
    else:
        print("\n" + flags.groupby("label").size().to_string())


if __name__ == "__main__":
    main()
