# Do a private credit fund's own documents agree?

Reads every document an ASX-listed private credit fund publishes (PDS, TMD, monthly reports, annual reports), pulls out the terms an analyst checks, each with its page and exact words, and lists every place the documents disagree with each other, with the ASX's figures or with the ASIC licence register. Each disagreement becomes a polite question for the manager. Built on La Trobe Private Credit Fund (LF1), then run unchanged on MXT, MA1 and REV. Results and caveats: [REPORT.md](REPORT.md).

## Steps

| Script | What it does |
|---|---|
| `src/1_fetch.py` | Downloads the fund documents, the ASX Investment Products report and the ASIC licensee register, and checks their checksums |
| `src/2_pages.py` | Turns every PDF into page-by-page text |
| `src/3_extract.py` | Asks Claude (Haiku 4.5 on Bedrock) for each field, with a page and a quote |
| `src/4_score.py` | Checks every quote is really on the page (code finds the page), then scores LF1 against the hand-labelled answer key |
| `src/5_compare.py` | Compares the documents and raises flags: same field with different values, limits against actuals, ASX against PDS, feeder against underlying fund, entities against the ASIC register |
| `src/6_memo.py` | Drafts questions for the manager from the reviewed real disagreements; code rejects any line without a valid flag or with a number not in the evidence |

Each of 3 to 6 takes the fund code: `python src/3_extract.py LF1` (or MXT, MA1, REV).

## What's here

- `schema.md` (LF1) and `schema-funds.md` (the other three): what to extract, where it is, and the traps.
- `EXTRACTION-NOTES.md`: which pages the PDF text gets wrong. `VERSIONS.md`: source files that changed after the first download.
- `gold/lf1.csv`: the answer key, labelled by hand from the PDFs.
- `flag_labels.csv`: every flag's review label and reason.
- `outputs/<fund>/`: flags, every comparison made, the manager questions, the extraction prompt and the scores.
- `aws/` and `AWS.md`: the daily watcher and pipeline on AWS, and what testing them showed.

Not here: the fund documents, their page text and the AI's raw replies, because they copy the documents at length. The fetch and page scripts recreate the first two.
