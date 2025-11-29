#!/usr/bin/python3

import sqlalchemy as sqa
import pandas as pd

from src.scraper import *
from src.cleaner import *
from src.queries import *
from src.matcher import *
from src.log import log

DEBUG = False
PROXY = False

DB_NAME = 'cigarData'
DEBUG_DB_NAME = 'cigarDataDebug'

DB_LOGIN_FILE = 'secrets/db_login_file'

def is_yes(buf):
    return buf.lower() in ['y', 'yes']

def main():

    log('a', '---------- New Run ----------')
    #engine = sqa.create_engine('sqlite:///'+DB_NAME)
    db_name = DB_NAME if not DEBUG else DEBUG_DB_NAME
    engine = create_db(db_name, DB_LOGIN_FILE)
    
    # this will eventually be set via cmd line arg
    interactive = False 
    if interactive:
        buf = input('Scrape data (y/N)? ')
        if is_yes(buf):
            scrape_data_combine(engine, DEBUG, proxy=PROXY)
            
        buf = input('Clean data (y/N)? ')
        if is_yes(buf):
            clean_data(engine)
        
        buf = input('Match data (y/N)? ')
        if is_yes(buf):
            match_skus(engine)
    else:
        scrape_data_combine(engine, DEBUG, proxy=PROXY)
        clean_data(engine)
        match_skus(engine)
        
if __name__ == '__main__':
    main()