# Do a private credit fund's documents agree with each other?

*November 2026. Independent work using public documents only. It is not advice, and an inconsistency between two documents is a matter to raise with the manager rather than a finding that anything is wrong.*

## Summary

I built a process that reads the documents an ASX-listed private credit fund publishes, extracts the figures an analyst would check, and compares them. I developed it on La Trobe Private Credit Fund (LF1) and then ran it, unchanged, on three other trusts: MXT, MA1 and REV. Across the four funds it read 21 documents (786 pages), made 503 comparisons and raised 73 flags. After review, 6 of these are genuine inconsistencies worth raising with the manager. Most of the others were errors made by the process itself, which is why every flag is reviewed before it is used.

## The problem

A fund is rated largely on the documents it publishes: the product disclosure statement (PDS), the target market determination (TMD), monthly reports and annual reports. Part of an analyst's work is to check that these documents agree with each other and that the fund is within its stated limits. ASIC's reports on private credit in 2025 (REP 814 and REP 820) encourage more independent checking of this kind. The difficulty is that private credit documents are long, are updated often, and usually describe several layers of funds.

The aim was to see whether this checking can be done in a way a compliance team would accept. Every figure therefore comes with the page and the exact words it was taken from, and code confirms that those words appear on that page.

## How it works

| Step | Script | What it does |
|---|---|---|
| 1. Collect | `src/1_fetch.py` | Downloads LF1's 7 documents, the ASX Investment Products report for September 2026 and the ASIC register of licensees, and checks each file's checksum. Two files had changed at the source since they were first downloaded (see `VERSIONS.md`). |
| 2. Read | `src/2_pages.py` | Converts 250 PDF pages to text, one page at a time. |
| 3. Define | `schema.md` | Sets out 18 fields an analyst would check, covering who runs the fund, fees, distributions, allocation, credit risk and liquidity. |
| 4. Answer key | `gold/lf1.csv` | 29 values labelled by hand from the PDFs, used to measure accuracy. |
| 5. Extract | `src/3_extract.py`, `src/4_score.py` | An AI model (Claude Haiku 4.5 on Amazon Bedrock, Sydney region) reads every page and returns each value with a page and a quote. Code checks the evidence and then scores the results against the answer key. |
| 6. Compare | `src/5_compare.py` | Five kinds of rule compare the checked values and raise flags. Each flag is then reviewed (`flag_labels.csv`). |
| 7. Questions | `src/6_memo.py` | The AI model drafts questions for the manager from the confirmed inconsistencies only. Code rejects any question that does not cite a valid flag or that contains a number not found in the evidence. |

LF1 does not lend directly. It holds about 41% in the 12 Month Investment Account of the La Trobe Australian Credit Fund, which lends against Australian property, and about 59% in the La Trobe US Private Credit Fund, which lends to US companies through LGAM Private Credit LLC. Every LF1 document describes both holdings, but the second is easy to overlook. Each field therefore records which fund it relates to.

## The answer key

The answer key contains 29 values from the PDS, LF1's annual report, the Credit Fund's annual report and the monthly profile. I labelled 28 of them by reading the PDFs. The remaining value, which records that the annual report does not state a total fee ratio anywhere, was labelled by an AI model before any extraction was run. Every row was then checked against its page, and 4 of my 28 labels were corrected. In each case I had taken a nearby figure on the right page:

- Row 23 recorded the value of loans with a loan-to-value ratio above 75% ($1,169.9m) instead of the stated portfolio maximum of 80%.
- Row 5 recorded the sentence about the responsible entity's fee instead of the sentence stating that the Manager receives nothing directly from LF1.
- Row 9 recorded a sentence about allocation instead of the fee line showing 1.93%.
- Row 14 recorded the 12 Month account's expenses in thousands of dollars (187,405) instead of its cost ratio of 1.70%.

The answer key keeps my original value and the review note on each row. It is smaller than I would like, so the accuracy figures below should be read as an indication.

## How accurate is the extraction?

In the second run, the AI model returned 133 values from the 7 documents. The code checked each one as follows:

| Result of the check | Values | Outcome |
|---|---|---|
| Quote found on the page the model cited | 90 | Kept |
| Quote found on one other page | 29 | Kept, with the page corrected |
| Quote found on several other pages | 5 | Dropped, because the right page cannot be identified |
| Value not contained in its own quote | 4 | Dropped |
| Quote not found anywhere in the document | 3 | Dropped, because it was reworded or invented |
| No quote given | 2 | Dropped |
| A deliberately false quote added as a test | 1 | Dropped, as intended |

In the first run, 31 quotes were genuine but were given with the page number printed on the page rather than the page of the PDF file. For example, page 78 of the PDS is page 80 of the file. Instructing the model to use the file's page number did not fix this, so the code now locates each quote and takes the page number from where the quote actually appears. Both runs are kept in `outputs/lf1/extract/`.

Scores against the answer key, using the values that passed the check in the second run:

| Measure | Result |
|---|---|
| Recall: answer-key values found | **26 of 29 (90%)** |
| Recall on the 28 values I labelled | 25 of 28 |
| Recall on the value labelled by an AI model | 1 of 1 |
| Precision: values on answer-key pages that were correct | **21 of 22 (95%)** |
| First run, for comparison | Recall 25 of 29, precision 18 of 19 |

The model made three kinds of error:

- It followed a label rather than its meaning. The monthly profile shows the total fees and costs of 1.93% in a row headed "Management Fee", and the model recorded this as the responsible entity's own fee, which is 0.05%.
- It reworded a quote, so a correct value was dropped. For the 3.25% target margin, the model quoted "target cash distribution yield" where the page says "target a cash distribution yield". The check is strict by design. It costs some correct values, but it stops invented quotes from getting through.
- It missed a value in a table. The 12 Month account's cost ratio of 1.70% sits in a table with one column per account, and the model did not return it.

Only 22 of the model's values fall on pages covered by the answer key. The remaining 97 passed the check but cannot be scored, and their errors appear instead in the flags described below.

## Where the documents disagree

The process made 176 comparisons for LF1. Of these, 103 agreed, 15 checked a value against a stated limit and found it within the limit, and 27 compared values from different dates and were set aside (a loan count in April 2025 and another in June 2026 is a change over time, not an inconsistency). The remaining 24 raised a flag.

Many figures agree across documents. LF1's investment of $110.2m in the 12 Month account at 30 June 2026 is the same in LF1's annual report and in the Credit Fund's annual report, as are that account's loan-to-value ratio of 67.5% and its 10,789 loans. The total fees and costs of 1.93% in the PDS match the management expense ratio in the ASX report. The target margin of 3.25% is the same in the five documents where the quote passed the check (the TMD, the FAQs, the monthly profile, the investor presentation and the annual report). The responsible entity's licence, AFSL 222213, appears on the ASIC register under the same name and has been held since 2002. LF1's actual allocation of about 41% and 59%, at both 30 June and 31 August 2026, is within its limits of 20% to 100% and 0% to 80%.

Each of the 24 flags was reviewed against both pages:

| Review outcome | Flags | Typical cause |
|---|---|---|
| Extraction error | 18 | A target allocation recorded as an actual allocation (8); the parent company's company number taken as the responsible entity's (6); the "Management Fee" row described above (2); a limit belonging to the 12 Month account recorded against LGAM (1); a conclusion the page does not state (1) |
| Different funds or bases | 2 | Two correct values about different funds. The ASX report shows no outperformance fee for LF1 itself, while the PDS's 0.07% is a fee LF1 bears through LGAM |
| No real difference | 2 | 64.7% rounded to 65%; the Manager is not on the register of licensees because it acts as an authorised representative |
| **Genuine inconsistency** | **2** | Described below |

As expected, most flags came from errors in the process, which is why each flag is reviewed before it is used.

The two genuine inconsistencies are:

1. **How the Manager is paid.** Page 27 of the PDS states that no separate fee is payable to the Manager by the responsible entity. Page 61 of the same document states that the responsible entity pays the Manager a fee out of its own remuneration.
2. **The loan-to-value ratio of the US portfolio at 30 June 2026.** LF1's annual report gives 38.8% (page 7), while the monthly profile gives 38.4% (page 5, and page 3 through footnote 14), both as at 30 June 2026. The difference is small and may come from rounding or from a different valuation basis, which is the question to ask.

## Questions for the manager

The AI model drafted these questions from the two inconsistencies, and code checked them. They are shortened here; the full wording is in `outputs/lf1/memo.md`.

1. Which statement about the Manager's fee is correct: that no separate fee is payable to the Manager by the responsible entity (PDS page 27), or that the responsible entity pays the Manager a fee out of its own remuneration (PDS page 61)? How do the two statements reconcile? (flag F6ea608)
2. The weighted average loan-to-value ratio of the US portfolio is 38.8% in the annual report (page 7) and 38.4% in the monthly profile (page 5), both at 30 June 2026. What explains the difference, and which figure should be relied on? (flag Feb3996)

As a test, two false questions were added, one containing a made-up number and one citing a flag that does not exist. The check rejected both.

## Other observations from reading the documents

The following points came up while reading the documents to design the fields. They fall outside what the process extracts, so they were not scored or flagged:

- The PDS's table of loan-to-value bands does not add up. On page 48, the five bands total 104.5% of the 12 Month account, and their dollar amounts ($11.4bn) exceed the loan book shown beside them ($9.9bn). I confirmed this on the page image. The page attributes differences to rounding, but 4.5 percentage points is more than rounding would explain. Because the error is within a single document, no comparison between documents would detect it.
- The PDS estimate of 1.93% for total fees and costs assumes an equal split between the two underlying funds. The actual split is about 41% and 59%, and LF1's annual report does not restate the figure using actual costs.
- LF1 intends to offer to buy back 5% of its units each quarter, while 59% of its assets are held in a fund whose own redemptions are capped at 5% of units each quarter.

## The other three funds: MXT, MA1 and REV

The purpose of this step was to see whether the method works beyond the fund it was built on. The scripts, the model and the checks were unchanged. Only the list of fields changed.

None of the three trusts lends directly, and in each case the structure is easy to overlook:

- MXT (Metrics Master Income Trust) holds units in a sub-trust, which invests in three Metrics funds. The 2026 reports do not mention the sub-trust.
- MA1 (MA Credit Income Trust) holds all of its assets in one wholesale fund, of which it owns about 63%, and that fund invests in other MA funds.
- REV (Revolution Private Credit Income Trust) holds about 99.6% of its assets in one unlisted fund, Revolution Private Debt Fund II. That fund now owns more than 5% of REV, bought on market.

Because the fields defined for LF1 do not apply to these trusts, `schema-funds.md` defines 19 fields that suit any listed credit trust. They cover fees, target return, number of loans, loan-to-value ratio, arrears, borrowing, net tangible assets, distributions, fund size, buy-backs, the mix of strategies and its permitted ranges, and the share held outside Australia. Every value records which fund it relates to. Each fund's documents were mapped page by page before extraction, and the model was given the list of fields but none of the values.

The check needed one change. In these funds' monthly reports, many figures sit in tables where the extracted text separates the label from the number (for example "Price / NAV $1.91 / $2.00"). The model quotes these as a label followed by a number, which is reasonable but not word for word. I therefore added a second, weaker test for table entries. If the quote is only a short label and the value, the value must appear on the page and every word of the label must appear within 300 characters of it. These values are counted separately, and the false test quote was still rejected for every fund.

| | MXT | MA1 | REV |
|---|---|---|---|
| Documents / pages | 6 / 162 | 4 / 233 | 4 / 141 |
| Values returned | 121 | 122 | 90 |
| Kept: exact quote | 86 | 93 | 64 |
| Kept: table entry | 20 | 17 | 11 |
| Dropped | 15 | 12 | 15 |
| Comparisons made | 152 | 106 | 69 |
| Agreed | 91 | 37 | 31 |
| Limits checked (all within) | 11 | 10 | 8 |
| Flags | 20 | 20 | 9 |
| Genuine inconsistencies after review | **1** | **3** | **0** |

There is no answer key for these three funds, so recall and precision cannot be measured for them, and the review of flags is the main evidence of accuracy. Each flag was reviewed against both pages by an AI model, and every flag marked as a genuine inconsistency was then checked against the pages a second time. That second check changed one outcome (MXT's management expense ratio, described below).

Of the 49 flags, 19 were extraction errors. The most common were a company number recorded as a licence number (behind six flags), the minimum and maximum amounts of a capital raising recorded as net assets, and total costs recorded as the management fee. A further 10 compared a 2020 PDS estimate with a 2026 actual, 12 showed no real difference (rounding, or a fee assumption within its permitted range), 4 compared different funds or bases, and 4 were genuine inconsistencies.

The four genuine inconsistencies, as questions for the manager (the full wording is in `outputs/<fund>/memo.md`):

- **MA1, direct asset lending below its range.** Direct asset lending was 19% at 30 September 2026 (investor update, pages 2 and 4), against a range of 30% to 50% in the PDS (page 18). The PDS allows the manager to move up to 10 percentage points outside the range in the ordinary course (page 36), so the lowest expected level is 20%. (flag F1264f4)
- **MA1, global assets above their limit.** About 17% of assets were outside Australia and New Zealand at 30 September 2026 (investor update, page 4), against a maximum of 10% of net asset value in the PDS (page 18). (flag F52d587)
- **MA1, the management expense ratio shown by the ASX.** The ASX report for September 2026 gives 0.90%, while the PDS estimates total management fees and costs at 1.21% of net asset value (page 72). 0.90% is the manager's fee on direct investments, which suggests the ASX figure does not include the costs of the underlying funds. (flag Fa118cc)
- **MXT, the management expense ratio shown by the ASX.** The ASX report for September 2026 gives 0.86%. MXT's own portfolio report for June 2026 (page 1) shows 0.86% as the figure at its 2017 listing and 0.59% for the 2026 financial year. (flag F8eebd5)

REV's 9 flags all had ordinary explanations, such as the manager's total funds under management recorded as REV's size, targets compared with actual figures, and rounding.

Reading the documents also turned up the following points, which were checked in the text but fall outside the fields or comparisons the process covers:

- **MA1's buy-back policy has changed.** The PDS states that the responsible entity intends to make a buy-back offer each quarter "for up to 5% of the issued capital" (page 57). The September 2026 update states that it would consider "up to 2.5% of issued units each quarter", and only when units trade at a discount (page 5). I found no supplementary PDS covering this change. The process did flag 5% against 2.5%, but it paired the update with the annual report's record of an actual offer, so the flag was correctly treated as a difference in dates.
- **REV's statement on related parties.** The PDS states that, because the trust invests in the underlying fund, "these related party transactions may be a potential conflict of interest" (page 107). The September 2026 report states that "there are no instances of related-party transactions" (page 4).
- **REV's underlying fund reports net borrowing above gross borrowing.** REV's annual RG 240 update, which reports against ASIC's disclosure benchmarks, gives net leverage of 8.2% and gross leverage of 7.6% (page 2), although net leverage is normally no higher than gross.
- **MXT's loan from its manager.** The PDS describes the loan as "up to $44.5 million" (page 29), while the pro forma table shows 44,875 in thousands of dollars (page 84).
- **MA1's manager licensee.** The PDS names MA Asset Management Ltd as the licensee (page 21), while the update names MAAM RE Ltd (page 14), and the update also states that no key service providers have changed.

Extending the work to three more funds showed three things. First, the structure of each fund needs to be understood before anything is compared: all four trusts invest through other funds, and a process that does not record which fund a figure belongs to will compare the wrong things. Second, the same errors recur from fund to fund, such as identifiers recorded in the wrong place, targets or scenarios recorded as actual figures, and totals recorded as components. Because they are predictable, clearer field instructions should reduce them. Third, the ASX report is a useful independent source, but it is not always current: for two of the four funds, its management expense ratio does not match the fund's own latest figure. All extraction runs for the four funds together cost about US$1.60.

## Running it automatically on AWS

Since 9 November 2026 the process has run daily in AWS, in the Sydney region. Each morning a small job downloads all 21 documents and the ASIC register and checks whether next month's ASX report has been published. When a file changes, it saves the new version, has the AI model read only that document again, reruns the checks and comparisons for that fund, updates a private log, and emails a summary of what changed and which new flags need review. LF1's accuracy against the answer key is recorded in CloudWatch on every run. The details, the test and the costs (well under US$1 a month) are in `AWS.md`.

Testing this showed one further point. When the same page was read a second time, the AI model took a date from the page heading instead of the footnote, and one genuine inconsistency was no longer flagged. The process now keeps a record of every reviewed flag and warns when a genuine inconsistency stops appearing.

## Limitations

- Agreement between documents does not show that a figure is correct. If every document repeats the same error, every check will pass.
- These are the documents published for retail investors. A research house would also use questionnaires, audited accounts of the underlying funds and loan-level data. The documents here include no statutory accounts for the US Private Credit Fund or LGAM.
- Because LF1 invests through other funds, much of the detail about risk sits in documents that were not collected.
- Only LF1 has an answer key. The other three funds are assessed through the review of flags alone, and that review was carried out by an AI model and has not yet been checked by a person.
- The answer key is small (29 values, 28 of them labelled by hand), so the recall of 90% is an indication rather than a precise measure. Precision is based on only 22 values.
- The model was asked to keep quotes to 12 words but exceeded 15 words in about half of its answers. Only short quotes are reproduced in this repository.
- The work covers four funds, one model and one run of each setting. Haiku 4.5 was the model available on the account; a larger model would probably read tables and labels more accurately.

## Files

- `gold/lf1.csv`: the answer key, with the labeller, the review note and my original value on each row (long values are shortened to 14 words).
- `outputs/lf1/extract/`: the prompt given to the model, the scores by field, the answer-key matches and a summary. The first run is in `run1/`.
- `outputs/lf1/checks.csv` lists every comparison, `outputs/lf1/flags.csv` lists the 24 flags with their review outcomes, and `flag_labels.csv` holds the reviews for all four funds.
- `outputs/lf1/memo.md`: the questions for the manager.
- The same files for the other three funds are in `outputs/mxt/`, `outputs/ma1/` and `outputs/rev/`, without answer-key scores. Their fields are defined in `schema-funds.md` and `src/fund_fields.py`.
- Not included: the fund documents, their page text and the AI model's full answers, because they reproduce the documents at length. Running `python src/1_fetch.py` and then `python src/2_pages.py` recreates the documents and their text, and `python src/3_extract.py <FUND>` asks the model again (the results will differ slightly).

To rerun one fund, use `python src/3_extract.py MA1 --rerun`, followed by `4_score.py MA1`, `5_compare.py MA1` and `6_memo.py MA1` (the fund can be LF1, MXT, MA1 or REV). Any new flags receive new identifiers and appear without a review outcome.
