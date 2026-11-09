"""Download the project's data files listed in data/MANIFEST.csv and check them.

Run from anywhere:  python src/1_fetch.py
It skips files that are already there with the right checksum.
"""
import csv
import hashlib
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"

# Quick version: only these files. Add more prefixes later if you need them.
WANTED = (
    "raw/abs_census/2021_",
    "raw/nsw_bonds_held/",
    "raw/qld_rta/",
    "raw/vic_rental_report/tables_rental_report",  # phase 6: Rockbank through the City of Melton
)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with open(DATA / "MANIFEST.csv", newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["file"].startswith(WANTED)]

    for r in rows:
        path = DATA / r["file"]
        if path.exists() and sha256(path) == r["sha256"]:
            print(f"ok (already here)  {r['file']}")
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(r["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            path.write_bytes(resp.read())

        status = "ok" if sha256(path) == r["sha256"] else "CHECKSUM DIFFERS (file changed upstream?)"
        print(f"{status:18} {r['file']}")


if __name__ == "__main__":
    main()
