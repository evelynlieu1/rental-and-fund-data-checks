"""Phase 8, Lambda 1 of 2: the watcher. Runs daily on a schedule.

For every fund document in src/2_pages.py (URLs from data/MANIFEST.csv), plus the ASIC register and the ASX report:
  1. download it and take its checksum
  2. if the checksum differs from the last one seen (state/versions.json in S3), save the new file to raw/
     (the bucket keeps old versions), turn it into page text (pages/<fund>/<doc>.json), and log the change
  3. try next month's ASX Investment Products report; if it's out, save it and use it from now on
  4. if anything changed, start the pipeline Lambda for the funds affected; if a download failed, email that

Nothing is sent when nothing changed. Needs: BUCKET, PIPELINE_FUNCTION, EMAIL (SES-verified) in the Lambda settings.
"""
import calendar
import csv
import datetime
import hashlib
import importlib.util
import json
import os
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

import boto3

BUCKET = os.environ["BUCKET"]
PROJECT = Path(__file__).parent / "project"
s3 = boto3.client("s3")

spec = importlib.util.spec_from_file_location("pages", PROJECT / "src" / "2_pages.py")  # name starts with a digit
pages_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pages_mod)

ASIC_FILE = "raw/asic/afs_lic_202610.csv"
ASX_URL = "https://www.asx.com.au/content/dam/asx/issuers/asx-investment-products-reports/{y}/excel/asx-investment-products-{m}-{y}-abs.xlsx"
MONTH_SPELLINGS = {9: ["sep", "sept", "september"], 7: ["jul", "july"], 6: ["jun", "june"]}  # ASX isn't consistent


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research; fund document check)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def load_state():
    return json.loads(s3.get_object(Bucket=BUCKET, Key="state/versions.json")["Body"].read())


def next_asx(state):
    """Try next month's ASX report under each spelling the ASX has used."""
    last = datetime.date.fromisoformat(state["asx_as_at"])
    y, m = (last.year + 1, 1) if last.month == 12 else (last.year, last.month + 1)
    names = MONTH_SPELLINGS.get(m, []) + [calendar.month_abbr[m].lower(), calendar.month_name[m].lower()]
    for name in dict.fromkeys(names):
        try:
            body = fetch(ASX_URL.format(y=y, m=name))
        except Exception:
            continue
        if body[:2] == b"PK":  # an .xlsx is a zip file; an error page isn't
            key = f"raw/asx/asx-investment-products-{calendar.month_abbr[m].lower()}-{y}-abs.xlsx"
            month_end = datetime.date(y, m, calendar.monthrange(y, m)[1]).isoformat()
            return key, month_end, body
    return None


def handler(event, context):
    today = datetime.datetime.now(ZoneInfo("Australia/Sydney")).date().isoformat()  # Lambda runs on UTC
    state = load_state()
    manifest = {r["file"]: r["url"] for r in csv.DictReader(open(PROJECT / "data" / "MANIFEST.csv", encoding="utf-8"))}
    changed, rerun, failed, log = {}, set(), [], []

    for file, (fund, doc, *_rest) in pages_mod.DOCS.items():
        try:
            body = fetch(manifest[file])
        except Exception as e:
            failed.append(f"{file}: {type(e).__name__}: {e}")
            continue
        sha = hashlib.sha256(body).hexdigest()
        known = state["files"].get(file, {})
        known["checked"] = today
        if sha != known.get("sha256"):
            if body[:4] != b"%PDF":
                failed.append(f"{file}: the link no longer returns a PDF (left unchanged)")
                continue
            s3.put_object(Bucket=BUCKET, Key=file, Body=body)
            tmp = Path("/tmp") / Path(file).name
            tmp.write_bytes(body)
            rows = pages_mod.page_rows(tmp, file)
            s3.put_object(Bucket=BUCKET, Key=f"pages/{fund}/{doc}.json", Body=json.dumps(rows).encode())
            state["history"].append({"date": today, "file": file, "old_sha256": known.get("sha256"), "new_sha256": sha,
                                     "bytes": len(body), "pages": len(rows)})
            known.update({"sha256": sha, "bytes": len(body), "changed": today})
            changed.setdefault(fund, []).append(doc)
            log.append(f"{fund} {doc}: new version ({len(body):,} bytes, {len(rows)} pages)")
        state["files"][file] = known

    # The ASIC register: same link; if it changes, every fund's licence check reruns
    try:
        body = fetch(manifest[ASIC_FILE])
        sha = hashlib.sha256(body).hexdigest()
        if sha != state["files"].get(ASIC_FILE, {}).get("sha256") and b"REGISTER_NAME" in body[:40]:  # really the register
            s3.put_object(Bucket=BUCKET, Key=ASIC_FILE, Body=body)
            state["files"][ASIC_FILE] = {"sha256": sha, "bytes": len(body), "changed": today, "checked": today}
            state["history"].append({"date": today, "file": ASIC_FILE, "new_sha256": sha, "bytes": len(body)})
            rerun |= set(state["funds"])
            log.append("ASIC licensee register: new version")
    except Exception as e:
        failed.append(f"{ASIC_FILE}: {type(e).__name__}: {e}")

    # The ASX report: a new file each month
    found = next_asx(state)
    if found:
        key, month_end, body = found
        s3.put_object(Bucket=BUCKET, Key=key, Body=body)
        state.update({"asx_latest": key, "asx_as_at": month_end})
        state["history"].append({"date": today, "file": key, "bytes": len(body)})
        rerun |= set(state["funds"])
        log.append(f"ASX report for {month_end[:7]} published: {key}")

    s3.put_object(Bucket=BUCKET, Key="state/versions.json", Body=json.dumps(state, indent=1).encode())
    summary = {"date": today, "changed": changed, "rerun": sorted(rerun - set(changed)), "failed": failed, "log": log}
    print(json.dumps(summary, indent=1))

    if changed or rerun:
        boto3.client("lambda").invoke(FunctionName=os.environ["PIPELINE_FUNCTION"], InvocationType="Event",
                                      Payload=json.dumps(summary).encode())
    elif failed and os.environ.get("EMAIL"):
        boto3.client("ses").send_email(
            Source=os.environ["EMAIL"], Destination={"ToAddresses": [os.environ["EMAIL"]]},
            Message={"Subject": {"Data": f"Fund documents {today}: {len(failed)} downloads failed"},
                     "Body": {"Text": {"Data": "Nothing changed, but these couldn't be checked:\n\n" + "\n".join(failed)}}})
    return summary
