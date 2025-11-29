#!/usr/bin/env python3

import os
from pathlib import Path

import sqlalchemy as sqa  # kept in case it's used inside src.*
import pandas as pd

from src.scraper import *
from src.cleaner import *
from src.queries import *
from src.matcher import *
from src.log import log
from sqlalchemy import text

DEBUG = False
PROXY = False

DB_NAME = "cigarData"
DEBUG_DB_NAME = "cigarDataDebug"

# This is the same file the original project used
DB_LOGIN_FILE = "secrets/db_login_file"


def is_yes(buf: str) -> bool:
    return buf.lower() in ["y", "yes"]


def export_to_csv(engine) -> None:
    """
    Export key tables from the database to CSV files in the ./output folder.
    If a table doesn't exist, it logs and continues instead of crashing.
    """
    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)

    with engine.connect() as conn:
        # Helper to avoid repeating try/except
        def dump_table(table_name: str, filename: str) -> None:
            try:
                df = pd.read_sql(text(f"SELECT * FROM {table_name}"), conn)
                csv_path = output_dir / filename
                df.to_csv(csv_path, index=False)
                log("i", f"Exported {table_name} to {csv_path}")
            except Exception as e:
                log("e", f"Could not export table '{table_name}': {e}")

        # Adjust these table names to whatever actually exists in your DB
        dump_table("international_data", "international_data.csv")
        dump_table("smokeinn_data", "smokeinn_data.csv")
        dump_table("matched_data", "matched_data.csv")


def main() -> None:
    log("a", "---------- New Run ----------")

    # Choose which DB name to use
    db_name = DB_NAME if not DEBUG else DEBUG_DB_NAME

    # Connect using the original helper from src.queries
    if not os.path.exists(DB_LOGIN_FILE):
        raise FileNotFoundError(
            f"Database login file not found at: {DB_LOGIN_FILE}\n"
            "Create this file locally (or have your workflow write it) "
            "with the correct credentials."
        )

    engine = create_db(db_name, DB_LOGIN_FILE)

    # This was already in your original code
    interactive = False
    if interactive:
        buf = input("Scrape data (y/N)? ")
        if is_yes(buf):
            scrape_data_combine(engine, DEBUG, proxy=PROXY)

        buf = input("Clean data (y/N)? ")
        if is_yes(buf):
            clean_data(engine)

        buf = input("Match data (y/N)? ")
        if is_yes(buf):
            match_skus(engine)
    else:
        # Non-interactive: run everything
        scrape_data_combine(engine, DEBUG, proxy=PROXY)
        clean_data(engine)
        match_skus(engine)

    # NEW: always try to export to CSV at the end
    export_to_csv(engine)


if __name__ == "__main__":
    main()
