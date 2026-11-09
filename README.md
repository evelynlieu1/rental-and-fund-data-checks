# Rental and fund data checks

Two small, working data pipelines on Australian public data, each with an AI step that is checked by plain code before anything is trusted.

| Project | Question | What it found |
|---|---|---|
| [rental-stock-drift](rental-stock-drift/) | A vacancy rate divides empty rentals by the number of rentals. If that number still comes from the 2021 Census, how far off is it now, postcode by postcode? | In the fastest-growing NSW and Queensland postcodes, rental stock is 1.2 to 2.4 times the 2021 count, so a 2021-based vacancy rate there would read 1.2 to 2.4 times too high. Student areas look similar but aren't new homes, and the method flags them. |
| [fund-document-checker](fund-document-checker/) | Do an ASX-listed private credit fund's own documents (PDS, TMD, monthly reports, annual reports) agree with each other, and with the ASX and ASIC? | Across four funds, 503 comparisons and 73 flags. After review, 6 are real disagreements, written up as questions for the manager. The AI found 26 of 29 values in a hand-labelled answer key. |

Both run on AWS (Lambda, S3, EventBridge, Bedrock in Sydney, SES), and each has a full write-up in its `REPORT.md`.

## How the AI is kept honest

- **Rental stock drift:** the AI writes a short note per postcode from one row of data. Code extracts every number in the note and rejects the note if any number isn't in the row. The first run was rejected in full (the model read bond counts as dollars); the fix and the rejected notes are kept.
- **Fund document checker:** the AI must return every value with the page and the exact words it came from. Code checks the words are really on that page, and takes the page from the text itself, because the model often cites the number printed on the page instead. A planted fake quote is rejected every run. Accuracy is measured against an answer key labelled by hand from the PDFs.

## Running it

Python 3.11 or later: `pip install -r requirements.txt`. Each project's `src/` scripts are numbered in the order they run, and `src/1_fetch.py` downloads the public source files listed in `data/MANIFEST.csv` (with their checksums). The AI steps use Claude on Amazon Bedrock and need an AWS profile with Bedrock access.

Source data is not stored here: download it with the fetch scripts. The fund documents are the managers' copyright, so this repo quotes them in short extracts only.

## About

Independent work by Evelyn Lieu on public data. Not commissioned by, or affiliated with, any research house or any fund named here. Nothing here is advice, and a disagreement between two documents is a question to ask, not a finding that anything is wrong.
