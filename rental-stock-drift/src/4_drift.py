"""Phase 4: how much has rental stock grown since the 2021 Census, postcode by postcode?

stock_now  = census_2021 x (bonds_now / bonds_2021)
drift      = stock_now / census_2021 - 1      (= bond growth since 2021)
multiplier = census_2021 / stock_now          (a vacancy rate built on 2021 stock, times this, gives the rate on today's stock)

Note: drift is the same whichever renter definition you use, because the Census count
cancels out. The definition only changes stock_now and which postcodes pass the size limit.

Run:  python src/4_drift.py
Writes outputs/top20.csv (top 20 per state) and outputs/drift_all.csv (every postcode).
"""
import importlib
from pathlib import Path

import pandas as pd

load = importlib.import_module("2_load")
OUT = Path(__file__).resolve().parents[1] / "outputs"

MIN_RENTERS = 300  # a rate on fewer rentals jumps around on one listing

# state: (bonds loader, base period near Census night, alternative base, latest period)
STATES = {
    "NSW": (load.load_nsw_bonds_held, "2021-12", None, "2025-12"),
    "QLD": (load.load_qld_bonds_held, "2021-06", "2021-09", "2026-09"),
}


def drift_table(state, bonds, base, now, census):
    b = bonds.pivot_table(index="postcode", columns="period", values="value")
    df = census[census["state"] == state].merge(
        b[[base, now]].rename(columns={base: "bonds_2021", now: "bonds_now"}),
        left_on="postcode", right_index=True, how="inner")
    df = df[df["bonds_2021"] > 0]  # no growth rate without a base
    df["census_2021"] = df["private"]  # main definition: private renters
    df["drift"] = df["bonds_now"] / df["bonds_2021"] - 1
    df["stock_now"] = df["census_2021"] * (1 + df["drift"])
    df["multiplier"] = df["census_2021"] / df["stock_now"]
    # Phase 3 check: if bonds and Census disagree badly at 2021, the growth rate is less trustworthy
    ratio = df["bonds_2021"] / df["private"]
    df["ratio_2021_flag"] = (ratio < 0.5) | (ratio > 2.0)
    df["state"], df["base"], df["now"] = state, base, now
    return df


def top20(df, size_col, min_size):
    return set(df[df[size_col] >= min_size].nlargest(20, "drift")["postcode"])


census = load.load_census_renters()
tables, tops = [], []
for state, (loader, base, alt_base, now) in STATES.items():
    bonds = loader()
    main = drift_table(state, bonds, base, now, census)
    eligible = main[main["census_2021"] >= MIN_RENTERS]
    print(f"{state}: {len(main)} postcodes with bonds at both dates; "
          f"{len(main) - len(eligible)} dropped by the {MIN_RENTERS}-renter minimum; "
          f"{len(eligible)} ranked. Bonds {base} -> {now}.")

    # Variants: other definition for the size limit, a stricter limit, and (QLD) a different base quarter
    variants = {
        "private>=300": top20(main, "private", 300),
        "all>=300": top20(main, "all_renters", 300),
        "private>=500": top20(main, "private", 500),
    }
    if alt_base:
        variants[f"base {alt_base}"] = top20(drift_table(state, bonds, alt_base, now, census), "private", 300)

    top = eligible.nlargest(20, "drift").copy()
    top["stays_top20_all_variants"] = top["postcode"].map(lambda p: all(p in v for v in variants.values()))
    top["variants_in"] = top["postcode"].map(lambda p: sum(p in v for v in variants.values()))
    print(f"  top 20 that stay in all {len(variants)} variants: {top['stays_top20_all_variants'].sum()}\n")
    tables.append(main)
    tops.append(top)

cols = ["state", "postcode", "census_2021", "bonds_2021", "bonds_now", "stock_now", "drift", "multiplier",
        "stays_top20_all_variants", "variants_in", "ratio_2021_flag", "base", "now"]
OUT.mkdir(exist_ok=True)
pd.concat(tops)[cols].round(3).to_csv(OUT / "top20.csv", index=False)
pd.concat(tables)[cols[:8] + ["ratio_2021_flag", "all_renters", "base", "now"]].round(3) \
    .sort_values(["state", "drift"], ascending=[True, False]).to_csv(OUT / "drift_all.csv", index=False)
print(pd.concat(tops)[cols[:10]].round(2).to_string(index=False))
