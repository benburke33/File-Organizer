#!/usr/bin/env python3
"""Sort (and optionally rename) the files in a folder. Standard library only.

Usage:
    python organize_files.py ~/Downloads --by type               # preview only
    python organize_files.py ~/Scans --by date --apply
    python organize_files.py ~/Photos --by date --format "%Y/%m" --rename --apply
    python organize_files.py ~/Invoices --by type --recursive --apply
    python organize_files.py ~/Scans --undo organize_log.csv --apply

Modes (--by):
    type   -> Images/, Documents/, Spreadsheets/, Archives/, ...
    date   -> subfolders from each file's modified date (default "%Y-%m")
Options:
    --rename     prefix each file with its date: 2026-11-09_name.ext
    --recursive  also include files in subfolders
    --apply      actually move files (default is a dry-run preview)
Every applied run writes organize_log.csv so it can be reversed with --undo.
Name collisions are never overwritten; a numeric suffix is added instead.
"""
import argparse
import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".heic", ".raw", ".cr2", ".nef"},
    "Videos": {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".webm"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md", ".pages"},
    "Spreadsheets": {".xls", ".xlsx", ".xlsm", ".csv", ".ods", ".numbers"},
    "Presentations": {".ppt", ".pptx", ".key", ".odp"},
    "Archives": {".zip", ".tar", ".gz", ".7z", ".rar", ".bz2"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".sh", ".java", ".c", ".cpp"},
}
EXT_TO_CAT = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}
LOG_NAME = "organize_log.csv"


def category(path: Path) -> str:
    return EXT_TO_CAT.get(path.suffix.lower(), "Other")


def unique_target(target: Path) -> Path:
    if not target.exists():
        return target
    n = 1
    while True:
        candidate = target.with_name(f"{target.stem}_{n}{target.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def list_files(root: Path, recursive: bool):
    it = root.rglob("*") if recursive else root.iterdir()
    for p in it:
        if p.is_file() and not p.name.startswith(".") and p.name != LOG_NAME:
            yield p


def plan(root: Path, args):
    moves, reserved = [], set()
    for f in sorted(list_files(root, args.recursive)):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        sub = category(f) if args.by == "type" else mtime.strftime(args.format)
        name = f.name
        if args.rename and not name[:10].replace("-", "").isdigit():
            name = f"{mtime:%Y-%m-%d}_{name}"
        dest = root / sub / name
        if dest == f:
            continue
        # avoid collisions with existing files and with other planned moves
        candidate, n = dest, 1
        while candidate.exists() or candidate in reserved:
            candidate = dest.with_name(f"{dest.stem}_{n}{dest.suffix}")
            n += 1
        reserved.add(candidate)
        moves.append((f, candidate))
    return moves


def apply_moves(moves, root: Path):
    log = root / LOG_NAME
    with open(log, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["original", "moved_to"])
        for src, dst in moves:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            w.writerow([src, dst])
    return log


def undo(log: Path, apply: bool):
    with open(log, newline="") as fh:
        rows = list(csv.DictReader(fh))
    for row in reversed(rows):
        src, dst = Path(row["original"]), Path(row["moved_to"])
        if not dst.exists():
            print(f"  missing, skipped: {dst}")
            continue
        print(f"  {dst}  ->  {src}")
        if apply:
            src.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst), str(unique_target(src)))
            try:
                dst.parent.rmdir()  # remove the folder if it is now empty
            except OSError:
                pass
    if not apply:
        print("\nDry run. Add --apply to restore these files.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--by", choices=["type", "date"], default="type")
    ap.add_argument("--format", default="%Y-%m", help="strftime pattern for --by date folders")
    ap.add_argument("--rename", action="store_true", help="prefix filenames with their date")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--apply", action="store_true", help="actually move files")
    ap.add_argument("--undo", type=Path, metavar="LOG", help="reverse a previous run using its log")
    args = ap.parse_args()

    if not args.folder.is_dir():
        sys.exit(f"Not a folder: {args.folder}")
    if args.undo:
        undo(args.undo, args.apply)
        return

    moves = plan(args.folder, args)
    if not moves:
        print("Nothing to do.")
        return
    for src, dst in moves:
        print(f"{src.relative_to(args.folder)}  ->  {dst.relative_to(args.folder)}")
    print(f"\n{len(moves)} file(s).")
    if args.apply:
        log = apply_moves(moves, args.folder)
        print(f"Done. Undo log: {log}")
    else:
        print("Dry run only. Re-run with --apply to move them.")


if __name__ == "__main__":
    main()