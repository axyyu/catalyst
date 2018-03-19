import sqlalchemy
from sqlalchemy import and_
from sqlalchemy.sql import exists
from sqlalchemy.orm import sessionmaker
from db import engine, Base, Stock, News, ChartData, get_or_create
from utils import minute_from_datelabel

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

from tqdm import tqdm
from pathlib import Path
import random
import requests
import pandas as pd
import pickle
import datetime
import numpy as np
import time
import gzip

"""
Globals
"""
sector_map = {}
industry_map = {}
stock_list = []


"""
Obtain Stock List
"""
stock_list_file = Path("./stock_list.pickle")
if not stock_list_file.is_file() or session.query(Stock).count() < 100:
    indexes = [
        pd.read_csv("nyse.csv"),
        pd.read_csv("nasdaq.csv"),
        pd.read_csv("amex.csv")
    ]
    seen = {}

    for i in tqdm(indexes, desc="Collecting Stocks"):
        for n in i.index:
            if '^' not in i["Symbol"][n]:
                ticker = i["Symbol"][n]
                sector = i["Sector"][n]
                industry = i["industry"][n]

                if ticker in seen:
                    continue
                seen[ticker] = 1

                s = Stock(ticker=ticker, sector=sector, industry=industry)
                session.add(s)
                stock_list.append(s)
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
        
session.commit()
stocks = session.query(Stock).all()
stocks = [s.ticker for s in stocks]
print(len(stocks))


"""
Obtain Stock Prices
"""
filename = datetime.datetime.now().strftime("stock_data/%Y-%m-%d.pkl.gz")
batches = []
count = 0
while 100*count < len(stock_list):
    stock_list[100*count:100*(count+1)]
    count += 1

random.shuffle(stock_list)

data_file = Path("./stock_list.pickle")
if not data_file.is_file() or True:
    batches = []
    count = 0
    while 100*count < len(stock_list):
        batches.append(stock_list[100*count:100*(count+1)])
        count+=1

    for batch in tqdm(batches, desc="Downloading stock data"):
        batch_string = ""
        for b in batch:
            batch_string += b.ticker + ","
        batch_string.rstrip()
        r = requests.get('https://api.iextrading.com/1.0/stock/market/batch?symbols='
            +batch_string+
            '&range=1d&types=news,chart'
        )
        for k,v in r.json().items():
            if k not in stocks:
                print("{} not in db, skipping...".format(k))
                continue
            try:
                for n in v["news"]:
                    p1 = n["datetime"][:-6]
                    p2 = n["datetime"][-6:]
                    p2 = p2[:3]+p2[4:]
                    final = p1+"|"+p2
                    m_time = datetime.datetime.strptime(final, "%Y-%m-%dT%H:%M:%S|%z")
                    if session.query(
                            exists().where(
                                and_(News.stock_ticker==k, News.time==m_time)
                            )
                        ).scalar():
                        continue
                    n = News(stock_ticker=k, headline=n["headline"],\
                            time=m_time,\
                            summary=n["summary"], related=n["related"])
                    session.add(n)
                mins = {}
                for c in v["chart"]:
                    hi = c["marketHigh"] if c["marketHigh"] > 0 else None
                    lo = c["marketLow"] if c["marketLow"] > 0 else None
                    ave = c["marketAverage"] if c["marketAverage"] > 0 else None
                    vol = c["marketVolume"] if c["marketVolume"] > 0 else None
                    minute = minute_from_datelabel(c["date"], c["minute"])
                    assert minute not in mins
                    mins[minute] = 1
                    if session.query(
                            exists().where(
                                and_(ChartData.stock_ticker==k, ChartData.minute==minute)
                            )
                        ).scalar():
                        continue
                    c = ChartData(stock_ticker=k,
                            minute=minute,
                            high=hi, low=lo, average=ave, volume=vol)
                    session.add(c)
                session.commit()
            except Exception as e:
                print("Error on {}: {}".format(k, str(e)))
        time.sleep(1)
session.commit()
session.close()
