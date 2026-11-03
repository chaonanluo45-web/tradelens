"""Create a clean submission zip with the repository root preserved."""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "TradeLens_submission.zip"
EXCLUDE_DIRS = {".deps", ".browsers", "__pycache__", ".git", ".venv", "venv"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".log"}

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDE_DIRS for part in relative.parts):
            continue
        if path.suffix.lower() in EXCLUDE_SUFFIXES:
            continue
        archive.write(path, Path("tradelens") / relative)

size = OUT.stat().st_size
print(f"created {OUT} ({size / 1024 / 1024:.2f} MB)")
