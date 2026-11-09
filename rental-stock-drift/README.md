# Rental stock drift since the 2021 Census

A vacancy rate is empty rentals divided by all rentals. The "all rentals" count usually starts from the Census, and the latest results are from August 2021. Where thousands of homes have been built since, a count frozen at 2021 is too small and the vacancy rate reads too high.

This measures, for every NSW and Queensland postcode, how much rental stock has grown since the 2021 Census, using rental bonds held as the growth signal, and lists where a 2021-based vacancy rate is most likely to be off. Results and caveats: [REPORT.md](REPORT.md).

## Steps

| Script | What it does |
|---|---|
| `src/1_fetch.py` | Downloads the Census, NSW, Queensland and Victorian files in `data/MANIFEST.csv` and checks their checksums |
| `src/2_load.py` | Reads each source into one tidy table (postcode, period, count) |
| `src/3_reconcile.py` | Checks bonds against Census renters at 2021, and explains every postcode that doesn't join |
| `src/4_drift.py` | Bond growth since 2021, the top 20 postcodes per state, and a robustness check |
| `src/5_notes.py` | A short note per postcode from Claude on Bedrock, rejected by code if any number isn't in the data |
| `src/6_rockbank.py` | Rockbank (VIC) through its council, because Victoria publishes bonds by council only |

`outputs/` has the top 20 tables, the sense checks against real building, the explained outliers and the AI notes (including the rejected first run). The full postcode-by-postcode tables aren't included because the NSW bond data has no reuse licence; the scripts recreate them.

## On AWS

`aws/lambda_function.py` runs the pipeline daily on a schedule (EventBridge Scheduler and Lambda in Sydney): it fetches the sources, keeps any changed file under a dated folder in a private S3 bucket, writes the results, and emails a short summary through SES. `aws/build.py` builds the upload package.

## Sources

ABS Census 2021 DataPacks (G37), CC BY 4.0. NSW Fair Trading rental bond data. Residential Tenancies Authority (QLD) bond statistics, CC BY 4.0. Homes Victoria Rental Report. Links, dates and checksums are in `data/MANIFEST.csv`.
