"""One-off: copy the laptop's current state into the S3 bucket, so the first cloud run starts where the laptop is.

Run from the project folder:  python aws/seed.py my-fund-docs-bucket
Uses your AWS credentials (for example, set AWS_PROFILE). Uploads (to a PRIVATE bucket: the fund documents are copyright):
  raw/...                  the fund PDFs, the September ASX report and the ASIC register
  pages/<FUND>/<doc>.json  page text, from data/processed/pages.parquet
  cache/<fund>/extract/raw/*.json  the AI's saved answers (so nothing is paid for twice)
  config/flag_labels.csv   the reviewed labels
  state/versions.json      the checksum of every file as processed here
Re-running it overwrites state/versions.json, so only run it again on purpose.
"""
import datetime
import os
import hashlib
import json
import sys
from pathlib import Path

import boto3
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "data"
BUCKET = sys.argv[1]
s3 = boto3.Session(profile_name=os.environ.get("AWS_PROFILE"), region_name="ap-southeast-2").client("s3")
ASX = "raw/asx/asx-investment-products-sep-2026-abs.xlsx"
ASIC = "raw/asic/afs_lic_202610.csv"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


today = datetime.date.today().isoformat()
pages = pd.read_parquet(DATA / "processed" / "pages.parquet")
files = sorted(pages.file.unique()) + [ASX, ASIC]

state = {"funds": sorted(pages.fund.unique()), "asx_latest": ASX, "asx_as_at": "2026-09-30", "files": {}, "history": []}
for f in files:
    s3.upload_file(str(DATA / f), BUCKET, f)
    state["files"][f] = {"sha256": sha256(DATA / f), "bytes": (DATA / f).stat().st_size, "checked": today, "changed": ""}
print(f"{len(files)} source files uploaded")

for (fund, doc), g in pages.groupby(["fund", "doc"]):
    rows = g.sort_values("pdf_page").to_dict("records")
    s3.put_object(Bucket=BUCKET, Key=f"pages/{fund}/{doc}.json", Body=json.dumps(rows, default=str).encode())
print(f"{pages.groupby(['fund', 'doc']).ngroups} page files uploaded")

n = 0
for fund in state["funds"]:
    for path in (PROJECT / "outputs" / fund.lower() / "extract" / "raw").glob("*.json"):
        s3.upload_file(str(path), BUCKET, f"cache/{fund.lower()}/extract/raw/{path.name}")
        n += 1
print(f"{n} cached extraction files uploaded")

s3.upload_file(str(PROJECT / "flag_labels.csv"), BUCKET, "config/flag_labels.csv")
s3.put_object(Bucket=BUCKET, Key="state/versions.json", Body=json.dumps(state, indent=1).encode())
print("labels and state uploaded")
