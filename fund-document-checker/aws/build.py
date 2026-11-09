"""Build the two Lambda upload packages: build/watch.zip and build/pipeline.zip.

Run from the project folder:  python aws/build.py

Two packages because one won't fit: PyMuPDF (to read PDFs) plus pandas would pass Lambda's 250 MB limit.
- watch.zip: PyMuPDF and the watcher. Reads new PDFs into page text.
- pipeline.zip: the anthropic library and the pipeline. pandas, numpy, pyarrow and openpyxl come from AWS's
  AWSSDKPandas layer, as in project 1.
Both carry the project files they need under project/. No fund documents go in either package.
"""
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
BUILD = PROJECT / "build"


def pip(target, *packages):
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet",
                    "--platform", "manylinux2014_x86_64", "--only-binary=:all:",
                    "--python-version", "3.13", "--implementation", "cp",
                    "--target", str(target), *packages], check=True)


def project_files(target, with_gold):
    shutil.copytree(PROJECT / "src", target / "project" / "src", ignore=shutil.ignore_patterns("__pycache__"))
    (target / "project" / "data").mkdir()
    shutil.copy(PROJECT / "data" / "MANIFEST.csv", target / "project" / "data")
    if with_gold:
        shutil.copytree(PROJECT / "gold", target / "project" / "gold", ignore=shutil.ignore_patterns("*worksheet*"))
        shutil.copy(PROJECT / "flag_labels.csv", target / "project")


def zip_up(name, package):
    zip_path = shutil.make_archive(str(BUILD / name), "zip", package)  # Python's zip: Linux-safe paths
    size_mb = Path(zip_path).stat().st_size / 1e6
    print(f"Built {zip_path} ({size_mb:.1f} MB){'' if size_mb < 50 else '  TOO BIG for direct upload'}")


shutil.rmtree(BUILD, ignore_errors=True)

watch = BUILD / "watch"
watch.mkdir(parents=True)
pip(watch, "pymupdf")
shutil.copy(PROJECT / "aws" / "watch.py", watch)
project_files(watch, with_gold=False)
zip_up("watch", watch)

pipeline = BUILD / "pipeline"
pipeline.mkdir(parents=True)
pip(pipeline, "anthropic==0.97.0")  # the version the scripts were written and tested with; newer ones drop temperature
shutil.copy(PROJECT / "aws" / "pipeline.py", pipeline)
project_files(pipeline, with_gold=True)
zip_up("pipeline", pipeline)
