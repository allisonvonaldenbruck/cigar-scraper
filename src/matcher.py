import pandas as pd

from src.log import *
from src.queries import write_to_db

def check_inter_sku(lst, sku):
    for _, i in lst:
        if sku == i:
            return True
    return False

def check_smoke_sku(lst, sku):
    for s, _ in lst:
        if sku == s:
            return True 
    return False
  
def match_skus(engine):
    log('a', '---------- Matching Data ----------')
    smoke_df = pd.read_sql('''
                      SELECT *
                      FROM smoke_inn_data_clean
                      ''', con=engine)
    inter_df = pd.read_sql('''
                      SELECT *
                      FROM international_data_clean
                      ''', con=engine)
    
    paired_skus = []
    
    for brand_idx in smoke_df['brand_idx'].drop_duplicates().to_list():
        sdf = smoke_df[smoke_df['brand_idx'] == brand_idx]
        idf = inter_df[inter_df['brand_idx'] == brand_idx]
        
        for _, row in sdf.iterrows():
            iidf = idf[idf['size'] == row['size']]
            iidf = iidf[iidf['qty'] == row['qty']]
            if len(iidf.index) == 1:
                paired_skus.append((row['sku'], iidf.iloc[0]['sku']))
                
            iidf = idf[idf['qty'] == row['qty']]
            
            for _, irow in iidf.iterrows():
                if row['title'] == irow['name']:
                    if not check_smoke_sku(paired_skus, row['sku']) and not check_inter_sku(paired_skus, irow['sku']):
                        paired_skus.append((row['sku'], irow['sku']))
                if irow['title'] in row['title']:
                    if not check_smoke_sku(paired_skus, row['sku']) and not check_inter_sku(paired_skus, irow['sku']):
                        paired_skus.append((row['sku'], irow['sku']))
                #if row['title'] in irow['name'] or irow['name'] in row['title']:
                #    paired_skus.append((row['sku'], irow['sku']))
    paired_skus = list(set(paired_skus))
    log('a', f'found {len(paired_skus)} matching products')
    
    
    data = {
        'inter_sku': [],
        'smoke_sku': [],
        'conf': [],
    }
    
    for (s, i) in paired_skus:
        data['inter_sku'].append(i)
        data['smoke_sku'].append(s)
        data['conf'].append(0)
    tdf = pd.DataFrame(data)
    write_to_db(tdf, 'equivalent_skus', engine)
    #tdf.to_sql('equivalent_skus', engine, index=False, if_exists='append')   
         