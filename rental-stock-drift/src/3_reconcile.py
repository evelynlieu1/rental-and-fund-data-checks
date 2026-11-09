"""Phase 3: join 2021 Census renters to bonds held around Census night (10 Aug 2021).

NSW: bonds at Dec 2021 (the only date published).
QLD: bonds at Jun 2021 (41 days before Census night; Sep 2021 is 51 days after).

Run:  python src/3_reconcile.py
Writes outputs/ratios_2021_<state>.csv and outputs/unmatched_2021_<state>.csv.
"""
import importlib
from pathlib import Path

import pandas as pd

load = importlib.import_module("2_load")  # file names starting with a number need this
PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "outputs"

# Why each unmatched postcode doesn't join: researched and double-checked on 8 Nov 2026
# (place, category, note and a source link per postcode).
NOTES = pd.read_csv(PROJECT / "unmatched_notes.csv", dtype={"postcode": str})


def reconcile(state, bonds, period):
    bonds = bonds[bonds["period"] == period].rename(columns={"value": "bonds_2021"})
    census = load.load_census_renters()
    census = census[census["state"] == state]  # for NSW this also drops Canberra (ACT bonds are held by the ACT)

    # Join on postcode. "outer" keeps postcodes that don't match, so none are dropped silently.
    df = census.merge(bonds[["postcode", "bonds_2021"]], on="postcode", how="outer", indicator=True)
    print(f"--- {state}, bonds at {period} ---")
    print(df["_merge"].value_counts().to_string())

    # Ratios where both sides exist
    both = df[df["_merge"] == "both"].copy()
    both["ratio_private"] = both["bonds_2021"] / both["private"]
    both["ratio_all"] = both["bonds_2021"] / both["all_renters"]
    print(f"{state} ratio, private: {both['bonds_2021'].sum() / both['private'].sum():.3f}")
    print(f"{state} ratio, all renters: {both['bonds_2021'].sum() / both['all_renters'].sum():.3f}")

    # Unmatched list, with a note for each code we understand
    unmatched = df[df["_merge"] != "both"].copy()
    unmatched["side"] = unmatched["_merge"].map({"left_only": "census only", "right_only": "bonds only"})
    notes = NOTES[NOTES["state"] == state].set_index("postcode")["note"]
    unmatched["note"] = unmatched["postcode"].map(notes).fillna("")
    is_act = unmatched["postcode"].map(load.state_of) == "ACT"
    unmatched.loc[is_act, "note"] = "ACT postcode, bond lodged in NSW by mistake or for a cross-border address"
    print(f"Unmatched: {len(unmatched)} postcodes, {(unmatched['note'] == '').sum()} without a note\n")

    OUT.mkdir(exist_ok=True)
    cols = ["postcode", "private", "all_renters", "bonds_2021"]
    both[cols + ["ratio_private", "ratio_all"]].to_csv(OUT / f"ratios_2021_{state.lower()}.csv", index=False)
    unmatched[cols + ["side", "note"]].sort_values("postcode").to_csv(OUT / f"unmatched_2021_{state.lower()}.csv", index=False)


reconcile("NSW", load.load_nsw_bonds_held(), "2021-12")
reconcile("QLD", load.load_qld_bonds_held(), "2021-06")
