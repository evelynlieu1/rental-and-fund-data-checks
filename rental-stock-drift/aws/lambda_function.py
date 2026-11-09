"""Runs project 1 inside AWS Lambda: scripts 1 to 5, then uploads to S3."""
import csv
import datetime
import hashlib
import os
import runpy
import shutil
import sys
from pathlib import Path

import boto3

BUCKET = os.environ["BUCKET"]          # set in the Lambda configuration, not in code
s3 = boto3.client("s3")
PACKAGED = Path(__file__).parent / "project"   # read-only copy inside the Lambda
WORK = Path("/tmp/project")                     # writable copy


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def exists_in_s3(key):
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        return True
    except s3.exceptions.ClientError:
        return False


def handler(event, context):
    run_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    # 1. Fresh writable copy of the project
    if WORK.exists():
        shutil.rmtree(WORK)
    shutil.copytree(PACKAGED, WORK)
    sys.path.insert(0, str(WORK / "src"))

    # 2. Run the data scripts in order. Any error stops the run and shows in CloudWatch.
    for script in ["1_fetch.py", "3_reconcile.py", "4_drift.py"]:
        print(f"=== {script}")
        runpy.run_path(str(WORK / "src" / script), run_name="__main__")

    # 3. The AI notes: a failure here shouldn't lose the data results
    notes_ok = True
    try:
        print("=== 5_notes.py")
        runpy.run_path(str(WORK / "src" / "5_notes.py"), run_name="__main__")
    except Exception as e:
        notes_ok = False
        print(f"Notes step failed, continuing: {e}")

    # 4. Raw files: upload only what S3 doesn't have yet, or what changed since the manifest
    manifest = {r["file"]: r["sha256"] for r in csv.DictReader(open(WORK / "data" / "MANIFEST.csv", encoding="utf-8"))}
    changed = []
    for path in (WORK / "data" / "raw").rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(WORK / "data").as_posix()          # e.g. raw/qld_rta/rta-bond-statistics.xlsx
        if sha256(path) != manifest.get(rel):
            key = f"raw/changed/{run_date}/{rel[4:]}"            # a new version: keep it, dated
            changed.append(rel)
        else:
            key = rel
        if not exists_in_s3(key):
            s3.upload_file(str(path), BUCKET, key)

    # 5. Results: everything in outputs/ goes to curated/<date>/, the key files also to reports/
    for path in (WORK / "outputs").rglob("*"):
        if path.is_file():
            rel = path.relative_to(WORK / "outputs").as_posix()
            s3.upload_file(str(path), BUCKET, f"curated/{run_date}/{rel}")
            if rel == "top20.csv" or rel.startswith("notes/"):
                s3.upload_file(str(path), BUCKET, f"reports/{rel}")

    summary = {"run_date": run_date, "changed_source_files": changed, "notes_ok": notes_ok}
    print(summary)

    # 6. Email the summary (only if an EMAIL setting exists; the address must be verified in SES)
    if os.environ.get("EMAIL"):
        boto3.client("ses").send_email(
            Source=os.environ["EMAIL"],
            Destination={"ToAddresses": [os.environ["EMAIL"]]},
            Message={"Subject": {"Data": f"Vacancy check {run_date}"},
                     "Body": {"Text": {"Data": str(summary)}}},
        )
    return summary