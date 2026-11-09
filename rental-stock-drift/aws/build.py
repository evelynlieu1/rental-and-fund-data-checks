"""Build the Lambda upload package: build/function.zip.

Run from the project folder:  python aws/build.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
BUILD = PROJECT / "build"
PACKAGE = BUILD / "package"

# 1. Start clean
shutil.rmtree(BUILD, ignore_errors=True)
PACKAGE.mkdir(parents=True)

# 2. The Linux version of the anthropic library (pandas, numpy and openpyxl come from the AWS layer)
subprocess.run([sys.executable, "-m", "pip", "install", "--quiet",
                "--platform", "manylinux2014_x86_64", "--only-binary=:all:",
                "--python-version", "3.13", "--implementation", "cp",
                "--target", str(PACKAGE), "anthropic"], check=True)

# 3. The handler at the top level, and the project files it needs under project/
shutil.copy(PROJECT / "aws" / "lambda_function.py", PACKAGE)
shutil.copytree(PROJECT / "src", PACKAGE / "project" / "src", ignore=shutil.ignore_patterns("__pycache__"))
shutil.copy(PROJECT / "unmatched_notes.csv", PACKAGE / "project")
(PACKAGE / "project" / "data").mkdir()
shutil.copy(PROJECT / "data" / "MANIFEST.csv", PACKAGE / "project" / "data")

# 4. Zip it with Python (Windows' own zip can write paths Linux can't read)
zip_path = shutil.make_archive(str(BUILD / "function"), "zip", PACKAGE)
size_mb = Path(zip_path).stat().st_size / 1e6
print(f"Built {zip_path} ({size_mb:.1f} MB)")
print("OK: under the 50 MB upload limit" if size_mb < 50 else "TOO BIG: check what went into build/package")
