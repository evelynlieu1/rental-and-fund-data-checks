"""Phase 6: Rockbank (VIC 3335) through its council, the City of Melton.

Victoria publishes active bonds only by council area (Rental Report, Table 15), so Rockbank's
own rental growth can't be measured. This uses Melton's growth as a floor and shows what it
would mean for a vacancy rate that still divides by the 2021 Census count.

Run:  python src/6_rockbank.py
"""
import importlib
from pathlib import Path

import pandas as pd

load = importlib.import_module("2_load")
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


# Active bonds by council, June each year (Table 15)
t15 = pd.read_excel(RAW / "vic_rental_report" / "tables_rental_report_2026-q2.xlsx", sheet_name="Table 15", header=None)
header = t15.iloc[2]
t15 = t15.iloc[3:]
t15.columns = ["lga"] + list(header[1:])
melton = t15[t15["lga"] == "Melton"].iloc[0]
vic = t15[t15["lga"] == "Total"].iloc[0]
growth = melton["Jun 2026"] / melton["Jun 2021"] - 1
vic_growth = vic["Jun 2026"] / vic["Jun 2021"] - 1
print(f"City of Melton active bonds: {melton['Jun 2021']:,} (Jun 2021) -> {melton['Jun 2026']:,} (Jun 2026), {growth:+.1%}")
print(f"All Victoria: {vic_growth:+.1%}")

# Rockbank's 2021 Census renters
census = load.load_census_renters()
rock = census[census["postcode"] == "3335"].iloc[0]
print(f"Rockbank 3335, Census 2021: {rock['private']:,} private renting households, {rock['all_renters']:,} all renters")

# What a 2021-based denominator would do to a vacancy rate there, under two growth assumptions
for label, g in [("Melton's growth (a floor)", growth), ("rentals doubled", 1.0)]:
    stock_now = rock["private"] * (1 + g)
    print(f"  If Rockbank's rentals grew like {label}: about {stock_now:,.0f} now; "
          f"a rate on the 2021 count should be multiplied by about {1 / (1 + g):.2f}")
