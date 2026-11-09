# Rental stock since the 2021 Census

*November 2026. Independent work using public data only. It is not affiliated with any research house and uses no private data.*

## The problem

A vacancy rate is the number of vacant rentals divided by the total number of rentals. The total usually starts from a Census count, and the most recent Census results are from August 2021 (the 2026 results are due in June 2027). In suburbs where many homes have been built since then, a total fixed at 2021 is too low, so the vacancy rate looks higher than it really is.

This project estimates how much the number of rented homes has grown since the 2021 Census in every NSW and Queensland postcode, using the number of rental bonds held as the measure of growth. It then lists the postcodes where a vacancy rate based on 2021 figures is most likely to be out of date. It cannot say whether any published vacancy rate is wrong, because it does not know how any particular rate is calculated.

## Main findings

1. Rental bonds follow Census renter numbers closely. In most postcodes there were between 1.1 and 1.25 bonds for every privately renting household in 2021, so growth in bonds is a reasonable guide to growth in rental stock.
2. Rental stock has grown fastest in the outer suburban growth areas, for example by 144% in Leppington (NSW) and 115% in Greater Flagstone (QLD) since 2021. In the 20 fastest-growing postcodes in each state, a vacancy rate based on the 2021 count would be between 1.2 and 2.4 times too high.
3. Not every postcode with fast growth has new homes. Student areas rank highly because international students returned after the borders reopened and because student accommodation lodges one bond per bed. These postcodes should not be adjusted.
4. Rockbank (VIC), a new estate on Melbourne's western fringe, is in the fastest-growing rental council area in Victoria. Active bonds in the City of Melton have risen by 53% since 2021, compared with 3% for Victoria as a whole.

## The 20 fastest-growing postcodes in each state

Growth is the increase in bonds held since 2021. The multiplier is the figure a vacancy rate based on the 2021 count should be multiplied by to reflect current stock. A postcode is marked as consistent if it stays in the top 20 under every variation of the method tested. The last column records whether new homes have actually been built there since 2021; each judgement has a source in `outputs/top20_sense_check.csv`.

| State | Postcode | Main suburbs | Private renters 2021 | Bonds, then and now | Growth | Multiplier | Consistent? | New homes built? |
|---|---|---|---|---|---|---|---|---|
| NSW | 2179 | Leppington, Austral | 1,182 | 1,323 to 3,231 | +144% | 0.41 | yes | yes |
| NSW | 2335 | North Rothbury (Huntlee), Branxton | 630 | 654 to 1,230 | +88% | 0.53 | yes | yes |
| NSW | 2765 | Box Hill, Marsden Park | 2,964 | 3,551 to 5,834 | +64% | 0.61 | yes | yes |
| NSW | 2573 | Tahmoor | 544 | 620 to 985 | +59% | 0.63 | yes | yes |
| NSW | 2016 | Redfern | 2,526 | 3,662 to 5,735 | +57% | 0.64 | yes | partly |
| NSW | 2762 | Schofields, Tallawong | 2,137 | 2,521 to 3,763 | +49% | 0.67 | yes | yes |
| NSW | 2007 | Ultimo, Broadway | 1,724 | 2,425 to 3,500 | +44% | 0.69 | yes | no |
| NSW | 2265 | Cooranbong, Martinsville | 494 | 505 to 710 | +41% | 0.71 | no | yes |
| NSW | 2174 | Edmondson Park | 975 | 1,221 to 1,715 | +40% | 0.71 | yes | yes |
| NSW | 2321 | Gillieston Heights, Lochinvar | 1,701 | 1,823 to 2,558 | +40% | 0.71 | yes | yes |
| NSW | 2572 | Thirlmere, Lakesland (Wollondilly) | 366 | 438 to 584 | +33% | 0.75 | no | yes |
| NSW | 2141 | Lidcombe, Berala | 4,006 | 4,330 to 5,734 | +32% | 0.76 | yes | partly |
| NSW | 2557 | Gregory Hills, Gledswood Hills | 1,569 | 1,646 to 2,170 | +32% | 0.76 | yes | yes |
| NSW | 2571 | Picton, Wilton | 553 | 668 to 877 | +31% | 0.76 | yes | yes |
| NSW | 2322 | Thornton, Chisholm | 1,864 | 2,088 to 2,631 | +26% | 0.79 | yes | yes |
| NSW | 2036 | Eastgardens, Hillsdale | 3,675 | 4,443 to 5,499 | +24% | 0.81 | yes | partly |
| NSW | 2325 | Cessnock, Bellbird | 2,575 | 2,957 to 3,657 | +24% | 0.81 | yes | partly |
| NSW | 2154 | Castle Hill | 2,800 | 2,987 to 3,693 | +24% | 0.81 | yes | yes |
| NSW | 2032 | Kingsford, Daceyville | 2,408 | 3,292 to 4,067 | +24% | 0.81 | yes | partly |
| NSW | 2570 | Camden, Oran Park | 4,366 | 4,734 to 5,835 | +23% | 0.81 | yes | yes |
| QLD | 4280 | Jimboomba, Flagstone | 1,022 | 1,122 to 2,413 | +115% | 0.47 | yes | yes |
| QLD | 4553 | Palmview, Mooloolah Valley | 603 | 640 to 1,305 | +104% | 0.49 | yes | yes |
| QLD | 4125 | Park Ridge, Park Ridge South | 1,550 | 1,792 to 3,468 | +94% | 0.52 | yes | yes |
| QLD | 4306 | Ripley, South Ripley | 2,973 | 3,368 to 6,204 | +84% | 0.54 | yes | yes |
| QLD | 4124 | Greenbank, Silverbark Ridge | 1,399 | 1,508 to 2,769 | +84% | 0.55 | yes | yes |
| QLD | 4133 | Logan Reserve, Chambers Flat | 2,516 | 3,233 to 5,537 | +71% | 0.58 | yes | yes |
| QLD | 4110 | Acacia Ridge, Heathwood | 1,481 | 1,795 to 2,733 | +52% | 0.66 | yes | yes |
| QLD | 4659 | Burrum Heads, Howard | 301 | 329 to 491 | +49% | 0.67 | no | unclear |
| QLD | 4505 | Burpengary, Burpengary East | 2,136 | 2,418 to 3,522 | +46% | 0.69 | yes | yes |
| QLD | 4506 | Morayfield, Moorina | 3,479 | 4,022 to 5,556 | +38% | 0.72 | yes | partly |
| QLD | 4076 | Darra, Wacol | 601 | 725 to 932 | +29% | 0.78 | yes | unclear |
| QLD | 4123 | Rochedale, Rochedale South | 1,507 | 1,585 to 1,996 | +26% | 0.79 | yes | yes |
| QLD | 4066 | Toowong, Auchenflower | 3,984 | 4,973 to 6,243 | +26% | 0.80 | yes | partly |
| QLD | 4501 | Lawnton | 716 | 841 to 1,050 | +25% | 0.80 | yes | partly |
| QLD | 4102 | Woolloongabba, Buranda | 2,548 | 4,175 to 5,138 | +23% | 0.81 | yes | partly |
| QLD | 4551 | Caloundra, Caloundra West | 6,591 | 7,391 to 8,890 | +20% | 0.83 | yes | yes |
| QLD | 4129 | Loganholme | 609 | 659 to 786 | +19% | 0.84 | no | partly |
| QLD | 4212 | Helensvale, Hope Island | 2,555 | 2,971 to 3,530 | +19% | 0.84 | yes | yes |
| QLD | 4036 | Bald Hills | 563 | 615 to 728 | +18% | 0.84 | yes | partly |
| QLD | 4504 | Narangba | 1,458 | 1,622 to 1,900 | +17% | 0.85 | no | yes |

## Why NSW and Queensland

The method needs a count of rented homes by postcode, both in 2021 and today. Only NSW (bonds held by postcode each December) and Queensland (bonds held by postcode each quarter) publish one. Together they account for about half of Australia's renting households. Victoria publishes active bonds only by council area (about 80 areas), so a Victorian postcode such as Rockbank can only be examined through its council, the City of Melton. Bond data for the other states was not collected. South Australia publishes a Private Rent Report, which has not yet been checked for counts of rental stock.

## What is left out, and why

- **Canberra.** ACT bonds are held by the ACT, not by NSW, so the 25 Canberra postal areas (51,655 renting households) are excluded. The 47 NSW bonds with ACT postcodes are listed in `outputs/unmatched_2021_nsw.csv`, which the scripts create.
- **Dates.** The 2021 Census was held on 10 August 2021, during the Sydney lockdown. NSW publishes bonds held only at December, so the NSW comparison uses December 2021, four months later. Queensland publishes quarterly, so the Queensland comparison uses 30 June 2021, which is 41 days before Census night and closer than 30 September 2021 (51 days after).
- **Queensland postcodes that are not published.** The Residential Tenancies Authority's postcode table covers 319 postcodes and totals 612,606 bonds at June 2021, while the statewide figure is 631,545. Whole regions are missing, including the Lockyer Valley, South Burnett, North Burnett, the North West (Mount Isa), the Cassowary Coast, Cape York and much of the South West. Size does not explain the gaps, because postcodes holding a single bond are included, and the Authority gives no reason, so it appears to be a decision about coverage. These 117 postal areas (27,983 renting households, or 4.5% of Queensland's total) are left out of both sides of the Queensland comparison.

## Do bonds and the Census agree in 2021?

The ratio below is the number of bonds held divided by the number of renting households in the Census. The full results are created by the scripts as `outputs/ratios_2021_nsw.csv` and `outputs/ratios_2021_qld.csv`.

| | Postcodes matched | Ratio to private renters | Ratio to all renters |
|---|---|---|---|
| NSW (December 2021) | 607 | 1.18 | 0.99 |
| QLD (June 2021) | 316 | 1.22 | 1.04 |

Among postcodes with at least 300 renting households, the middle half of ratios falls between 1.08 and 1.22 in NSW and between 1.11 and 1.25 in Queensland, measured against private renters. In most places, therefore, bonds follow the number of renters closely.

There are two main reasons the counts differ. Bonds overstate private renters by about 20%, because one home can carry several bonds (share houses, students renting by the room and mine workers) and because student accommodation lodges one bond per bed while the Census counts those beds as non-private dwellings. Bonds understate the total number of renters wherever there is a lot of public housing, because public tenants in NSW usually do not lodge a bond (Homes NSW asks for one only after damage of $500 or more, or from some returning tenants).

The ratio is furthest from 1 in four kinds of place: mining towns (Cobar 3.1; Dysart, Moranbah and Middlemount about 3), student areas (Chippendale, Kelvin Grove and the Brisbane CBD about 1.6), older public housing estates (Windale 0.29 and Claymore 0.38 against all renters) and areas with Defence housing (Ermington and Ferny Grove). Every postcode among the 10 highest and 10 lowest ratios is explained, with a source, in `outputs/ratio_extremes_explained.csv`. Two remain unexplained: Moree (2400, ratio 1.71) and Berrinba (4117, ratio 0.74).

Some postcodes do not match between the two sources. Notes on each are in `unmatched_notes.csv`.

- **NSW (47 postcodes).** There are 18 ACT postcodes (47 bonds), 15 post office box or mail centre postcodes (2001 and 2002 are the Sydney GPO and World Square boxes), 7 numbers that are not current postcodes (25 bonds, probably typing errors; 2301 holds between 11 and 20 bonds every year, for reasons unknown) and 6 very small areas with no bond record, such as an army training area, the ski resorts, a university campus and small rural localities. None of these affects the ratio.
- **Queensland (119 postcodes).** 117 are the unpublished areas described above, and 2 are post office box postcodes (4219 and 4271).

## Where has rental stock grown most since 2021?

The summary tables are in `outputs/top20.csv` and `outputs/top20_sense_check.csv`; the full table, `outputs/drift_all.csv`, is created by the scripts.

**Method.** Growth is calculated as bonds held now divided by bonds held in 2021, minus one. The NSW period runs from December 2021 to December 2025 (four years) and the Queensland period from June 2021 to September 2026 (five and a quarter years). Only postcodes with at least 300 privately renting households in 2021 are ranked, which leaves 368 in NSW and 206 in Queensland. A postcode is treated as consistent if it stays in the top 20 when the size limit is applied to all renters, when the limit is raised to 500, and, for Queensland, when September 2021 is used as the starting point. 18 of the 20 NSW postcodes and 17 of the 20 Queensland postcodes pass. Growth does not depend on which definition of renters is used, because the Census count cancels out.

**Checking against new building.** Each of the top postcodes was checked against evidence of new building since 2021, using ABS population growth, named housing estates and completed apartment buildings, and a second, sceptical review checked every claim.

| | New homes | Partly | No, or unclear |
|---|---|---|---|
| NSW top 20 | 14 | 5 | 1 |
| QLD top 20 | 12 | 6 | 2 |

Greenfield growth areas account for most of the genuine growth. In NSW these include Leppington and Austral (2179, up 144%), Box Hill (2765), Schofields (2762), Gregory Hills (2557), Oran Park and Camden (2570), Huntlee (2335) and the Wilton and Tahmoor area. In Queensland they include Greater Flagstone (4280, up 115%), Palmview and Harmony (4553), Park Ridge (4125), Ripley (4306), Greenbank (4124), Logan Reserve (4133) and Aura in Caloundra (4551). New apartments explain the growth in Edmondson Park (Ed.Square), Castle Hill (around the Showground) and Hope Island.

Student areas are the main exception. Redfern (2016), Ultimo (2007), Kingsford (2032), Toowong (4066) and Woolloongabba (4102) rank highly because international students returned after the borders reopened and because student accommodation lodges one bond per bed. Their growth overstates the growth in ordinary rental homes, and a vacancy rate there should not be adjusted using this method. In Darra (4076) and Burrum Heads (4659) there is no new building that would explain the growth. It may reflect owner-occupied homes being rented out, or a data issue, and these postcodes should be treated with care.

**What this means for a vacancy rate.** In the consistent growth-area postcodes, rental stock is now between 1.2 and 2.4 times the 2021 Census count. A vacancy rate that still divides by the 2021 count would therefore be about 1.2 to 2.4 times too high in those postcodes. The multiplier in `top20.csv` (0.41 to 0.81) is the figure to multiply such a rate by to obtain the rate on today's stock. In Leppington, for example, a rate of 2.0% would be about 0.8%.

## Notes written by an AI model, with a check on every number

`src/5_notes.py` sends one postcode's row from `top20.csv` to an AI model (Claude Haiku 4.5 on Amazon Bedrock, using the Australian region so the data stays in Australia) and asks for a note of three to five sentences. Code then extracts every number in the note and compares it with the row, at the precision it is written. Any note that contains a number not in the row is rejected. Each prompt, the model's name, its reply and the result of the check are saved in `outputs/notes/`.

**First run: all three notes were rejected.** The model treated bond counts as dollar amounts (for example "$3.4m") and invented figures per home (for example "$1.1k per unit"). The check caught every one of them, and the rejected notes are kept in `outputs/notes/run1_rejected/`. Two rules were added after this run, one rejecting any dollar sign (the data contains no money) and one rejecting growth expressed as a multiple (for example "1.4x"), and the instructions now state that bonds are counts.

**Second run: all three notes passed,** and a deliberately altered copy (with the bond count changed to 3,731) was rejected.

The three notes that passed are reproduced below exactly as the model wrote them.

**Leppington and Austral (NSW 2179):**

> Rental bonds in this postcode increased from 1,323 to 3,231 between December 2021 and December 2025—a 144% rise. The Census recorded 1,182 private rental households in 2021, but adjusted for bond growth, the current rental stock is estimated at 2,887 dwellings. Bond lodgements have grown substantially faster than the baseline Census count, suggesting either significant population inflow to the rental market, a shift from unregistered to registered tenancies, or improved compliance. An analyst should verify whether this postcode experienced new housing supply, migration patterns, or changes in reporting behaviour. The multiplier of 0.41 indicates that vacancy rates calculated on 2021 Census data should be scaled down when applying them to current stock estimates.

**Box Hill and Marsden Park (NSW 2765):**

> Postcode 2765 (NSW) shows strong rental bond growth of 64.3% since December 2021, with bonds rising from 3,551 to 5,834 tenancies. The private rental stock is estimated to have grown to 4,870 dwellings based on this bond drift. The multiplier of 0.609 indicates that 2021 Census vacancy rates need adjustment downward by this factor to reflect current conditions. An analyst should verify whether this bond growth reflects genuine stock expansion or tenant turnover, and cross-check the estimate against recent ABS or local authority data on housing supply.

**Ripley (QLD 4306):**

> Postcode 4306 (QLD) shows strong rental growth: bonds held grew 84% from 3,368 in June 2021 to 6,204 by September 2026. The private rental stock is estimated at 5,476 dwellings, up from 2,973 households recorded in the 2021 Census. Bond growth has outpaced census-based stock growth, suggesting either undercount in the Census, rapid new supply, or a shift in tenancy patterns. An analyst should verify whether bond data captures all rental arrangements and cross-check the stock estimate against recent development approvals and completions in the area.

**What the check cannot catch.** The check proves that every number comes from the data, but not that the reasoning is sound. Two of the notes compare bond growth with the estimated stock ("grown substantially faster than the baseline Census count" and "outpaced census-based stock growth"). Because the stock estimate is itself the 2021 count increased by bond growth, those sentences are circular. Each note therefore still needs to be read by a person. The check removes invented numbers, which is the more serious error, but not weak reasoning. A possible next step would be a short list of statements the notes may not make, or a second review of the reasoning by another model.

## Rockbank, through the City of Melton

Victoria publishes active bonds only by council (Rental Report, June quarter 2026, Table 15), so Rockbank (3335) cannot be measured on its own. The calculation is in `src/6_rockbank.py`.

- Active bonds in the City of Melton rose from 16,365 in June 2021 to 25,045 in June 2026, an increase of 53%. This is the fastest growth among the 56 Victorian councils with at least 1,000 bonds; Victoria overall grew by 2.9%.
- In the 2021 Census, Rockbank had 480 privately renting households (563 renters in total), which is a small base.
- Rockbank grew faster than Melton as a whole. The ABS recorded dwelling growth of 41.5% in the Rockbank and Mount Cottrell area in 2021-22 alone (2,138 net new dwellings), one of the highest rates in Australia ([ABS, Dwelling stock growth areas](https://www.abs.gov.au/articles/dwelling-stock-growth-areas)).

If a vacancy rate for Rockbank still divides by a 2021 count, it could be adjusted as follows:

| Assumption for Rockbank's rental growth since 2021 | Estimated rentals now | Multiply a 2021-based rate by |
|---|---|---|
| Same as Melton (+53%), probably too low | about 735 | about 0.65 |
| Doubled (+100%) | about 960 | about 0.5 |

Even after this adjustment, a high rate would be expected for a new estate, where many new homes reach the rental market at once and take time to lease. The reasonable conclusion is that a 2021-based vacancy rate for Rockbank is probably overstated because of its denominator, and is probably still high, although the evidence is at council level only.

## Limitations

- Bonds are not an exact count of rented homes. Share houses and student rooms carry several bonds, most public housing carries none, and bonds are optional in Queensland. The method uses growth in bonds, which cancels out any steady over- or under-count, but not one that changed after 2021, such as the opening of new student accommodation.
- Postal areas are not the same as postcodes. The ABS approximates postcodes, and post office box postcodes, mistyped postcodes and the Queensland areas the Authority does not publish are listed rather than silently dropped.
- The dates differ between states. NSW bonds run from December 2021 to December 2025, Queensland bonds from June 2021 to September 2026, and Victorian bonds from June 2021 to June 2026, by council only.
- The project cannot see how any published vacancy rate is calculated. It shows where a denominator fixed at 2021 would be out of date, and by roughly how much. It is intended as a check that can help explain a published figure, not as evidence that any figure is wrong.

## Sources

ABS Census 2021 DataPacks (table G37), CC BY 4.0. NSW Fair Trading rental bond data (bonds held by postcode). Residential Tenancies Authority (QLD) bond statistics, CC BY 4.0. Homes Victoria Rental Report, June quarter 2026. ABS, *Dwelling stock growth areas*. Download links, dates and checksums are in `data/MANIFEST.csv`.
