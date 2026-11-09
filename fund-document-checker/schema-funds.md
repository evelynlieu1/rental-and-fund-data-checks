# Field schema for MXT, MA1 and REV

LF1's schema (`schema.md`) is built around LF1's own two underlying funds, so it can't be reused as it is. This file is the shared version for the other three listed private credit trusts, drafted 8 Nov 2026 from a page-by-page read of every document by one reader per fund (text, plus page images where text extraction was unclear). The model gets the same field list without any numbers (`src/fund_fields.py`).

All pages are **pdf_page**. Values below are what the readers found, so the AI's flags can be checked against them; they are not an answer key and nothing is scored against them.

## Every one of them is a feeder

Like LF1, none of the three trusts lends directly. The 2026 reports mostly show look-through figures for the funds underneath, so every field records a **vehicle**.

| Trust | RE | Manager | What the trust actually holds |
|---|---|---|---|
| **MXT** Metrics Master Income Trust (the 2020 PDS calls it MCP Master Income Trust; same ARSN) | The Trust Company (RE Services) Limited, AFSL 235150 | Metrics Credit Partners Pty Ltd, AFSL 416146 | Units in the **MCP Wholesale Investments Trust** (Sub-Trust, trustee The Trust Company Limited, not the RE), which holds units and convertible notes in **DASLF**, **SPDF II** and **REDF**; plus a Manager Loan receivable and cash. The 2026 documents never mention the Sub-Trust. |
| **MA1** MA Credit Income Trust | Equity Trustees Limited, AFSL 240975 | MA Investment Management Pty Ltd, an **authorised representative** (no AFSL) | 100% in **MA Credit Income Fund (Wholesale)** (the "Underlying Fund"; MA1 owns about 63% of it), which invests in MA Master Credit Trust, MA Secured Loan Series A and B, MA Specialty Credit Income Fund and others. |
| **REV** Revolution Private Credit Income Trust | Equity Trustees Limited, AFSL 240975 | Revolution Asset Management Pty Ltd, AFSL 507353 | About 99.6% in **Revolution Private Debt Fund II** (RPDF II, unregistered; trustee Channel Investment Management). RPDF II in turn owns over 5% of REV, bought on market. |

## The fields

19 fields. 1 to 16 apply to any listed credit trust; 17 to 19 (strategy mix, strategy ranges, offshore share) were added because two of the three funds publish limits and actuals for them.

| # | Field | MXT | MA1 | REV | Traps across all three |
|---|---|---|---|---|---|
| 1 | `re_identity` (legal_name, afsl, acn) | pds 1, 2, 4, 5, 14, 110; tmd 1; monthlies p1, p2; portfolio 1, 22 | pds 1, 3, 20, 118; spds 1, 2; update 11, 14; ar 1, 6, 7, 14, 22, 40 | pds 1, 2, 12, 25, 28, 119; factsheet 3, 5; report 1, 10; rg240 1, 2 | Sub-trustees, custodians and RE-like names (MAAM RE Ltd, The Trust Company Limited, EQT Australia) are not the RE. "AFSL 240 975" = 240975. |
| 2 | `manager_identity` (legal_name, licence_number) | pds 1, 4, 5, 11, 118; monthlies; portfolio 1, 22 | pds 1, 3, 21, 28; spds 1; update 11, 14; ar 3, 7, 9, 22 | pds 1, 2, 8, 14, 28; factsheet 3, 5; report 1, 10; rg240 2 | MA1's manager is an authorised representative: its licensee differs between pds 21 and update 14. Channel Capital's AR number (REV) is Channel's. |
| 3 | `management_fee_pct_pa` | Trust charges none (pds 70, 97); RE fee about 0.02% (pds 68); IEE 0.28-0.29% (pds 26, 69) | Manager fee 0.90% on direct holdings only, nil on the UF (pds 21, 23, 75); RE fee rate never printed | Never split from the 0.95% total; RE maximum 0.50% of GAV (pds 63) | Fees of the underlying funds look like the trust's. Constitutional maximums are on gross assets. |
| 4 | `total_fees_and_costs_pct_pa` | pds 27 (three columns by raise size), 68, 69; portfolio 1 (FY2026 actual) | pds 72, 74 (1.21% of NAV); update 9 is a different concept (% of AUM) | pds 59, 61; factsheet 3; report 1 (0.95% of NAV) | Compare with the ASX MER. MXT's PDS table has one column per possible raise. |
| 5 | `performance_fee` | None at trust level; SPDF II and REDF charge one (pds 70); estimate 0.09% (pds 26, 27, 68), actual 0.11% FY2026 (portfolio 1) | None at trust level (pds 77); interposed funds 0.45% estimate (pds 73, 74, 77); 0.22% actual (update 9) | None (pds 9, 18, 59, 61, 62; factsheet 4) | The ASX "outperformance fee" column is about the trust only. |
| 6 | `target_return` | RBA + 3.25% net of fees (pds 11, 17, 19, 51; tmd 3; monthlies; portfolio 1, 2) | RBA + 4.25% (pds 10, 12, 36; ar 1, 7; update 1) | RBA + 4% (pds 8, 18, 29, 33; factsheet 1, 3; report 1, 4; rg240 1) | Underlying funds' hurdles and targets (BBSW + bps; MA's UF + 4.75%, SLS A + 4.25%) belong to them. The "net of" wording varies by page. |
| 7 | `underlying_allocation_pct` | Not stated in 2026; ranges only (pds 24) | Update 46 (image only), pds 12 (target weights) | rg240 1 (99.6% / 0.4%, 30 Jun 2026) | A target or a range is not an actual. MA1's share of the UF is not an allocation. |
| 8 | `loan_count` | 354 / 356 / 360 (monthlies, Jun to Aug 2026); portfolio 1, 2, 3 | ar 12 (237, 30 Jun 2026); update 1, 4 (246, 30 Sep 2026); pds 43 | report 4 ("58 loans") and report 9 (58 issuers, 123 tranches) | Underlying-fund counts sit on later pages of MXT's portfolio report. |
| 9 | `weighted_avg_lvr_pct` | Portfolio 5 (CRE loans only, simple average) | By segment only (update 5, 8, 45; pds 44) | Not stated | No whole-portfolio LVR for any of them. |
| 10 | `largest_exposure_pct` (actual, limit) | Limit 5% at investment (pds 16, 52); actual portfolio 1, 3 | Update 1, 4; limits pds 46, 48, 50 by vehicle | Limit 7.5% of RPDF II committed capital (pds 31, 35); actual not stated | Limits are per vehicle and "at investment". |
| 11 | `arrears_or_impairment_pct` | Portfolio 2, 5 (watchlist definitions differ between the two pages) | Update 3, 5, 8, 9; ar not stated | Report 9 (watchlist and arrears 0.7%) | Receivables-level arrears (MA1) measure collateral, not positions. |
| 12 | `leverage` (actual, limit) | None at trust (pds 25, 61); caps per underlying fund | Caps per fund (pds 19, 20, 46, 51); actual update 3 | REV 0% (rg240 1, 2); RPDF II cap 25% (pds 26, 29, 36), actual rg240 2 | Borrower net debt/EBITDA ("3.2x") is not fund leverage. |
| 13 | `nta_per_unit` | Monthlies p1 ($2.00 NAV); pds 84 | ar 4; update 1, 5 | rg240 1; report 1; pds 46 | Compared with the ASX NTA price at 31 Aug 2026 where a document gives that date. |
| 14 | `monthly_distribution_cpu` | Monthlies p2 | ar 2, 8, 37 | report 1 (columns extract out of order) | Annual totals and yields are not this. |
| 15 | `fund_size_aud` (net_assets, fum) | Monthlies p1; portfolio 3; pds 52, 82, 91 | ar 4, 12, 18, 19 ($'000); update 1 | rg240 1; report 1 | Group-wide AUM (Metrics, MA Financial, Revolution) is not the trust's. |
| 16 | `liquidity_or_buyback` | No buy-back obligation (pds 62, 74, 106) | pds 13, 57, 58, 114; ar 3, 9; update 5 | pds 20, 26, 83, 102, 103; factsheet 3; report 5 | The underlying funds' redemption caps are separate. |
| 17 | `strategy_mix_pct` | Not stated in 2026 | Update 2, 4 | rg240 1; report 2, 9 | Codes are fixed per fund in `src/fund_fields.py`. |
| 18 | `strategy_limits` | pds 24 (DASLF / SPDF II / REDF ranges) | pds 18, 36 | pds 30, 35 | A single target weight is not a range. |
| 19 | `offshore_pct` (actual, limit) | Australian borrowers over 80% (pds 16, 52); actual portfolio 3 | Cap pds 18, 41, 50; actual update 2, 4 | NZ share in report 9 | State the basis: outside Australia, or outside Australia and NZ. |

## Leads to confirm in phase 6

Found by the readers while mapping. Each is checked against the pages before it's called anything; until then it's a lead, not a finding.

**MA1**
1. Buy-back: "up to 5%" a quarter (pds 57) against "up to 2.5%" a quarter, only at a discount (update 5). No supplementary PDS covers the change.
2. Strategy ranges: direct asset lending 30-50% and asset-backed 40-60% (pds 18) against 19% and 66% (update 2, 4).
3. Global cap 10% of NAV (pds 18) against about 17% outside Australia and NZ (update 2, 4).
4. The manager's licensee: MA Asset Management Ltd (pds 21) against MAAM RE Ltd (update 14).
5. The custodian: Equity Trustees Limited (ar 7) against EQT Australia Pty Ltd (pds 20, update 11).
6. June 2025 monthly return: 0.67% (ar 8) against 0.74 (update 10). ar 8's own FY25 total needs 0.74.

**MXT**
1. Manager Loan maximum: "up to $44.5 million" (pds 29, 103) against 44,875 ($'000) (pds 84).
2. The IEE: 0.29% (pds 26) against "currently... 0.28%" (pds 69).
3. Performance fee: FY2026 actual 0.11% (portfolio 1) above the PDS's "nil to 0.09%" (pds 70). Different periods.
4. The RE's ABN printed one digit short on monthly_06 p1.
5. The portfolio report points investors to a PDS whose offer was withdrawn in March 2020.

**REV**
1. Related parties: the PDS calls the investment in RPDF II a related-party arrangement (pds 107, 108); the report says there are no related-party transactions (report 4).
2. RPDF II's net leverage (8.2%) above its gross (7.6%) (rg240 2).
3. The report's "58 loans" (report 4) are "58 issuers" with 123 tranches on report 9.
4. Derivatives: the PDS promises an annual list of derivative counterparties for the trust and RPDF II (pds 23); the RG 240 update reports none, at trust level only (rg240 1).
