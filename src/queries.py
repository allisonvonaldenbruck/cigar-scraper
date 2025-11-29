from sqlalchemy import Table, Column, Integer, String, Float, Boolean, Date
import sqlalchemy as sqa
import sqlalchemy_utils as sqaUtil
import pandas as pd
import sqlite3

from src.log import *

def get_db_credentials(db_login_file):
    """takes a file and pulls the db credentials from it. Dose not error checking. Data should take the following form:
    
    host:hostname \\
    pass:password \\
    user:username

    Order dose not matter.

    Args:
        db_login_file (str): credential file name

    Returns:
        (str, str, str): (username, password, host, port) for db. A val will be '' if no present in file.
    """

    with open(db_login_file, 'r') as fp:
        user = ''
        pas = ''
        host = ''
        port = ''
        for line in fp:
            line = line.split(':')
            if line[0] == 'host':
                host = line[1].strip()
            if line[0] == 'pass':
                pas = line[1].strip()
            if line[0] == 'user':
                user = line[1].strip()
            if line[0] == 'port':
                port = line[1].strip()
    return (user, pas, host, port)

def create_db(db_name, db_login_file):
    """create db, including tables that don't already exist. Also deletes tabes that need to be built form scratch.

    Args:
        db_name (str): db name
        db_login_file (str): file containing login info for db

    Returns:
        sqlalchemy.engine: engine needed for pandas to write to db
    """

    (user, pas, host, port) = get_db_credentials(db_login_file)

    if not port:
        engine_name = f'mysql+pymysql://{user}:{pas}@{host}/{db_name}'
    else:
        engine_name = f'mysql+pymysql://{user}:{pas}@{host}:{port}/{db_name}'
    engine = sqa.create_engine(engine_name)

    if not sqaUtil.database_exists(engine.url):
        sqaUtil.create_database(engine.url)


    log('a', '---------- Creating Database ----------')
    
    inspector = sqa.inspect(engine)
    tables = inspector.get_table_names()
    
    # TODO: Tables to create:
    tb_name = 'review_data'
    
    tb_name = 'international_data'
    if tb_name in tables:
        meta = sqa.MetaData()
        table = sqa.Table(tb_name, meta)
        table.drop(engine, True)
    meta = sqa.MetaData()
    inter_table = Table(tb_name, meta,
                  Column('sku', String(256), primary_key=True),
                  Column('title', String(256)),
                  Column('shape', String(256)),
                  Column('size', String(256), nullable=False),
                  Column('name', String(256)),
                  Column('qty', String(256), nullable=False),
                  Column('price', Float, nullable=False),
                  Column('msrp', Float),
                  Column('url', String(128), nullable=False),
                  Column('brand', String(256), nullable=False),
                  Column('brand_idx', Integer, nullable=False),
                  Column('timestamp', Date, nullable=False),
                  )
    meta.create_all(engine)
    
    tb_name = 'international_data_clean'
    if tb_name not in tables:
        meta = sqa.MetaData()
        Table(tb_name, meta,
                  Column('sku', String(256), primary_key=True),
                  Column('title', String(256)),
                  Column('shape', String(256)),
                  Column('size', String(256), nullable=False),
                  Column('name', String(256)),
                  Column('qty', Integer, nullable=False),
                  Column('price', Float, nullable=False),
                  Column('msrp', Float),
                  Column('url', String(128), nullable=False),
                  Column('brand', String(256), nullable=False),
                  Column('brand_idx', Integer, nullable=False),
                  Column('timestamp', Date, nullable=False),
                  )
        meta.create_all(engine)
    
    tb_name = 'smoke_inn_data'
    if tb_name in tables:
        meta = sqa.MetaData()
        table = sqa.Table(tb_name, meta)
        table.drop(engine, True)
    meta = sqa.MetaData()
    smoke_table = Table(tb_name, meta,
                  Column('sku', String(256), primary_key=True),
                  Column('title', String(256)),
                  Column('size', String(256), nullable=False),
                  Column('qty', String(256), nullable=False),
                  Column('price', Float, nullable=False),
                  Column('msrp', Float),
                  Column('url', String(128), nullable=False),
                  Column('brand', String(256), nullable=False),
                  Column('brand_idx', Integer, nullable=False),
                  Column('timestamp', Date, nullable=False),
                  )
    meta.create_all(engine)
        
    tb_name = 'smoke_inn_data_clean'
    if tb_name not in tables:
        meta = sqa.MetaData()
        Table(tb_name, meta,
                  Column('sku', String(256), primary_key=True),
                  Column('title', String(256)),
                  Column('size', String(256), nullable=False),
                  Column('qty', Integer, nullable=False),
                  Column('price', Float, nullable=False),
                  Column('msrp', Float),
                  Column('url', String(128), nullable=False),
                  Column('brand', String(256), nullable=False),
                  Column('brand_idx', Integer, nullable=False),
                  Column('timestamp', Date, nullable=False),
                  )
        meta.create_all(engine)
     
    
    tb_name = 'price_data'
    if tb_name not in tables:
        meta = sqa.MetaData()
        Table(tb_name, meta,
                      Column('sku', String(256)),
                      Column('site', String(256)),
                      Column('timestamp', Date),
                      Column('price', Float),
                      Column('msrp', Float),
                      Column('sale', Boolean),
                      sqa.UniqueConstraint('sku', 'timestamp')
                      )
        meta.create_all(engine)
        
    tb_name = 'equivalent_skus'
    if tb_name not in tables:
        metadata = sqa.MetaData()
        Table(tb_name, metadata,
              Column('index',               Integer, primary_key=True, autoincrement=True),
              Column('smoke_sku',           String(256)), #sqa.ForeignKey(smoke_table.c.sku)),
              Column('inter_sku',           String(256)), #sqa.ForeignKey(inter_table.c.sku)),
              Column('conf',                Integer),
              sqa.UniqueConstraint('smoke_sku', 'inter_sku'),
              )
        metadata.create_all(engine)
        
    return engine
    
            
def write_to_db(table, name, engine, check_insert=True, index=False, if_exists='append'):
    """Write pandas table to db, check if row exists before writing. Only works on data constrained as unique in db proper.

    Args:
        table (pandasTable): data to write
        name (str): name of table
        engine (sqlalchemyEngine): engine handling db reads/writes
        checkInsert (bool, optional): check data before inserting it. Defaults to True
        index (bool, optional): write data index to table. Defaults to False.
        if_exists (str, optional): what to do if table already exists, options are 'append' and 'replace'. Defaults to 'append'.
    """
    if check_insert:
        # TODO: may need to insert one row at a time to catch errors and not miss new rows mixed with old data
        try:
            table.to_sql(name, engine, index=index, if_exists=if_exists)
            log('a', f'wrote {len(table.index)} new rows of table {name} to db')
        except sqa.exc.IntegrityError as e:
            log('w', f'integrity error writing to db, this may just be duplicate data')
    else:
        log('a', f'wrote {len(table.index)} rows in table {name} to db')
        table.to_sql(name, engine, index=index, if_exists=if_exists)
