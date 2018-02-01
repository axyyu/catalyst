import requests
import pickle
from pprint import pprint


"""
QUANDL STUFF

All open prices for Facebook

https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json?ticker=FB&qopts.columns=date,open&api_key=c5dqzrs4YNVTEaCpFn3a


Prices for all tickers for 2016-09-12

https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json?date=20160912&api_key=c5dqzrs4YNVTEaCpFn3a


Prices for Microsoft and Facebook for year 2015

https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json?date.gte=20150101&date.lt=20160101&ticker=MSFT,FB&api_key=c5dqzrs4YNVTEaCpFn3a

"""
# r = requests.get('https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json?date=20180105&ticker=FB&api_key=c5dqzrs4YNVTEaCpFn3a')
# pprint(r.json())

# import quandl
# quandl.ApiConfig.api_key = "c5dqzrs4YNVTEaCpFn3a"

# print("\n ------- PRICES ------- \n")
# data = quandl.get_table('WIKI/PRICES', ticker='FB', date='20160912')
# pprint(data)

# print("\n ------- SENTIMENT ------- \n")
# data = quandl.get('AAII/AAII_SENTIMENT')
# pprint(data)

"""
REDDIT STUFF


"""

import praw
reddit = praw.Reddit(client_id='9hmhQ1D4ljWSag',
                     client_secret='TEwFwiIkgex9S5ZGAon8z9ViCHE',
                     user_agent='catalyst')
subreddit = reddit.subreddit('RobinHoodPennyStocks')

for submission in subreddit.hot(limit=25):
    print(type(submission))
    print(submission.title)
    # print(submission.text)

for comment in subreddit.comments(limit=25):
    print(comment.body)