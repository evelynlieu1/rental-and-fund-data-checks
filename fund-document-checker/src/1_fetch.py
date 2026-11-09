"""Phase 1: download the quick-version files listed in data/MANIFEST.csv and check them.

Run:  python src/1_fetch.py
Skips files already here with the right checksum. A file whose checksum differs is kept
(three LF1 files sit at "latest" URLs that change) and listed so it can go in VERSIONS.md.

These files are third-party documents: research use only, never commit or publish them.
They are in data/NOSYNC.txt, so scripts/data_sync.py never uploads them.
"""
import csv
import hashlib
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"

# LF1 (quick version) plus the other three funds (added 8 Nov), the September ASX report,
# the ASIC register and REP 814
WANTED = (
    "raw/lf1/",
    "raw/mxt/",
    "raw/ma1/",
    "raw/rev/",
    "raw/asx/asx-investment-products-sep-2026",
    "raw/asic/afs_lic_202610.csv",
    "raw/asic/asic_rep814_",
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

    changed = []
    for r in rows:
        path = DATA / r["file"]
        if path.exists() and sha256(path) == r["sha256"]:
            print(f"ok (already here)  {r['file']}")
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(r["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            path.write_bytes(resp.read())

        if sha256(path) == r["sha256"]:
            print(f"ok                 {r['file']}")
        else:
            changed.append(r["file"])
            print(f"CHECKSUM DIFFERS   {r['file']}  (new version at the source? record it in VERSIONS.md)")

    print(f"\n{len(rows)} files, {len(changed)} changed since the manifest")


if __name__ == "__main__":
    main()
