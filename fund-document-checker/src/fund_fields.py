"""The field list for MXT, MA1 and REV, as sent to the model: schema-funds.md WITHOUT its numbers.

GENERIC_FIELDS is the same for the three funds. BACKGROUND tells the model how each fund is structured
(which vehicle is which, defined terms), never what the values are.
"""

GENERIC_FIELDS = """
Fields (name: unit, sub_fields, what to capture, traps). Every row also needs a "vehicle": "trust" (the listed
trust itself) or the short name of the underlying fund or portfolio it describes. A figure for an underlying
fund is NOT a figure for the trust.
1. re_identity: the responsible entity (RE). sub_fields legal_name, afsl, acn. AFSL and ACN as digits only.
   The RE and the investment manager are different companies.
2. manager_identity: the investment manager. sub_fields legal_name, licence_number (digits only; in notes say
   whether it is an AFSL, or an authorised representative number such as CAR or AFSRN).
3. management_fee_pct_pa: the trust's own management fee, % p.a. sub_fields management_fee, re_fee (only if the
   RE's fee is stated separately). Not the total fees and costs. Record the basis as printed (NAV, NTA, GAV).
4. total_fees_and_costs_pct_pa: the trust's total management fees and costs (or MER/ICR), % p.a. sub_field total.
   Record the basis and, in notes, the period it covers.
5. performance_fee: sub_fields charged_by_trust (yes / no, from an explicit statement only), rate_pct (the
   performance fee rate), estimated_pct_pa (an estimated performance fee as % p.a.). Say in vehicle who charges it.
6. target_return: sub_field margin_pct (the margin over the benchmark, e.g. RBA cash rate + x% gives x);
   basis = the benchmark and what it is net of, as printed. A distribution yield actually paid is not a target.
7. underlying_allocation_pct: actual % of the trust in each underlying fund, sleeve or portfolio, with date.
   sub_field = short name of that fund or sleeve. A target or limit is not an actual.
8. loan_count: sub_fields loans (number of loans / investments / positions), borrowers (number of borrowers),
   with date and vehicle.
9. weighted_avg_lvr_pct: weighted average loan-to-value ratio, %, with date and vehicle. No sub_field.
10. largest_exposure_pct: sub_fields actual (largest single borrower or loan as % of the portfolio, with date)
   and limit (the stated maximum for a single borrower or loan). Say in notes borrower or loan.
11. arrears_or_impairment_pct: % of the portfolio in arrears, impaired, non-performing or non-accrual, with date.
   sub_field = the measure as printed in short (e.g. arrears_90d, impaired, non_performing).
12. leverage: sub_fields actual and limit (borrowing as % or multiple, as printed), with vehicle.
13. nta_per_unit: net tangible assets (or NAV) per unit in $, with date. No sub_field. Basis in basis (NTA/NAV,
   pre- or post-tax).
14. monthly_distribution_cpu: distribution in cents per unit for one month, with that month's last day as as_at.
   No sub_field. An annual total or a yield is not this.
15. fund_size_aud: sub_fields net_assets (or NAV), fum (funds under management), in whole AUD, with date and vehicle.
   Convert $m, $bn and $'000.
16. liquidity_or_buyback: sub_fields offer_pct (buy-back or redemption offer per period), cap_pct (any cap),
   price_basis (text). Put the period and wording ("intends", "up to") in notes.
17. strategy_mix_pct: actual % of the portfolio in each strategy or asset class, with date and vehicle.
   sub_field = the strategy code listed in the background below.
18. strategy_limits: the permitted range for each strategy or asset class, value_norm "min-max" (e.g. "10-40").
   sub_field = the same strategy code. A target weight is not a range: put a single target in notes instead.
19. offshore_pct: sub_fields actual (% of the portfolio outside Australia and New Zealand, or outside Australia,
   as printed; say which in basis) and limit (the stated cap).
"""

# Sub-fields that don't exist for these fields (4_score.py ignores the sub_field when matching them)
NO_SUB_FIELD_GENERIC = {"weighted_avg_lvr_pct", "nta_per_unit", "monthly_distribution_cpu"}

BACKGROUND = {
    "MXT": """
Background: MXT (Metrics Master Income Trust, ASX:MXT; called "MCP Master Income Trust" in the 2020 PDS) is a
listed trust. RE: The Trust Company (RE Services) Limited (part of Perpetual). Manager: Metrics Credit Partners
Pty Ltd. MXT holds units in an unlisted sub-trust, MCP Wholesale Investments Trust (vehicle "Sub-Trust"; its
trustee, The Trust Company Limited, is NOT the RE), which invests in three Metrics funds: the Metrics Credit
Partners Diversified Australian Senior Loan Fund (vehicle "DASLF"), the Metrics Credit Partners Secured Private
Debt Fund II ("SPDF II") and the Metrics Credit Partners Real Estate Debt Fund ("REDF"). In the 2026 monthly
and portfolio reports, MXT figures are look-through figures: use vehicle "trust" for them. In the portfolio
report, pages about DASLF, SPDF II or REDF describe that fund, not MXT. "Fund" can mean any of these; decide from
context. The PDS is from January 2020: its figures are estimates at that date. Traps: Metrics' group-wide funds
under management is not MXT's size. The custodian (Perpetual Corporate Trust) is not the RE. Tables that show
one column per possible capital raise: record the column's heading in notes. A borrower leverage ratio
(net debt / EBITDA, "x") is not fund leverage. "Manager Share of Transaction Benefits" is not a fee.
underlying_allocation_pct sub_fields: daslf, spdf2, redf, cash.
Strategy codes (fields 17, 18): daslf, spdf2, redf (the three underlying funds, as allocation ranges).
""",
    "MA1": """
Background: MA1 (MA Credit Income Trust, ASX:MA1) is a listed trust. RE: Equity Trustees Limited. Investment
manager: MA Investment Management Pty Ltd, an authorised representative (it has no AFSL of its own).
MA1 holds units in ONE wholesale fund, MA Credit Income Fund (Wholesale), which the documents call the
"Underlying Fund" (vehicle "UF"). The UF invests in other MA Financial credit funds, e.g. MA Master Credit Trust
(vehicle "MCT"), MA Secured Loan Series Class A and Class B ("SLS A", "SLS B"), MA Specialty Credit Income Fund
("SCIF"). Portfolio figures in the investor update are look-through figures for the UF: use vehicle "UF".
Use vehicle "trust" for MA1 itself. Traps: MAAM RE Ltd and MA Asset Management Ltd are not the RE; KPMG and the
custodian are service providers. MA1's share OF the UF is not an allocation. A target return, LVR limit or fee
printed for MCT, SLS or SCIF belongs to that vehicle, not to MA1. MA Financial's group-wide AUM is not MA1's size.
Figures in the annual report tables are often in $'000.
underlying_allocation_pct sub_fields: uf, mct, sls_a, sls_b, scif, other, cash.
Strategy codes (fields 17, 18): direct_asset_lending (real estate / DAL), asset_backed, direct_corporate_lending.
""",
    "REV": """
Background: REV (Revolution Private Credit Income Trust, ASX:REV) is a listed trust. RE: Equity Trustees Limited.
Manager: Revolution Asset Management Pty Ltd. REV invests almost all its assets in ONE unlisted fund,
Revolution Private Debt Fund II (vehicle "RPDF II"), which holds senior secured corporate loans and asset-backed
securities. Use vehicle "trust" for REV and "RPDF II" for the underlying fund. "Fund" means REV in some places
and RPDF II in others: decide from context. Traps: Revolution's funds under management across the whole firm
is not REV's size. Channel Capital's authorised representative number belongs to Channel, not the manager. The
custodian (EQT Australia) is not the RE. Some tables (monthly distributions, credit ratings) extract with their
columns out of order: take a value only if the quote shows its label next to it.
underlying_allocation_pct sub_fields: rpdf2, cash.
Strategy codes (fields 17, 18): corporate_loans, asset_backed, commercial_property, bonds, cash.
""",
}
