"""Create a transactionally consistent SQLite backup, including WAL contents."""
import argparse
from pathlib import Path
import sqlite3
import os
from src.data import ROOT

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    source=Path(os.environ.get("SONGMATCH_DB_PATH",ROOT/"data/feedback.db"))
    if not source.is_file():
        raise SystemExit("No study database exists yet.")
    if source.resolve()==args.output.resolve():
        raise SystemExit("Backup path must differ from the live database.")
    if args.output.exists():
        raise SystemExit("Choose a new backup filename; existing files are not overwritten.")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(source) as live,sqlite3.connect(args.output) as backup:
        live.backup(backup)
    print(f"Backup saved to {args.output}")

if __name__=="__main__":
    main()
