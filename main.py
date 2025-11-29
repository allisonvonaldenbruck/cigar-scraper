#!/usr/bin/env python3

import os
from pathlib import Path

import sqlalchemy as sqa
import pandas as pd  # noqa: F401  # used in imported modules

from src.scraper import *
from src.cleaner import *
from src.queries import *
from src.matcher import *
from src.log import log

DEBUG = False
PROXY = False

DB_NAME = "cigarData"
DEBUG_DB_NAME = "cigarDataDebug"

# Base directory of the repo (directory where main.py lives)
BASE_DIR = Path(__file__).resolve().parent

# Allow overriding the DB login file via environment variable,
# otherwise default to "secrets/db_login_file" in the repo.
DB_LOGIN_FILE = os.getenv(
    "DB_LOGIN_FILE",
    str(BASE_DIR / "secrets" / "db_login_file")
)

# If this is "1", we use a local SQLite database instead of MySQL.
USE_SQLITE = os.getenv("USE_SQLITE", "0") == "1"


def is_yes(buf: str) -> bool:
    return buf.lower() in ["y", "yes"]


def main() -> None:
    log("a", "---------- New Run ----------")

    db_name = DB_NAME if not DEBUG else DEBUG_DB_NAME

    if USE_SQLITE:
        # Use a sqlite file in the repo folder when running in CI
        db_path = BASE_DIR / f"{db_name}.sqlite"
        log("i", f"Using SQLite database at {db_path}")
        engine = sqa.create_engine(f"sqlite:///{db_path}")
    else:
        # Original behavior: use credentials file to connect to MySQL
        if not os.path.exists(DB_LOGIN_FILE):
            raise FileNotFoundError(
                f"Database login file not found at: {DB_LOGIN_FILE}\n"
                " - On GitHub Actions, either set USE_SQLITE=1, or make sure "
                "   the 'Write database credentials' step ran.\n"
                " - Locally, create 'secrets/db_login_file' next to main.py, "
                "   or set the DB_LOGIN_FILE environment variable."
            )
        engine = create_db(db_name, DB_LOGIN_FILE)

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
        scrape_data_combine(engine, DEBUG, proxy=PROXY)
        clean_data(engine)
        match_skus(engine)


if __name__ == "__main__":
    main()
