"""Phase 7: draft the questions-for-the-manager memo with Claude, then check every line with code.

Only flags labelled "real disagreement" in outputs/<fund>/flags.csv go to the model, with their evidence.
The check rejects any question that:
  - doesn't cite a flag id, or cites one that isn't a real-disagreement flag
  - contains a number that isn't in the evidence of the flag(s) it cites (same idea as project 1's number checker)

Run:  python src/6_memo.py LF1      (or MXT, MA1, REV)
Needs AWS credentials with Bedrock access (for example, set AWS_PROFILE). Writes outputs/<fund>/memo.md and outputs/<fund>/memo_check.json.
"""
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd
from anthropic import AnthropicBedrock

PROJECT = Path(__file__).resolve().parents[1]
MODEL = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
FUND_NAMES = {"LF1": "La Trobe Private Credit Fund", "MXT": "Metrics Master Income Trust",
              "MA1": "MA Credit Income Trust", "REV": "Revolution Private Credit Income Trust"}

SYSTEM = ("You help a fund research analyst prepare for a meeting with a fund manager. You write polite, specific "
          "questions, never accusations. You use only the evidence given. Plain punctuation: full stops and "
          "commas, no dashes or ellipses.")

PROMPT = """Below are the places where {code}'s ({name}) own documents disagree with each other,
each with a flag id and the evidence on both sides (document, page, value, date, short quote).

{flags}

Write up to 5 questions for the manager, most important first. Rules:
- One question per line, starting with "- ", and ending with the flag id(s) it is about in square brackets, e.g. [F123abc].
- Every question must be about one of the flags above. If there are fewer real issues than 5, write fewer questions.
- Quote numbers exactly as they appear in the evidence; don't calculate new ones.
- Assume there may be a good explanation (a rounding difference, a different basis, an out-of-date page): ask which
  figure or statement is right and why they differ.
Reply with the question lines only."""


def numbers(s):
    return [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", str(s))]


def check_line(line, real):
    ids = re.findall(r"\[(F[0-9a-f]{6})\]", line)
    if not ids:
        return "no flag id"
    bad = [i for i in ids if i not in real]
    if bad:
        return f"not a real-disagreement flag: {', '.join(bad)}"
    allowed = []
    for i in ids:
        allowed += numbers(" ".join(map(str, real[i].values())))
    body = re.sub(r"\[F[0-9a-f]{6}\]", "", line)
    stray = [x for x in numbers(body) if not any(abs(x - a) < 1e-9 for a in allowed)]
    return f"number not in the evidence: {stray}" if stray else "pass"


def main():
    fund = sys.argv[1].upper() if len(sys.argv) > 1 else "LF1"
    OUT = PROJECT / "outputs" / fund.lower()
    flags = pd.read_csv(OUT / "flags.csv", dtype=str, encoding="utf-8-sig").fillna("")
    real_df = flags[flags.label == "real disagreement"]
    if real_df.empty:
        (OUT / "memo.md").write_text(f"# Questions for the manager: {fund}\n\nNo flag was labelled \"real disagreement\", "
                                     "so there is nothing to ask.\n", encoding="utf-8")
        print(f"{fund}: no real disagreements, memo says so")
        return
    cols = ["field", "sub_field", "a_doc", "a_page", "a_value", "a_as_at", "a_quote",
            "b_doc", "b_page", "b_value", "b_as_at", "b_quote"]
    real = {r.flag_id: {c: getattr(r, c) for c in cols} for r in real_df.itertuples()}
    flag_text = "\n\n".join(
        f"[{fid}] field {e['field']} {e['sub_field']}\n"
        f"  A: {e['a_doc']} page {e['a_page']}, value {e['a_value']}, date {e['a_as_at'] or 'not stated'}: \"{e['a_quote']}\"\n"
        f"  B: {e['b_doc']} page {e['b_page']}, value {e['b_value']}, date {e['b_as_at'] or 'not stated'}: \"{e['b_quote']}\""
        for fid, e in real.items())

    profile = None if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") else os.environ.get("AWS_PROFILE")
    client = AnthropicBedrock(aws_region="ap-southeast-2", aws_profile=profile)
    msg = client.messages.create(model=MODEL, max_tokens=1500, temperature=0, system=SYSTEM,
                                 messages=[{"role": "user", "content": PROMPT.format(
                                     code=fund, name=FUND_NAMES[fund], flags=flag_text)}])
    reply = msg.content[0].text

    lines = [l.strip() for l in reply.splitlines() if l.strip().startswith("-")]
    results = [{"line": l, "check": check_line(l, real)} for l in lines]
    # Prove the check works: one planted line with a made-up number, one with a fake flag id
    planted = [f"- Why does one report show 41.5% for this figure? [{next(iter(real))}]",
               "- Can you confirm the buy-back cap? [F000000]"]
    planted_results = [{"line": l, "check": check_line(l, real)} for l in planted]

    passed = [r["line"] for r in results if r["check"] == "pass"]
    memo = [f"# Questions for the manager: {fund} (draft)", "",
            f"Drafted by {MODEL} from the {len(real)} flags labelled \"real disagreement\" in outputs/{fund.lower()}/flags.csv, "
            "then checked by code: every question cites a real flag, and every number in it is in that flag's evidence.",
            "", *passed, "", "## The evidence behind each flag", ""]
    for fid, e in real.items():
        memo += [f"**{fid}** ({e['field']} {e['sub_field']})".replace(" )", ")"),
                 f"- {e['a_doc']} p{e['a_page']}: {e['a_value']} ({e['a_as_at'] or 'undated'}), \"{e['a_quote']}\"",
                 f"- {e['b_doc']} p{e['b_page']}: {e['b_value']} ({e['b_as_at'] or 'undated'}), \"{e['b_quote']}\"", ""]
    (OUT / "memo.md").write_text("\n".join(memo), encoding="utf-8")
    (OUT / "memo_check.json").write_text(json.dumps({"model": MODEL, "flags_sent": list(real), "raw_reply": reply,
                                                     "results": results, "planted": planted_results}, indent=1),
                                         encoding="utf-8")
    for r in results + planted_results:
        print(f"{r['check']:45} {r['line']}")


if __name__ == "__main__":
    main()
