# Which version of each file this project uses

`data/MANIFEST.csv` records what was downloaded on 4 Nov 2026. Some sources replace files at the same link, so a fresh download can differ. Every difference is listed here, with the version actually used. A value extracted from a file is only valid for that version.

| File | Manifest version (4 Nov 2026) | Version used (downloaded 8 Nov 2026) | Why it differs |
|---|---|---|---|
| `raw/lf1/lf1_roadshow_deck_2026-07.pdf` | July 2026 roadshow deck, 18 pages, 2,845,198 bytes | **October 2026** deck, 18 pages, 1,647,996 bytes, PDF created 2 Nov 2026 | La Trobe replaced the deck at the same URL. The file name still says 2026-07; `src/2_pages.py` dates it 2026-10. |
| `raw/asic/afs_lic_202610.csv` | October 2026 extract, 6,541 licensees, 11,382,558 bytes | October 2026 extract re-issued 4 Nov 2026 20:51 UTC (after the first download), 6,548 licensees, 11,395,200 bytes | data.gov.au updated the file at the same URL the same day. |

All other quick-version files match the manifest checksums: the LF1 PDS, TMD, FAQs, monthly fund profile (Aug 2026), LF1 annual report (FY2026), La Trobe Australian Credit Fund annual report (FY2026), the September 2026 ASX report and ASIC REP 814.
