"""Turn the raw files into tidy tables.

Bonds: postcode, period, value. Census renters: postcode, state, private, all_renters.

Postcodes are kept as text ("2000"), never numbers.
Run:  python src/2_load.py   (prints the state totals to check against STEPS.md)
"""
from pathlib import Path
import zipfile

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def load_nsw_bonds_held():
    """NSW bonds held by postcode, one file per December."""
    tables = []
    for path in sorted((RAW / "nsw_bonds_held").glob("rentalbond_bondsheld_*.xlsx")):
        # Sheet names differ between years, so read the first sheet.
        # Rows 0-2 are a title and the header, so skip them.
        df = pd.read_excel(path, sheet_name=0, skiprows=3, header=None, names=["postcode", "value"])
        df = df.dropna(subset=["postcode"])
        df["postcode"] = df["postcode"].astype(int).astype(str).str.zfill(4)
        df["period"] = path.stem.split("_")[-1]  # e.g. "2021-12"
        tables.append(df)
    return pd.concat(tables)[["postcode", "period", "value"]]


def load_qld_bonds_held(dwelling="All dwellings"):
    """QLD bonds held by postcode and quarter, for one dwelling type."""
    raw = pd.read_excel(RAW / "qld_rta" / "rta-bond-statistics.xlsx", sheet_name="3 pc-all-bonds", header=None)

    # Rows 5 and 6 hold the month and year of each quarter column; join them into "2021-06".
    months = {"Mar": "03", "Jun": "06", "Sep": "09", "Dec": "12"}
    periods = {}
    for col in raw.columns[4:]:
        month, year = raw.iloc[5, col], raw.iloc[6, col]
        if month in months:
            periods[col] = f"{int(year)}-{months[month]}"

    body = raw.iloc[8:, [2, 3] + list(periods)].copy()
    body.columns = ["postcode", "dwelling"] + list(periods.values())
    body = body[body["dwelling"] == dwelling]
    body["postcode"] = body["postcode"].astype(int).astype(str).str.zfill(4)

    tidy = body.melt(id_vars="postcode", value_vars=list(periods.values()), var_name="period", value_name="value")
    # The sheet mixes text and numbers, so pandas keeps values as generic "object".
    # Make them real numbers, otherwise dividing by 0 crashes instead of giving inf.
    tidy["value"] = pd.to_numeric(tidy["value"])
    return tidy.dropna(subset=["value"])


def state_of(postcode):
    """NSW, ACT or QLD from a 4-digit postcode. ACT codes sit inside the 2xxx range."""
    pc = int(postcode)
    if 2600 <= pc <= 2618 or 2900 <= pc <= 2920:
        return "ACT"
    if 2000 <= pc <= 2999:
        return "NSW"
    if 4000 <= pc <= 4999:
        return "QLD"
    return "other"


def load_census_renters():
    """2021 Census table G37: renting households per postal area, two definitions."""
    zip_path = RAW / "abs_census" / "2021_GCP_POA_for_AUS_short-header.zip"
    with zipfile.ZipFile(zip_path) as z:
        g37 = pd.read_csv(z.open("2021 Census GCP Postal Areas for AUS/2021Census_G37_AUST_POA.csv"))

    out = pd.DataFrame()
    out["postcode"] = g37["POA_CODE_2021"].str.replace("POA", "")
    out["state"] = out["postcode"].map(state_of)
    # Private = real estate agent + person not in the same household
    out["private"] = g37["R_RE_Agt_Total"] + g37["R_Psn_not_in_s_hh_Total"]
    # All renters = every landlord type, including state and community housing and not stated
    out["all_renters"] = g37["R_Tot_Total"]
    return out


if __name__ == "__main__":
    nsw = load_nsw_bonds_held()
    print("NSW bonds held by December (expect 930,787 in 2021 and 980,458 in 2025):")
    print(nsw.groupby("period")["value"].sum().map("{:,.0f}".format).to_string())
    print("NSW postcodes per year:", nsw.groupby("period")["postcode"].nunique().to_dict())

    qld = load_qld_bonds_held()
    totals = qld.groupby("period")["value"].sum()
    print("\nQLD bonds held, all dwellings (expect 612,606 at 2021-06 and 628,557 at 2026-09):")
    print(totals.loc[["2021-06", "2026-09"]].map("{:,.0f}".format).to_string())
    print("QLD postcodes:", qld["postcode"].nunique())

    census = load_census_renters()
    print("\nCensus 2021 renting households")
    print("(expect NSW + ACT together: 830,067 private, 996,463 all, 638 areas; QLD: 517,077, 618,479, 433)")
    by_state = census.groupby("state")[["private", "all_renters"]].sum()
    by_state["areas"] = census.groupby("state").size()
    print(by_state.to_string())
