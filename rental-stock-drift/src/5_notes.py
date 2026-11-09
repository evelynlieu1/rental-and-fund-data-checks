"""Phase 5: AI notes for 3 top-20 postcodes, with a number checker.

The model (Claude Haiku 4.5 on AWS Bedrock, Australian route) sees ONLY that postcode's row
from outputs/top20.csv. Plain Python then pulls every number out of the note and checks it
against the row. A note with any number that isn't in the row is rejected.

Run:  python src/5_notes.py
Needs AWS credentials with Bedrock access (for example, set AWS_PROFILE). Writes outputs/notes/<postcode>.json and outputs/notes/broken_test.json.
"""
import json
import re
import os
from pathlib import Path

import pandas as pd
from anthropic import AnthropicBedrock

PROJECT = Path(__file__).resolve().parents[1]
NOTES_DIR = PROJECT / "outputs" / "notes"

MODEL = "au.anthropic.claude-haiku-4-5-20251001-v1:0"  # Haiku 5.5 isn't enabled on this AWS account yet
POSTCODES = ["2179", "2765", "4306"]  # Leppington, Box Hill (NSW), Ripley (QLD): solid in every variant

ROW_FIELDS = ["state", "postcode", "census_2021", "bonds_2021", "bonds_now", "stock_now", "drift", "multiplier", "base", "now"]
RATIO_FIELDS = ["drift", "multiplier"]  # these may also appear as percentages (0.253 -> 25.3%)

SYSTEM = (
    "You write short notes for a property data analyst. Use only the numbers in the data row you are given. "
    "Do not calculate new numbers, do not add facts about the area, and do not mention years or counts that are not in the row. "
    "You may show drift and multiplier as percentages. Round numbers to whole numbers or one decimal place. "
    "Bonds are COUNTS of tenancies, not money: never use a $ sign. Don't express growth as a multiple such as '2.4x'; use the drift percentage."
)
# Run 1 (8 Nov) without the last sentence: all 3 notes were rejected. The model read bond counts
# as dollars ("$3.4m") and invented per-unit figures ("$1.1k per unit"). See outputs/notes/run1_rejected/.

PROMPT = """Data row for one postcode (bonds held = rental bonds lodged with the state):
{row}

Field meanings:
- census_2021: households renting privately on Census night 2021
- bonds_2021, bonds_now: NUMBER of rental bonds held (one per tenancy) at the base period and now (periods are 'base' and 'now', as YYYY-MM)
- drift: bond growth since the base period (0.5 means +50%)
- stock_now: census_2021 grown by drift, an estimate of today's private rentals
- multiplier: census_2021 / stock_now. A vacancy rate that still divides by the 2021 Census count, times this, gives the rate on today's stock.

Write a note of 3 to 5 sentences: what moved, since when, and what an analyst should check."""


def numbers_in(text):
    """Every number written in the text, e.g. '2,964' -> 2964.0, '64.3%' -> 64.3, '2021-06' -> 2021 and 6."""
    found = []
    for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", text):
        raw = m.group().rstrip(",")
        decimals = len(raw.split(".")[1]) if "." in raw else 0
        found.append((raw, float(raw.replace(",", "")), decimals))
    return found


def allowed_values(row):
    values = []
    for field in ROW_FIELDS:
        v = row[field]
        if field in ("base", "now"):  # "2021-12" -> 2021 and 12
            values += [float(x) for x in str(v).split("-")]
        elif field == "state":
            continue
        else:
            values.append(float(v))
            if field in RATIO_FIELDS:
                values.append(float(v) * 100)
    return values


def check_note(note, row):
    """Return (passed, problems). A number passes if it matches a row value at the precision it's written."""
    allowed = allowed_values(row)
    problems = []
    for raw, x, decimals in numbers_in(note):
        tolerance = 0.5 * 10 ** -decimals + 1e-9
        if not any(abs(x - v) <= tolerance for v in allowed):
            problems.append(f"'{raw}' is not in the data row")
    # Two unit checks found in run 1: a number can be right but used wrongly
    if "$" in note:
        problems.append("uses a $ sign, but the row has no money amounts")
    if re.search(r"\d(?:\.\d+)?\s*x\b", note):
        problems.append("states growth as a multiple ('1.4x'), which isn't in the row")
    return len(problems) == 0, problems


def ask_model(client, row):
    prompt = PROMPT.format(row=json.dumps(row, indent=2))
    response = client.messages.create(model=MODEL, max_tokens=1000, system=SYSTEM,
                                      messages=[{"role": "user", "content": prompt}])
    if response.stop_reason != "end_turn":
        raise RuntimeError(f"Model stopped early: {response.stop_reason}")
    note = "".join(block.text for block in response.content if block.type == "text").strip()
    return prompt, note, response


def main():
    top = pd.read_csv(PROJECT / "outputs" / "top20.csv", dtype={"postcode": str})
    # Locally, use the AWS profile in AWS_PROFILE; inside Lambda the function's role gives access
    profile = None if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") else os.environ.get("AWS_PROFILE")
    client = AnthropicBedrock(aws_region="ap-southeast-2", aws_profile=profile)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    first = None
    for pc in POSTCODES:
        row = top[top["postcode"] == pc].iloc[0][ROW_FIELDS].to_dict()
        row = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}
        prompt, note, response = ask_model(client, row)
        passed, problems = check_note(note, row)
        record = {"postcode": pc, "model": MODEL, "system": SYSTEM, "prompt": prompt, "raw_reply": note,
                  "checker_passed": passed, "checker_problems": problems,
                  "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}}
        (NOTES_DIR / f"{pc}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"--- {pc}: {'PASS' if passed else 'REJECTED ' + str(problems)}\n{note}\n")
        first = first or (row, note)

    # Deliberately broken note: change the first number from the row by hand. The checker must reject it.
    row, note = first
    real = f"{int(row['bonds_now']):,}"
    broken = note.replace(real, f"{int(row['bonds_now']) + 500:,}") if real in note else note + f" Bonds reached 9,999."
    passed, problems = check_note(broken, row)
    (NOTES_DIR / "broken_test.json").write_text(json.dumps(
        {"postcode": row["postcode"], "broken_note": broken, "checker_passed": passed, "checker_problems": problems},
        indent=2), encoding="utf-8")
    print(f"--- Broken-note test: {'FAILED, checker let it through' if passed else 'rejected as expected'} {problems}")


if __name__ == "__main__":
    main()
