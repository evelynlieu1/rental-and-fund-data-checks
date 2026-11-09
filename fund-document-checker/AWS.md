# Running it on AWS

Built and tested 9 Nov 2026 in a personal AWS account (Sydney, ap-southeast-2). It watches all four funds' documents every morning and reruns the pipeline only when something changes.

## What runs, and when

**Every day at 6:30 am Sydney time**, EventBridge Scheduler (`fund-docs-daily`) starts the watcher.

**Lambda 1, the watcher** (`fund-docs-watch`, `aws/watch.py`):
1. Downloads all 21 fund documents from their links, plus the ASIC licensee register.
2. If a checksum differs from the last one seen, it saves the new file (the bucket keeps old versions), reads its pages and logs the change in `state/versions.json`.
3. Tries next month's ASX Investment Products report under each spelling the ASX has used.
4. If nothing changed, it stops quietly. It only emails if a download failed.
5. If something changed, it starts the pipeline.

**Lambda 2, the pipeline** (`fund-docs-pipeline`, `aws/pipeline.py`):
1. For each fund affected, runs the same scripts as on the laptop: `3_extract` (the AI only reads the changed document; everything else is cached), `4_score`, `5_compare`, `6_memo`.
2. Saves the outputs to S3 and writes a private HTML log per fund (`reports/<fund>.html`).
3. Sends LF1's recall and precision, and each fund's "flags to review", to CloudWatch (`FundDocs`).
4. Emails a summary: what changed, new flags that need a person, a 7-day link to each fund's log, and a warning if a flag already reviewed as a real disagreement is no longer raised.

## Why two Lambdas

Reading PDFs needs PyMuPDF; the rest needs pandas. Together they pass Lambda's 250 MB limit, and without Docker on this laptop a container image wasn't an option. So the watcher has PyMuPDF and no pandas (`build/watch.zip`, 25 MB), and the pipeline has the anthropic library plus AWS's pandas layer, as in project 1 (`build/pipeline.zip`, 7.5 MB). `src/2_pages.py` was changed so the watcher can use its page reader without pandas.

## What's in AWS

The names below are examples; use your own.

| Thing | Name | Notes |
|---|---|---|
| S3 bucket | `my-fund-docs-bucket` | **Private** (all public access blocked): it holds copyright fund documents. Versioning on; old versions deleted after 400 days. |
| Lambda | `fund-docs-watch` | Python 3.13, 1 GB, 10 min timeout, no retries |
| Lambda | `fund-docs-pipeline` | Python 3.13, AWSSDKPandas layer, 2 GB, 15 min timeout, no retries |
| Role | `fund-docs-role` | Only this bucket, Bedrock InvokeModel, SES send, CloudWatch metrics in the FundDocs namespace, and starting the pipeline |
| Role | `fund-docs-scheduler-role` | Can only start the watcher |
| Schedule | `fund-docs-daily` | cron(30 6 * * ? *), Australia/Sydney |

Bucket layout: `raw/` the documents, `pages/<FUND>/<doc>.json` page text, `cache/<fund>/extract/raw/` the AI's saved answers, `outputs/<fund>/` checks, flags, memo, scores, `reports/<fund>.html` the logs, `config/flag_labels.csv` the reviewed labels, `state/versions.json` every file's checksum and change history, `state/known_flags/` the reviewed flags per fund.

## How a new flag gets reviewed

The pipeline can raise a flag; only a person can label it. When the email lists a new flag, the review happens on the laptop as before: look at both pages, add a row to `flag_labels.csv`, then copy that file to `config/flag_labels.csv` in the bucket. The next run picks up the label.

## The test (9 Nov)

No fund had published anything new since the documents were collected, so a new LF1 monthly profile was **simulated**: its checksum in `state/versions.json` was set to a fake old value.

1. The watcher saw a "new version", saved it, re-read its 6 pages, and started the pipeline. Correct.
2. The first pipeline run failed: the build had installed the newest anthropic library, which no longer accepts `temperature`. Fixed by pinning the version the scripts were tested with (0.97.0). The failure itself was emailed, as designed.
3. The next run worked in 15 seconds, but showed 16 flags instead of 24: the re-read profile had a "vehicle" column the older LF1 answers lacked, so its values stopped being compared with the other documents. Fixed: LF1 doesn't group by vehicle.
4. Then 23 flags instead of 24. **The same document, read again, gave one different answer**: the AI dated the profile's 38.4% to 31 July (the page header) instead of 30 June (the asterisk footnote), so the 38.4% vs 38.8% disagreement (Feb3996) was no longer compared. That's why the pipeline now warns when a reviewed real disagreement disappears; the next run's email did exactly that.
5. The original profile extraction was restored. The cloud now matches the laptop for all four funds: LF1 24 flags (2 real), recall 26 of 29, precision 21 of 22; MXT 20 (1 real); MA1 20 (3 real); REV 9 (0 real). Every flag already labelled.

The re-read answer is kept for the record: it showed that the AI isn't fully repeatable even at temperature 0, which is the strongest argument for keeping a person on the review step.

## Cost

- The watcher: about 30 seconds a day. Free tier.
- The pipeline only runs on a change, and only re-reads the changed document: a monthly profile costs about 2 US cents in Bedrock; a whole new PDS about 15 cents.
- S3: about 60 MB plus old versions. Cents a month.
- CloudWatch: 7 custom metrics, inside the 10 free. (The first test sent 18; the extras stop costing once they stop receiving data.)
- Expected total: well under US$1 a month.

## Not built, on purpose

- **Textract** for the pages PyMuPDF reads badly: the table rule in the evidence check covers most of them, and Textract would add cost and another service for a few pages.
- **DynamoDB** for evidence rows: the CSVs in S3 are enough at this size, and the HTML log is what a person reads.
- **New MXT monthly reports**: MXT publishes each month at a new link, so the watcher can't see them without scraping Metrics' website. LF1's, MA1's and REV's "latest" links and the ASX report are covered.

## To change the code

Edit `aws/watch.py` or `aws/pipeline.py` (or anything in `src/`), then `python aws/build.py` and upload the zip to the function (`aws lambda update-function-code --function-name ... --zip-file fileb://build/pipeline.zip --region ap-southeast-2`, with your own AWS profile). `aws/seed.py` copied the laptop's state into the bucket once; it overwrites `state/versions.json`, so don't run it again by accident.

To switch it off: disable the schedule `fund-docs-daily` in EventBridge Scheduler.
