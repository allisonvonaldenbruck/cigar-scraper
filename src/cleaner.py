import re
import sqlalchemy as sqa
import pandas as pd

from src.log import *

def clean_size(string):
    if not string:
        return string
    t = re.match('\d\.{0,1}\d{0,3}x\d{2}', string)
    if t:
        s = t.group()
        if '.0x' in s:
            return s.replace('.0', '', 1)
        return s
    return None

def string_match_helper(string, sub):
    for word in sub.split():
        if word not in string:
            return False
    return True

def remove_non_digits(word):
    return re.sub("[^0-9]", "", word)

def clean_data(engine):
    log('a', '---------- Cleaning Data ----------')
    idf = pd.read_sql('''
                      SELECT *
                      FROM international_data
                      ''', con=engine)
    sdf = pd.read_sql('''
                      SELECT *
                      FROM smoke_inn_data
                      ''', con=engine)
    
    
    shapes = idf['shape'].to_list()
    for i, shape in enumerate(shapes):
        if shape:
            shapes[i] = shape.strip('()')
    idf['shape'] = shapes
    
    idf['size'] = idf['size'].str.strip('()')
    idf['size'] = idf['size'].str.replace('"', '')
    idf['size'] = idf['size'].map(clean_size)
    
    qty_list = idf['qty'].to_list()
    for i, qty in enumerate(qty_list):
        line = qty.split()
        qty = 1
        for v in line:
            if v.isnumeric():
                qty *= int(v)
        qty_list[i] = qty
    idf['qty'] = qty_list
    
    sdf['qty'].str = sdf['qty'].str.replace(' ', '')
    
    sdf['qty'] = sdf['qty'].str.replace('n/a', '0')
    sdf['qty'] = sdf['qty'].map(remove_non_digits, na_action='ignore')
    sdf['qty'] = sdf['qty'].map(int, na_action='ignore')
    
    sdf['title'] = sdf['title'].str.replace(' - 5 Pack', '')
    
    idf.to_sql('international_data_clean', engine, index=False, if_exists='replace')
    sdf.to_sql('smoke_inn_data_clean', engine, index=False, if_exists='replace')
