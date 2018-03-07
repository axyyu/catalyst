from tqdm import tqdm
from pathlib import Path
import requests
import pandas as pd
import pickle
import datetime
import numpy as np
<<<<<<< HEAD
import time
=======
import gzip
>>>>>>> 0233bbc581f9cb56df676cefd5de445f30437bc1

"""
Globals
"""
sector_map = {}
industry_map = {}
stock_list = []

"""
Stock Class
"""
class Stock():
    def __init__(self, ticker, sector, industry):
        self.ticker = ticker
        self.sector = sector
        self.industry = industry

"""
Obtain Stock List
"""
stock_list_file = Path("./stock_list.pickle")
if not stock_list_file.is_file():
    indexes = [
        pd.read_csv("nyse.csv"),
        pd.read_csv("nasdaq.csv"),
        pd.read_csv("amex.csv")
    ]

    for i in tqdm(indexes, desc="Collecting Stocks"):
        for n in i.index:
            if '^' not in i["Symbol"][n]:
                ticker = i["Symbol"][n]
                sector = i["Sector"][n]
                industry = i["industry"][n]

                stock_list.append( Stock(ticker, sector, industry) )
                if sector not in sector_map: # and not np.isnan(sector):
                    sector_map[len(sector_map)+1] = sector
                if industry not in industry_map: # and not np.isnan(industry):
                    industry_map[len(industry_map)+1] = industry

    with open('stock_list.pickle', 'wb') as handle:
        pickle.dump(stock_list, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('sector_map.pickle', 'wb') as handle:
        pickle.dump(sector_map, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('industry_map.pickle', 'wb') as handle:
        pickle.dump(industry_map, handle, protocol=pickle.HIGHEST_PROTOCOL)
else:
    with open('stock_list.pickle', 'rb') as handle:
        stock_list = pickle.load(handle)
    with open('sector_map.pickle', 'rb') as handle:
        sector_map = pickle.load(handle)
    with open('industry_map.pickle', 'rb') as handle:
        industry_map = pickle.load(handle)

"""
Obtain Stock Prices
"""
filename = datetime.datetime.now().strftime("stock_data/%Y-%m-%d.pkl.gz")
batches = []
count = 0
while 100*count < len(stock_list):
    stock_list[100*count:100*(count+1)]
    count+=1

data_file = Path("./stock_list.pickle")
if not data_file.is_file() or True:
    batches = []
    count = 0
    while 100*count < len(stock_list):
        batches.append(stock_list[100*count:100*(count+1)])
        count+=1

    data = {}
    for batch in tqdm(batches, desc="Downloading stock data"):
        batch_string = ""
        for b in batch:
            batch_string += b.ticker + ","
        batch_string.rstrip()
        r = requests.get('https://api.iextrading.com/1.0/stock/market/batch?symbols='
            +batch_string+
            '&range=1d&types=quote,news,chart'
        )
        for k,v in r.json().items():
            data[k] = v
        time.sleep(.1)

    with gzip.open(filename, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
else:
    print("FILE ALREADY EXISTS")
