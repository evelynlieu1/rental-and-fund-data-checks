# Field schema for LF1 (phase 3)

What to extract from LF1's documents, how to record it, and which later check each field feeds. Drafted 8 Nov 2026 from a page-by-page review of all 7 documents and ASIC REP 814 (47 good practices listed), then checked by two independent reviewers: one opened every cited page, the other tested whether two people would label each field the same way. Their corrections are applied here.

## First, the structure

**LF1 invests in two funds, not one.** Every document says so:

| Holding | Short name | Share of LF1 | Who runs it |
|---|---|---|---|
| 12 Month Investment Account (called "12 Month Term Account" before 2026) of the La Trobe Australian Credit Fund | **12MIA** | 41.01% (31 Aug 2026) | La Trobe; Australian mortgages |
| La Trobe US Private Credit Fund, Class A | **USPC** | 58.79% (31 Aug 2026) | La Trobe; invests mainly in **LGAM Private Credit LLC**, advised by Morgan Stanley (MS Capital Partners Adviser) |
| Cash and net receivables | | 0.21% | |

So "level" has more than two values. Every field names its **vehicle**: LF1, 12MIA, the whole Credit Fund, USPC, LGAM LLC, or the RE/Manager. The Credit Fund annual report covers only the 12MIA side (about 41% of LF1). There are no statutory accounts for USPC or LGAM in the document set.

## The fields

18 fields in six groups. `value pages` hold the value; `distractor pages` look like they hold it but don't (a labeller must not use them). Pages are **pdf_page** (the page index in the file). Document names: `pds`, `tmd`, `faqs`, `profile` (monthly fund profile, 31 Aug 2026), `ar` (LF1 annual report FY2026), `uar` (La Trobe Australian Credit Fund annual report FY2026), `deck` (roadshow deck, Oct 2026), and `asx` (ASX Investment Products report, Sep 2026, a spreadsheet).

### A. Who runs it

| # | Field | Vehicle | Unit / sub-fields | Value pages | Comparison it feeds | Trap |
|---|---|---|---|---|---|---|
| 1 | `re_identity` | RE | sub-fields `legal_name`, `acn`, `afsl` (a name with no ACN/AFSL on the page is still a row; the missing parts are "not stated on page"); plus `also_re_of_underlying` yes/no | pds 2, 4, 9, 60, 120; tmd 1, 7; profile 3 (name only), 6; deck 16; ar 4, 8; uar 4, 13 | Same across documents; against the ASIC licensee register (outside the 7 documents) | "AFSL 222 213" = 222213. ar 8 also prints an **ACL** (credit licence) with the same digits: not the AFSL. The Manager (La Trobe Financial Services Pty Ltd) is a different company. Never take roles from the structure diagram text (pds 18, 40): extraction loses which box is LF1's. "Limited" = "Ltd". |
| 2 | `manager_payment` | Manager (fee flow out of LF1) | sub-fields `paid_directly_by_lf1` (yes / no / not stated), `paid_by` (RE out of its own fee / no fee payable by RE / not stated) | pds 27, 61; ar 8, 33 | **Same document disagrees with itself:** pds 27 says no separate fee is payable to the Manager by the RE; pds 61 says the RE pays the Manager a manager fee out of its own remuneration | ar uses "management fee" for the RE's 0.05% fee (ar 18, 22, 24, 27, 29): not a Manager fee. Distractors: profile 3 ("Management Fee" row = the 1.93% total), uar 38 (a different vehicle's service fee). |

### B. Fees

| # | Field | Vehicle | Unit / sub-fields | Value pages | Comparison it feeds | Trap |
|---|---|---|---|---|---|---|
| 3 | `lf1_re_fee_pct_pa` | LF1 | % p.a. of NAV; `value_type` per row (current rate / estimate / constitutional maximum) | pds 25, 80, 83 (maximum); ar 33 | PDS against annual report (0.05% in both); phase 5 can test the $145,344 fee (ar 33) against 0.05% of average NAV | Not 1.93% (total), 0.17% (recoverable) or 1.71% (indirect). The constitutional maximum is also 0.05%, so `value_type` matters. |
| 4 | `lf1_total_fees_and_costs_pct_pa` | LF1 | % p.a. of NAV or NTA **as printed**; sub-fields `re_fee`, `recoverable`, `indirect`, `total`; `assumed_weighting` (50:50 in the PDS); `covers_period` | pds 25, 80, 82; profile 3; asx (MER column); ar: **not stated** | **ASX report against PDS** (the MER check: 1.93% in the ASX report and the PDS). The annual report never restates the estimate against actuals. | It's a pre-launch **estimate** assuming 50:50; the actual mix is about 41:59. Distractor: profile 2 prints 1.93 as the 3-month distribution return. pds 83 (s10.3.1) defines fees and costs without the RE fee, contradicting pds 80: record as a source inconsistency. On pds 80 the table columns interleave: check 0.05 + 0.17 + 1.71 = 1.93. |
| 5 | `lgam_performance_fee_pct_of_lf1_nav` | LGAM LLC (borne by LF1) | % p.a. of LF1 NAV; sub-fields `with_waiver` (0.07), `without_waiver` (0.58), `assumed_uspc_weighting` (50%); fee terms as text only (12.5% of realised gains, hurdle) | pds 25, 81, 82, 85, 86; profile, deck, ar: **not stated** | **ASX report against PDS:** the ASX report's outperformance-fee column says "No" for LF1. That's consistent if read as "LF1 charges none itself" (pds 84 says LF1, the Credit Fund and USPC charge none), but the PDS shows LF1 bears one through LGAM. This is the level check. | An estimate from the year before LF1 existed. The fee example on pds 82 extracts as "$1,0101, 3". |
| 6 | `12mia_rebate_to_lf1_pct_pa` | 12MIA (income to LF1) | % p.a.; `basis` = "not stated" unless the page says it (faqs 3 and ar 31 do) | pds 43 (chart footnote), 84; faqs 3; ar 33 | Same across PDS, FAQs, annual report (0.50%); ar 33 adds "or such other amount as agreed", and ar 29 lets the RE rebate more to cover a distribution shortfall | It's income to LF1, not a cut to LF1's fee. On pds 84 it sits under a heading printed on pds 83, so a page-level reader may assign it to LF1. Synonyms: investor rebate income, management fee rebate (receivable), fee rebate received. |
| 7 | `12mia_management_costs_pct_pa` | 12MIA | % p.a. of the 12MIA's average investor balances, for a **period**; `value_type` estimate or actual ICR; `definition_basis` | pds 84 (FY2025 estimate 1.80%), pds 49 (the retention practice); uar 17 (FY2026 ICR 1.70%) | Estimate against actual across documents | 1.79% on uar 17 is the whole fund; other accounts range from 0.17% to 3.33%. The two figures are defined differently (retained share against an ICR on a cash basis). Never compare with 1.71% or 1.93% directly: different base. |
| 8 | `uspc_lgam_management_fees_pct_pa` | USPC and LGAM LLC | sub-fields `uspc_fee` (0.75% of Class A NAV), `uspc_constitutional_max`, `lgam_base_fee` (1.00%), `lgam_recoverable` (0.30%) | pds 84 only; other documents: not stated | Together with field 7, this lets phase 5 rebuild LF1's 1.71% indirect costs from both layers. Without it, 59% of LF1's fee stack has no field. | Single-document field: the comparison is the reconstruction, not a cross-document match. |

### C. Distributions

| # | Field | Vehicle | Unit / sub-fields | Value pages | Comparison it feeds | Trap |
|---|---|---|---|---|---|---|
| 9 | `lf1_target_distribution` | LF1 | sub-fields `margin_over_rba_pct` (3.25), `net_of_wording` (per occurrence), `rba_reference_date` | pds 13, 15, 20, 42, 45; tmd 1, 3; faqs 1, 4; profile 2, 3, 6; deck 3, 12, 14, 17; ar 10, 27, 29 | Same across all documents; wording differs **within** the profile (p2 "fees and costs", p6 "fees, costs and taxes"), so compare occurrences, not documents | Footnote digits fuse to the text ("Rate4 + 3.25%"). The 12MIA's "AusBond Bank Bill + 1.50%" benchmark belongs to the underlying fund. No document says what the target yield is measured against. |

### D. Allocation

| # | Field | Vehicle | Unit / sub-fields | Value pages | Comparison it feeds | Trap |
|---|---|---|---|---|---|---|
| 10 | `lf1_allocation_limits` | LF1 | min % and max % per holding (12MIA, USPC, cash); target weighting recorded separately | pds 17, 43, 46; faqs 1; profile 3; deck 3 (12MIA and USPC only; cash not stated) | Same across documents (12MIA 20-100%, USPC 0-80%, cash no limit); **limit against actual** with field 11 | Cash "no limit" = max unlimited, not 100. The 50:50 target is not a limit. Distractor: pds 11's "20%" is a free-float condition. |
| 11 | `lf1_allocation_actual_pct` | LF1 | % of LF1 net assets, one row per holding, with date | profile 2 (graphic), 3; ar 7 | Limit against actual; across dates (about 59% USPC at 30 Jun and 31 Aug 2026) | Profile slices sum to 100.01 (rounding). ar 7 says "approximately". Don't derive % from dollars in phase 4. |
| 12 | `lf1_investment_in_12mia_aud` | LF1 | whole AUD, with date | ar 24, 30; uar 40 | **Feeder against underlying:** $110,200k (ar 24) against $110,200,000 (uar 40), both 30 Jun 2026 | ar is in $'000, uar Notes 11-13 in whole dollars. 0.95% on ar 31 is LF1's share of the 12MIA, not of LF1. Not the Credit Fund's $48.6m loan to buy LF1 units (uar 40). |

### E. Credit risk

| # | Field | Vehicle | Unit / sub-fields | Value pages | Comparison it feeds | Trap |
|---|---|---|---|---|---|---|
| 13 | `12mia_weighted_avg_lvr_pct` | 12MIA | %, with date and `lvr_basis` (value at loan start / latest valuation) | pds 20, 21, 45, 46, 48; ar 7; uar 7, 35; profile 3, 4; deck 8 | Across documents and dates (64.7% Apr 2025 to 67.5% Jun 2026 to 67.4% Aug/Sep 2026); feeder against underlying at 30 Jun 2026; limit against actual with field 14 | 67.7% (uar 16) is the whole fund. The basis differs by document. USPC's 38.4% is a different field even where deck 12 labels both "LTV". |
| 14 | `12mia_max_lvr_pct` | 12MIA | % with the quote showing per-loan or portfolio | pds 48 (80%); uar 34: not stated (mentioned without a number) | Limit against the weighted average only | Distractor: uar 28's 80% is an impairment-review trigger, not a lending limit. The ≥75% LVR bucket can't test an 80% cap. |
| 15 | `12mia_loan_count` | 12MIA | count, with date | pds 48; ar 7, 8 (undated, "over 10,500"); uar 7; profile 3, 4; deck 8 | Across documents and dates (11,540 to 10,789 to 10,350 to 10,114); feeder against underlying at 30 Jun 2026 | 12,514 (uar 10, 16) is the whole fund. deck 12 shows the 12MIA count under an LF1 heading (scope mismatch: log it). "More than 11,000 credit assets" is LF1 look-through including US borrowers. |
| 16 | `uspc_weighted_avg_ltv_pct` | LGAM LLC (via USPC) | %, with date; basis "fair market value" as printed | pds 52; ar 7; profile 3, 5; deck 11 | **Same date, different value:** 38.4% (profile, footnoted to 30 Jun 2026) against 38.8% (ar 7, 30 Jun 2026) | Not comparable with the 12MIA's property LVR. pds 52 extracts as "39%11" (footnote fused). Profile footnote numbers carry dates (14 = 30 Jun 2026). |

### F. Liquidity

| # | Field | Vehicle | Unit / sub-fields | Value pages | Comparison it feeds | Trap |
|---|---|---|---|---|---|---|
| 17 | `lf1_buyback_policy` | LF1 | sub-fields `quarterly_offer_pct` (5, with qualifier "intends" / "up to"), `cap_12m_pct` (10), `approval_can_lift_cap` (yes/no/not stated), `price_basis` (NAV per unit plus forgone distributions, pds 54) | pds 14, 21, 23, 45, 53, 54, 56, 116; tmd 2; profile 3, 6; deck 3, 15, 17; ar 9, 25 | Same across documents; phase 5 can test the units bought back per quarter (ar 25) against 5% and the 10% cap | "5%" means three different things: LF1's buy-back, the USPC redemption cap and the LGAM repurchase limit. ar 9's on-market buy-back is a separate programme. |
| 18 | `underlying_redemption_cap_pct_per_quarter` | USPC and LGAM LLC (one row per vehicle) | % of outstanding units (USPC) or interests (LGAM) per quarter | pds 55, 57, 70; ar 26, 29 | Same across documents; **feeder against underlying liquidity:** LF1 offers 5% of its own units a quarter while 59% of its assets sit in a fund capped at 5% a quarter (LF1 holds 42.43% of USPC, ar 31) | The PDS states both levels (LGAM "expected" 5% of interests; USPC 5% of Class A units). Record the vehicle. |

## Left out, and why

- **Next to add if there's time:** NTA per unit and ASX price (the denominators for any "% of NTA" check and the discount to NTA); USPC leverage (1.26x at 31 Jul 2026 against the PDS target and cap); arrears and impairment (whole-fund 0.48%, uar 16; silence elsewhere is itself a disclosure-gap finding); LF1's monthly total return (see early findings).
- **Consistent and low value:** custodian, auditor, unit registry (Perpetual, EY, Automic everywhere).
- **Single document or not checkable:** distributions in cents (they reconcile already: 14.23c in both the profile and the annual report), valuation policy (qualitative), research ratings (logos are images), sector and state splits (map percentages have no labels in the text), the investor reserve (size never disclosed).

## Labelling rules for phase 4

1. **One row per value occurrence:** `field, sub_field, doc, pdf_page, printed_page, value_raw, value_norm, unit, basis, as_at, value_type, vehicle, quote, status, notes`. The same value on three pages is three rows.
2. **Cite pdf_page.** Work out printed_page from the offsets in `EXTRACTION-NOTES.md`; never use the parquet's `printed_page` column (wrong on about 15 pages).
3. **value_raw** is exactly as printed. **value_norm** removes spaces and separators ("$13, 030 million" becomes 13030000000) and fused footnote marks ("39%11" to 39, footnote 11 in notes). In the monthly profile, footnote numbers and symbols carry the as-at date.
4. **Units:** percent points (7.60, not 0.076); the basis as printed ("of NAV", "of NTA": never treat NAV and NTA as the same); money in whole AUD (convert $'000 and $m; USD marked); counts as integers; distributions in cents.
5. **as_at** is the date the value describes, from the header, footnote or sentence (a month-end label means the last day of the month). If the page gives none, leave it blank with "undated on page". Never copy the document date. Period values get period_start and period_end.
6. **value_type:** target, estimate, actual, actual for a period, policy limit, constitutional maximum, or marketing claim. PDS fee figures are estimates; annual report figures are actuals.
7. **Ranges:** min and max separately; "up to X" to max X; "no limit" to unlimited; "over X" to X with qualifier ">"; "about" to "~". Never take a midpoint.
8. **vehicle** must match the field. A value for a different vehicle (the whole fund's 67.7% LVR offered for a 12MIA field) is not recorded in that field; log it in notes as a scope mismatch.
9. **Defined terms differ by document.** "Fund" = LF1 in the PDS and LF1 annual report, USPC in the profile's Important Information (p6), the Credit Fund in the Credit Fund annual report. "Underlying Fund" = LGAM LLC in the LF1 annual report and profile, but the 12MIA and USPC together in the TMD. In the LF1 annual report "management fee(s)" = the RE's 0.05% fee.
10. **Silence is never "No" and never zero.** A field a document doesn't state gets one row: status "not stated", the pages searched in notes. "not applicable" only when it can't exist (an actual value in the pre-listing TMD). "image only" when it's visible only in a chart or logo.
11. **Problem pages** (list in `EXTRACTION-NOTES.md`): check the value against the page image before recording; set source_kind to text, table or chart_image.
12. **Record inconsistencies in the source as printed,** with source_inconsistency = true; never correct them.
13. **No derived values in phase 4** (implied rates, % from dollars, discount to NTA). Those are phase 5.
14. **Quotes under 15 words.** These are copyright documents; paraphrase everything else.

## Early findings to confirm in phase 6

Spotted while drafting; each is a question for the manager until checked against both pages.

1. **How the Manager is paid** (field 2): the PDS says on pdf 27 that no separate fee is payable by the RE, and on pdf 61 that the RE pays the Manager a manager fee. *Checked against the text: both statements are there.*
2. **USPC loan-to-value at 30 Jun 2026** (field 16): 38.4% in the monthly profile, 38.8% in the annual report. *Checked against the text.*
3. **Fee definition** (field 4): pds 83 describes management fees and costs without the RE fee; pds 80 includes it.
4. **Monthly total return, May 2026:** 0.14% in the deck against 0.65% in the profile (seen on the page images by a reviewer; not yet checked by me).
5. **PDS LVR buckets** (pds 48) add up to about 104.5% and their dollar amounts exceed the loan book: an error in the source itself.
6. **Chair:** pds 26 calls one director Executive Chairman, pds 62 names another Non-Executive Chairman.
