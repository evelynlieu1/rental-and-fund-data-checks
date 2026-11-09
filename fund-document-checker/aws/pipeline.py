"""Phase 8, Lambda 2 of 2: the pipeline. Started by the watcher when something changed (or by hand).

For each fund affected it runs the same scripts as on the laptop:
  3_extract (only for chunks not already cached, so only changed documents cost anything)
  4_score (the evidence check; for LF1 also the score against gold/lf1.csv)
  5_compare (flags; labels come from config/flag_labels.csv in S3, so reviewed flags stay reviewed)
  6_memo (questions from the flags labelled "real disagreement")
then saves the outputs to S3, writes a private HTML log per fund (reports/), sends the scores to CloudWatch
(namespace FundDocs) and emails a summary with the new flags that need a person to review them.

Event from the watcher: {"changed": {"LF1": ["profile"]}, "rerun": ["MXT"], "log": [...], "failed": [...]}.
By hand: {"funds": ["LF1"]} reruns a fund with nothing re-extracted.
Needs: BUCKET, EMAIL in the Lambda settings.
"""
import datetime
import html

import json
import os
import re
import runpy
import shutil
import sys
from pathlib import Path

import boto3
import pandas as pd

BUCKET = os.environ["BUCKET"]
PACKAGED = Path(__file__).parent / "project"
WORK = Path("/tmp/project")
s3 = boto3.client("s3")


def get(key, path=None):
    body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    return body


def keys(prefix):
    out = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefix):
        out += [o["Key"] for o in page.get("Contents", [])]
    return out


def run(script, fund):
    print(f"=== {script} {fund}")
    sys.argv = [script, fund]
    runpy.run_path(str(WORK / "src" / script), run_name="__main__")


def prepare(fund, changed_docs, state):
    """Rebuild the fund's working folder in /tmp from S3: pages, cached extraction, ASX, ASIC, labels."""
    rows = []
    for key in keys(f"pages/{fund}/"):
        rows += json.loads(get(key))
    (WORK / "data" / "processed").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(WORK / "data" / "processed" / "pages.parquet", index=False)

    raw_dir = WORK / "outputs" / fund.lower() / "extract" / "raw"
    shutil.rmtree(raw_dir, ignore_errors=True)
    raw_dir.mkdir(parents=True)
    for key in keys(f"cache/{fund.lower()}/extract/raw/"):
        name = key.rsplit("/", 1)[1]
        if any(re.fullmatch(rf"{re.escape(d)}_\d{{3}}-\d{{3}}\.json", name) for d in changed_docs):
            continue  # this document changed: its chunks are extracted again
        get(key, raw_dir / name)

    get(state["asx_latest"], WORK / "data" / state["asx_latest"])
    get("raw/asic/afs_lic_202610.csv", WORK / "data" / "raw" / "asic" / "afs_lic_202610.csv")
    os.environ["ASX_FILE"], os.environ["ASX_AS_AT"] = state["asx_latest"], state["asx_as_at"]
    try:
        get("config/flag_labels.csv", WORK / "flag_labels.csv")
    except s3.exceptions.NoSuchKey:
        pass  # the copy packaged with the code


def publish(fund):
    out = WORK / "outputs" / fund.lower()
    for path in out.rglob("*"):
        if path.is_file():
            rel = path.relative_to(out).as_posix()
            key = f"cache/{fund.lower()}/{rel}" if rel.startswith("extract/raw/") else f"outputs/{fund.lower()}/{rel}"
            s3.upload_file(str(path), BUCKET, key)


def esc(x):
    return html.escape(str(x if x == x else ""))  # NaN-safe


def report_html(fund, state, summary, flags, memo, run_date):
    docs = [(f, v) for f, v in state["files"].items() if f.startswith(f"raw/{fund.lower()}/")]
    doc_rows = "".join(f"<tr><td>{esc(f.rsplit('/', 1)[1])}</td><td>{esc(v.get('changed', '') or 'first copy')}</td>"
                       f"<td>{esc(v.get('checked', ''))}</td><td><code>{esc(v.get('sha256', '')[:12])}</code></td></tr>"
                       for f, v in sorted(docs))
    order = {"": 0, "real disagreement": 1}
    flags = flags.assign(_o=flags.label.map(lambda l: order.get(l, 2))).sort_values(["_o", "rule"])
    flag_rows = "".join(
        f"<tr class='{'todo' if not r.label else ('real' if r.label == 'real disagreement' else '')}'>"
        f"<td><code>{esc(r.flag_id)}</code></td><td>{esc(r.rule)}</td><td>{esc(r.field)} {esc(r.sub_field)}</td>"
        f"<td>{esc(r.a_doc)} p{esc(r.a_page)}: <b>{esc(r.a_value)}</b> {esc(r.a_as_at)}<br><small>{esc(r.a_quote)}</small></td>"
        f"<td>{esc(r.b_doc)} p{esc(r.b_page)}: <b>{esc(r.b_value)}</b> {esc(r.b_as_at)}<br><small>{esc(r.b_quote)}</small></td>"
        f"<td>{esc(r.label) or '<b>needs review</b>'}<br><small>{esc(r.reason)}</small></td></tr>"
        for r in flags.itertuples())
    scores = "".join(f"<li>{esc(k)}: {esc(v)}</li>" for k, v in summary.items() if k not in ("fund",))
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{fund} document check</title>
<style>body{{font:14px/1.45 system-ui,sans-serif;max-width:1100px;margin:2em auto;padding:0 16px;color:#222}}
table{{border-collapse:collapse;width:100%;margin:1em 0}}td,th{{border-bottom:1px solid #ddd;padding:6px;vertical-align:top;text-align:left}}
tr.todo{{background:#fff4d6}}tr.real{{background:#fde2e2}}small{{color:#555}}code{{font-size:12px}}</style></head><body>
<h1>{fund}: do the fund's own documents agree?</h1>
<p>Last run {esc(run_date)}. Private research log: contains short quotes from copyright documents, not for publication.
A flag is a question to check, not a finding. Yellow rows need a person to review them; red rows are reviewed real disagreements.</p>
<h2>Questions for the manager</h2><div>{memo}</div>
<h2>Flags ({len(flags)})</h2><table><tr><th>Id</th><th>Rule</th><th>Field</th><th>Side A</th><th>Side B</th><th>Review</th></tr>{flag_rows}</table>
<h2>Evidence check and scores</h2><ul>{scores}</ul>
<h2>Documents watched</h2><table><tr><th>File</th><th>Last changed</th><th>Last checked</th><th>Checksum</th></tr>{doc_rows}</table>
</body></html>"""


def memo_html(fund):
    path = WORK / "outputs" / fund.lower() / "memo.md"
    if not path.exists():
        return "<p>No memo.</p>"
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("- ") and "[F" in l]
    return "<ul>" + "".join(f"<li>{esc(l[2:])}</li>" for l in lines) + "</ul>" if lines else "<p>None: no real disagreements.</p>"


def metrics(fund, summary, flags):
    data = [("Flags", len(flags)), ("FlagsToReview", int((flags.label == "").sum())),
            ("RealDisagreements", int((flags.label == "real disagreement").sum()))]
    checked = summary.get("check", {})
    total = sum(checked.values())
    if total:
        data.append(("EvidencePassRate", 100 * sum(v for k, v in checked.items() if k.startswith("pass")) / total))
    for name in ("recall_all", "precision"):  # LF1 only: "26/29 = 90%"
        if name in summary:
            hit, n = re.match(r"(\d+)/(\d+)", summary[name]).groups()
            data.append(("Recall" if name == "recall_all" else "Precision", 100 * int(hit) / int(n)))
    # CloudWatch: 10 custom metrics are free, then about US$0.30 each a month. So only 7 are sent: FlagsToReview
    # for each fund, and LF1's accuracy (the only fund with an answer key). The email shows all of them.
    send = {"FlagsToReview"} | ({"Recall", "Precision", "EvidencePassRate"} if fund == "LF1" else set())
    boto3.client("cloudwatch").put_metric_data(Namespace="FundDocs", MetricData=[
        {"MetricName": m, "Dimensions": [{"Name": "Fund", "Value": fund}], "Value": float(v),
         "Unit": "Percent" if m in ("EvidencePassRate", "Recall", "Precision") else "Count"} for m, v in data if m in send])
    return dict(data)


def handler(event, context):
    run_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if WORK.exists():
        shutil.rmtree(WORK)
    shutil.copytree(PACKAGED, WORK)
    sys.path.insert(0, str(WORK / "src"))
    state = json.loads(get("state/versions.json"))

    changed = event.get("changed", {})
    funds = list(dict.fromkeys(list(changed) + event.get("rerun", []) + event.get("funds", [])))
    results, links = {}, {}
    for fund in funds:
        try:
            prepare(fund, changed.get(fund, []), state)
            for script in ("3_extract.py", "4_score.py", "5_compare.py", "6_memo.py"):
                run(script, fund)
            out = WORK / "outputs" / fund.lower()
            summary = json.loads((out / "extract" / "summary.json").read_text(encoding="utf-8"))
            flags = pd.read_csv(out / "flags.csv", dtype=str, encoding="utf-8-sig").fillna("")
            publish(fund)
            page = report_html(fund, state, summary, flags, memo_html(fund), run_date)
            s3.put_object(Bucket=BUCKET, Key=f"reports/{fund.lower()}.html", Body=page.encode(), ContentType="text/html")
            links[fund] = s3.generate_presigned_url("get_object", ExpiresIn=7 * 24 * 3600,
                                                    Params={"Bucket": BUCKET, "Key": f"reports/{fund.lower()}.html"})
            new = flags[flags.label == ""]
            # Reviewed flags that this run no longer raises. Re-reading even an identical document can change one
            # answer (a date, say), and a real disagreement must not disappear silently.
            known_key = f"state/known_flags/{fund.lower()}.json"
            try:
                known = json.loads(get(known_key))
            except s3.exceptions.NoSuchKey:
                known = {}
            raised = set(flags.flag_id)
            dropped = {i: l for i, l in known.items() if i not in raised}
            known.update({r.flag_id: r.label for r in flags.itertuples() if r.label})
            s3.put_object(Bucket=BUCKET, Key=known_key, Body=json.dumps(known, indent=1).encode())
            results[fund] = {"changed_docs": changed.get(fund, []), "metrics": metrics(fund, summary, flags),
                             "new_flags": [f"{r.flag_id} {r.field} {r.sub_field}: {r.a_doc} p{r.a_page} {r.a_value} vs "
                                           f"{r.b_doc} p{r.b_page} {r.b_value}" for r in new.itertuples()],
                             "real_flags_no_longer_raised": sorted(i for i, l in dropped.items() if l == "real disagreement"),
                             "other_reviewed_flags_no_longer_raised": len([l for l in dropped.values() if l != "real disagreement"])}
        except Exception as e:  # one fund failing shouldn't stop the others
            results[fund] = {"error": f"{type(e).__name__}: {e}"}
            print(f"{fund} failed: {e}")

    print(json.dumps(results, indent=1))
    if os.environ.get("EMAIL"):
        lines = [f"Fund document check, {run_date}", ""]
        lines += event.get("log", [])
        lines += [f"Couldn't check: {f}" for f in event.get("failed", [])]
        for fund, r in results.items():
            lines += ["", f"== {fund}"]
            if "error" in r:
                lines.append(f"Run failed: {r['error']}")
                continue
            m = r["metrics"]
            lines.append(f"Flags: {m['Flags']} ({m['FlagsToReview']} need review, {m['RealDisagreements']} real disagreements)")
            if "Recall" in m:
                lines.append(f"Accuracy against the answer key: recall {m['Recall']:.0f}%, precision {m['Precision']:.0f}%")
            lines += [f"  NEW: {f}" for f in r["new_flags"]]
            lines += [f"  CHECK: real disagreement {i} is no longer raised. Did the document change, or did the AI "
                      f"misread it this time? Compare the old and new extraction." for i in r["real_flags_no_longer_raised"]]
            if r["other_reviewed_flags_no_longer_raised"]:
                lines.append(f"  {r['other_reviewed_flags_no_longer_raised']} other reviewed flags are no longer raised "
                             "(not real disagreements; usually fine).")
            if fund in links:
                lines.append(f"Log (link valid 7 days): {links[fund]}")
        n_new = sum(len(r.get("new_flags", [])) for r in results.values())
        subject = f"Fund documents: {', '.join(funds)} updated, {n_new} new flag{'s' if n_new != 1 else ''} to review"
        boto3.client("ses").send_email(Source=os.environ["EMAIL"], Destination={"ToAddresses": [os.environ["EMAIL"]]},
                                       Message={"Subject": {"Data": subject}, "Body": {"Text": {"Data": "\n".join(lines)}}})
    return results
