from curl_cffi import requests
from bs4 import BeautifulSoup
import re
import sqlalchemy as sqa
import pandas as pd
from threading import Lock
import concurrent.futures
from datetime import datetime
from scrapingbee import ScrapingBeeClient as sbc
from enum import Enum

from src.log import *
from src.queries import write_to_db

NUM_THREADS = 5
MAX_RETRIES = 5

NUM_SITES = 3

CIGAR_COMPANY_INDEX_URL = 'https://www.cigarsinternational.com/shop/big-list-of-cigars-brands/1803000/'
CIGAR_COMPANY_URL = 'https://www.cigarsinternational.com'


SMOKE_BRAND_INDEX = 'https://www.smokeinn.com/Cigar-List/'
INTER_BRAND_INDEX = 'https://www.cigarsinternational.com/shop/big-list-of-cigars-brands/1803000/'

NEPTUNE_URL = 'https://www.neptunecigar.com'

class Brand(Enum):
    SMOKE = 1
    INTER = 2
    NEPTUNE = 3

# scrape a page, return page data
def scrape_page(url, proxy=True, premium=False):
    if proxy:
        with open('secrets/sb_api_key', 'r') as fp:
            sb_api_key = fp.read().strip()
        client = sbc(api_key=sb_api_key)
        for _ in range(MAX_RETRIES):
            page = client.get(url, params={
                "country_code": "us",
                "premium_proxy": premium,       # cigars international will block EU ips, so need premium to guarantee us location
            })
            if page.status_code == 200:
                return page.content
        log('e', f'index page {url} returned error code {page.status_code}', verbose=True)
        return None    
    else:
        page = requests.get(url, impersonate='edge')
        if page.status_code != 200:
            log('e', f'index page {url} returned error code {page.status_code}', verbose=True)
            return None
            
        return page.content

def scrape_data_combine(engine, debug, numThreads=NUM_THREADS, proxy=True):
    log('a', '---------- Scraping Cigar Brands ----------')


    # get neptune brands
    html = scrape_page(NEPTUNE_URL, proxy)
    if not html:
        return
    soup = BeautifulSoup(html, 'html.parser')
    brand_list = soup.find('div', id='divBrands111')
    neptune_brands = []
    for child in brand_list.children:
        if 'column' in child['id']:
            #soup = BeautifulSoup(child, 'html.parser')
            cigars = child.find_all('li', class_='classItem')
            for cigar in cigars:
                cigar = cigar.find('a')
                name = cigar.text.strip()
                name = name.lower()
                neptune_brands.append((name, NEPTUNE_URL+cigar['href'], Brand.NEPTUNE))

    # get smoke inn brands    
    html = scrape_page(SMOKE_BRAND_INDEX, proxy)
    if not html:
        return
    soup = BeautifulSoup(html, 'html.parser')
    brands = soup.find('ul', class_=re.compile('cigar_list'))
    smoke_brands = []
    for brand in brands.children:
        name = brand.text.strip()
        name = name.lower()
        if len(brand) < 2:
            continue
        smoke_brands.append((name, list(brand.children)[1]['href'], Brand.SMOKE))
        
    # get inter brands
    html = scrape_page(INTER_BRAND_INDEX, proxy, premium=proxy)
    if not html:
        return
    soup = BeautifulSoup(html, 'html.parser')
    brands = soup.find_all('a', class_=re.compile('biglist-browser-mobile-view'))
    inter_brands = []
    for brand in brands:
        href = CIGAR_COMPANY_URL + brand['href']
        brand = brand.text.strip()
        brand = brand.lower()
        inter_brands.append((brand, href, Brand.INTER))
        
    # match smoke inn and inter brands, keep only matching
    matching_brands = []
    for s in [val[0] for val in smoke_brands]:
        if s in [val[0] for val in inter_brands]:
            matching_brands.append(s)
        elif s in [val[0] for val in neptune_brands]:
            matching_brands.append(s)
    
    
    smoke_brands = [val for val in smoke_brands if val[0] in matching_brands]
    inter_brands = [val for val in inter_brands if val[0] in matching_brands]
    neptune_brands = [val for val in neptune_brands if val[0] in matching_brands]
    
    # TODO: fix this so it's not O(n^3)
    combine_list = []
    #for s in smoke_brands:
    #    combine_list.append([s])
    #for idx in range(len(combine_list)):
    #    row = combine_list[idx]
    #    s = row[0]
    #    for i in inter_brands:
    #        if s[0].lower == i[0].lower:
    #            combine_list[idx].append(i)
    #for idx in range(len(combine_list)):
    #    row = combine_list[idx]
    #    s = row[0]
    #    for n in neptune_brands:
    #        if s[0].lower == n[0].lower:
    #            combine_list[idx].append(n)
    #combine_list = [row for row in combine_list if len(row) > 1]
    #for row in combine_list:
    #    print(row)

    #return

    for s in smoke_brands:
        for i in inter_brands:
            for n in neptune_brands:
                row = [None, None, None]
                if s[0].lower() == i[0].lower():
                    row[0] = s
                    row[1] = i
                if s[0].lower() == n[0].lower():
                    row[0] = s
                    row[2] = n
                if not row[0]:
                    continue
                row = tuple(row)
                if row in combine_list:
                    continue
                if None not in row:
                    combine_list = [val for val in combine_list if (row[0] != val[0] and row[1] != val[1] and row[2] != val[2])]
                combine_list.append(row)
    
    futures = [0] * len(combine_list)
    lock_list = []
    for _ in range(NUM_SITES + 1):
        lock_list.append(Lock())

    log('a', f'Found {len(combine_list)} cigar types in common to scrape')

    if debug:
         for i, row in enumerate(combine_list):
            for val in row:
                if not val:
                    continue
                scrape_combine_data(engine, val, lock_list, i, proxy)
                if i == 2:
                    return
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=numThreads) as exe:
            for i, (row) in enumerate(combine_list):
                for val in row:
                    if not val:
                        continue
                    futures[i] = exe.submit(scrape_combine_data, engine, val, lock_list, i, proxy)
       

def scrape_combine_data(engine, row, lock_list, brand_idx, proxy=True):
    """scrapes smoke inn and inter pages that are related to each other

    Args:
        engine (sqlalchemy.engine): db engine
        smoke (str, str, Brand): scraping data (brand name, url, site)
        lock_list ([threading.Lock[]): list of locks for db table
        brand_idx (int): index of brand from list of like brands
        proxy (bool, optional): use proxy. Defaults to True.
    """
    log('a', '---------- Scraping Individual Cigar Data ----------')
    day = datetime.now().date()

    price_data = {
        'sku': [],
        'site': [],
        'timestamp': [],
        'price': [],
        'msrp': [],
        'sale': [],
    }
    match row[2]:
        case Brand.SMOKE:
            scrape_smoke_inn_data(engine, row, lock_list[1], lock_list[0], brand_idx, day, price_data, proxy)
        case Brand.INTER:
            scrape_international_data(engine, row, lock_list[2], lock_list[0], brand_idx, day, price_data, proxy)
        case Brand.NEPTUNE:
            scrape_neptune_data(engine, row, lock_list[3], lock_list[0], brand_idx, day, price_data, proxy)
        case _:
            return

    pdf = pd.DataFrame(price_data)
    with lock_list[0]:
        write_to_db(pdf, 'price_data', engine, check_insert=True)


def scrape_smoke_inn_data(engine, smoke, smoke_db_lock, price_data_lock, brand_idx, day, price_data, proxy):
    """scrape the individual page data for a smoke inn page

    Args:
        engine (sqlalchemy.engine): db engine
        smoke (str): page url
        smoke_db_lock (threading.Lock): lock for writing to smoke in db
        price_data_lock (threading.Lock): lock for writing price data
        brand_idx (int): index of brand from brand page
        day (_date): current date
        price_data (dict): dict to store price data into
        proxy (bool): use proxy
    """
    smoke_data = {
        'sku': [],
        'title': [],
        'size': [],
        'qty': [],
        'price': [],
        'msrp': [],
        'url': [],
        'brand': [],
        'brand_idx': [],
        'timestamp': [],
    }

    log('a', f'scraping smoke inn page {smoke[1]}', True)
    html = scrape_page(smoke[1], proxy)
    if not html:
        return
    soup = BeautifulSoup(html, 'html.parser')
    products = soup.find('div', class_='products products-list list_view')
    products = products.find_all(class_=re.compile('.*item'))
    link_list = []
    for p in products:
        links = p.find_all('a')
        for link in links:
            if link and link['href'] and link['href'][-5:] == '.html':
                link_list.append(link['href'])
                
    for link in link_list:
        html = scrape_page(link, proxy)
        if not html:
            return
        soup = BeautifulSoup(html, 'html.parser')
        smoke_data['sku'].append(soup.find('div', id='product_code').text)
        
        prices = soup.find_all('span', class_='currency')
        if len(prices) > 1:
            smoke_data['msrp'].append(prices[0].text[1:])
            smoke_data['price'].append(prices[1].text[1:])
        else:
            smoke_data['msrp'].append(0)
            smoke_data['price'].append(prices[0].text[1:])
        
        notes = soup.find('div', class_='notes').find_all('div', class_='property-value')
        # it's backwards at least once, hence the check
        if 'x' in notes[0].text.lower():
            smoke_data['size'].append(notes[0].text)
            smoke_data['qty'].append(notes[1].text)
        else:    
            smoke_data['size'].append(notes[1].text)
            smoke_data['qty'].append(notes[0].text)
        smoke_data['title'].append(soup.find('div', class_='details_product').find('h1').text)
        smoke_data['url'].append(link)
        
        with price_data_lock:
            price_data['sku'].append(smoke_data['sku'][-1])
            price_data['site'].append('smoke inn')
            price_data['timestamp'].append(day)
            price_data['price'].append(smoke_data['price'][-1])
            price_data['msrp'].append(smoke_data['msrp'][-1] if smoke_data['msrp'][-1] else 0) # replace None with 0 because pd can't match None and None
            price_data['sale'].append(False) # TODO: placeholder for checking sale data
        
    len_data = len(smoke_data['sku'])
    smoke_data['brand'] = [smoke[0]] * len_data
    smoke_data['brand_idx'] = [brand_idx] * len_data
    smoke_data['timestamp'] = [day] * len_data
    
    smoke_data['msrp'] = [float(price) for price in smoke_data['msrp']]
    smoke_data['price'] = [float(price) for price in smoke_data['price']]

    sdf = pd.DataFrame(smoke_data)
    with smoke_db_lock:
        write_to_db(sdf, 'smoke_inn_data', engine, check_insert=True)

 
def scrape_international_data(engine, inter, inter_db_lock, price_data_lock, brand_idx, day, price_data, proxy):
    """scrape the individual page data for a cigars international page

    Args:
        engine (sqlalchemy.engine): db engine
        inter (str): page url
        inter_db_lock (threading.Lock): lock for writing to international db
        price_data_lock (threading.Lock): lock for writing price data
        brand_idx (int): index of brand from brand page
        day (_date): current date
        price_data (dict): dict to store price data into
        proxy (bool): use proxy
    """
    inter_data = {
        'sku': [],
        'title': [],
        'shape': [],
        'size': [],
        'name': [],
        'qty': [],
        'price': [],
        'msrp': [],
        'url': [],
        'brand': [],
        'brand_idx': [],
        'timestamp': [],
    }

    log('a', f'scraping international page {inter[1]}', True)
    html = scrape_page(inter[1], proxy, premium=proxy)
    if not html:
        return
    soup = BeautifulSoup(html, 'html.parser')
    products = soup.find_all('div', itemprop='offers')
    # TODO: if len products is 0, should consider just skipping to next product

    for p in products:
        inter_data['sku'].append(p.find('meta', itemprop='sku')['content'])
        inter_data['shape'].append(p.find('span', class_='cigar-shape'))
        inter_data['title'].append(p.find('span', class_='cigar-title'))
        inter_data['size'].append(p.find('span', class_='size-text pr-2'))
        inter_data['name'].append(p.find('meta', itemprop='name')['content'])
        inter_data['qty'].append(p.find('span', class_='quantity-heading text-uppercase'))
        
        price_data_big = p.find_all('span', class_='price-dollars')
        price_data_small = p.find_all('span', class_='price-cents')
        inter_data['msrp'].append(price_data_big[0].text+'.'+price_data_small[0].text)
        inter_data['price'].append(price_data_big[2].text+'.'+price_data_small[2].text)
        
        with price_data_lock:
            price_data['sku'].append(inter_data['sku'][-1])
            price_data['site'].append('international')
            price_data['timestamp'].append(day)
            price_data['sale'].append(False) # TODO: placeholder for sale check
            price_data['price'].append(inter_data['price'][-1])
            price_data['msrp'].append(inter_data['msrp'][-1] if inter_data['msrp'][-1] else 0) # replace None with 0 because pd can't match None and None
        
    for i in range(len(inter_data['title'])):
        for col in ['title', 'size', 'shape', 'qty']:
            inter_data[col][i] = inter_data[col][i].text if inter_data[col][i] else None
        
    len_data = len(inter_data['sku'])
    inter_data['url'] = [inter[1]] * len_data
    inter_data['brand'] = [inter[0]] * len_data
    inter_data['brand_idx'] = [brand_idx] * len_data
    inter_data['timestamp'] = [day] * len_data
   
    inter_data['price'] = [float(price) for price in inter_data['price']]
    inter_data['msrp'] = [float(msrp) for msrp in inter_data['msrp']]

    idf = pd.DataFrame(inter_data)
    with inter_db_lock:
        write_to_db(idf, 'international_data', engine, check_insert=True)


def scrape_neptune_data(engine, neptune, neptune_db_lock, price_data_lock, brand_idx, day, price_data, proxy):
    """scrape price data for neptune cigars

    Args:
        engine (sqlalchemy.engine): db engine
        neptune (str): page rul
        neptune_db_lock (threading.Lock): lock for writing to neptune db
        price_data_lock (threading.Lock): lock for writing price data
        brand_idx (int): index of brand from brand page
        day (_date): current date
        price_data (dict): dict to store price data into
        proxy (bool): use proxy
    """
    neptune_data = {
        'sku': [],
        'name': [],
        'size': [],
        'qty': [],
        'price': [],
        'msrp': [],
        'url': [],
        'brand': [],
        'brand_idx': [],
        'timestamp': [],
    }

    log('a', f'scraping neptune cigars page {neptune[1]}', True)

    html = scrape_page(neptune[1], proxy)
    if not html:
        return
    soup = BeautifulSoup(html, 'html.parser')
    cigars = soup.find_all('a', class_='product_name')
    product_url_list = []
    for c in cigars:
        product_url_list.append(NEPTUNE_URL+c['href'])


    for url in product_url_list:

        html = scrape_page(url, False)
        soup = BeautifulSoup(html, 'html.parser') 
        data = soup.find('table', id='product_table')
        data = data.find_all('tr', align='center')

        specs = soup.find('ul', class_='pr_specList')

        brand = None
        length = None
        diameter = None

        for s in specs.children:
            category = next(s.children).text
            match category:
                case 'Brands':
                    brand = s.find('div', class_='onHover').text
                case 'Cigar Length':
                    length = ''.join(v for v in s.find('div', class_='onHover').text if v.isdigit())
                case 'Cigar Ring Gauge': 
                    diameter = ''.join(v for v in s.find('div', class_='onHover').text if v.isdigit())
                case 'UPC':
                    for sku in list(s.children)[1:]:
                        neptune_data['sku'].append(sku.text)
        name = url.split('/')[-1].replace('-', ' ')

        for row in data:
            row = list(row.children)
            neptune_data['qty'].append(row[0].text)
            neptune_data['msrp'].append(''.join(v for v in row[1].text if v.isdigit() or v == '.'))
            neptune_data['price'].append(''.join(v for v in row[2].text if v.isdigit() or v == '.'))
            neptune_data['name'].append(name)
            neptune_data['size'].append(f'{length}x{diameter}')
            neptune_data['brand'].append(brand)
            neptune_data['url'].append(url)
            neptune_data['timestamp'].append(day)
            neptune_data['brand_idx'].append(brand_idx)

        with price_data_lock:
            price_data['sku'] += neptune_data['sku']
            price_data['site'] += neptune_data['url']
            price_data['timestamp'] += neptune_data['timestamp']
            price_data['price'] += neptune_data['price']
            price_data['msrp'] += neptune_data['msrp']
            price_data['sale'] += [False] * len(neptune_data['sku'])

    ndf = pd.DataFrame(neptune_data)
    with neptune_db_lock:
        write_to_db(ndf, 'neptune_data', engine, check_insert=True)


    