#!/usr/bin/env python3
"""Create a deliberately messy folder of dummy files for demoing organize_files.py.

Usage:
    python make_messy_folder.py                 # creates ./messy_folder/
    python make_messy_folder.py --outdir demo

Every file is a tiny placeholder with invented names. Modified dates are spread across
several months so --by date has something to sort. Includes odd extensions, an uppercase
extension, a hidden file, and two files named report.pdf (one in a subfolder) to show
collision handling with --recursive. Safe for screenshots and public repos.
"""
import argparse
import os
from datetime import datetime
from pathlib import Path

# (relative path, modified date)
FILES = [
    ("invoice_march.pdf",        "2026-03-14"),
    ("invoice_april.pdf",        "2026-04-02"),
    ("IMG_2041.jpg",             "2026-03-20"),
    ("IMG_2042.JPG",             "2026-03-21"),
    ("vacation_photo.png",       "2026-06-09"),
    ("budget.xlsx",              "2026-02-11"),
    ("sales_export.csv",         "2026-05-30"),
    ("backup.zip",               "2026-01-25"),
    ("notes.txt",                "2026-04-18"),
    ("meeting_notes.docx",       "2026-05-05"),
    ("clip.mp4",                 "2026-06-15"),
    ("podcast_episode.mp3",      "2026-02-27"),
    ("quarterly_slides.pptx",    "2026-03-03"),
    ("cleanup_script.py",        "2026-05-12"),
    ("mystery_file.xyz",         "2026-04-22"),
    ("data.dat",                 "2026-01-08"),
    ("2026-03-01_receipt.pdf",   "2026-03-01"),   # already date-prefixed (rename should skip it)
    ("report.pdf",               "2026-05-20"),
    ("old/report.pdf",           "2026-02-02"),   # same name as above -> collision with --recursive
    ("old/draft_letter.docx",    "2026-01-14"),
    (".DS_Store",                "2026-06-01"),   # hidden, should be ignored
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, default=Path("messy_folder"))
    args = ap.parse_args()

    for rel, day in FILES:
        path = args.outdir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"placeholder for {path.name}\n")
        ts = datetime.strptime(day, "%Y-%m-%d").replace(hour=12).timestamp()
        os.utime(path, (ts, ts))
    print(f"Created {len(FILES)} dummy files in {args.outdir}/")


if __name__ == "__main__":
    main()
