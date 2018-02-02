import requests
import pickle
from pprint import pprint


"""
QUANDL - Basic stock data

All open prices for Facebook

https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json?ticker=FB&qopts.columns=date,open&api_key=c5dqzrs4YNVTEaCpFn3a


Prices for all tickers for 2016-09-12

https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json?date=20160912&api_key=c5dqzrs4YNVTEaCpFn3a


Prices for Microsoft and Facebook for year 2015

https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json?date.gte=20150101&date.lt=20160101&ticker=MSFT,FB&api_key=c5dqzrs4YNVTEaCpFn3a


Sentiment - AAII Investor Sentiment Data
NASDAQ OMX Global Index Data

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
REDDIT - community opinion
"""

# import praw
# reddit = praw.Reddit(client_id='9hmhQ1D4ljWSag',
#                      client_secret='TEwFwiIkgex9S5ZGAon8z9ViCHE',
#                      user_agent='catalyst')
# subreddit = reddit.subreddit('RobinHoodPennyStocks')

# for submission in subreddit.hot(limit=25):
#     print(type(submission))
#     print(submission.title)
#     print(submission.comments)

# for comment in subreddit.comments(limit=25):
#     print(comment.body)

"""
TWITTER - community opinion

"""
# import twitter
# twit = twitter.Api(consumer_key='OhhRFRJ3Y3li5kCegraHtWVLG',
#             consumer_secret='prNqdviMhKZITTruRrAPnN08m9czP7GlpVrKaur0vGtkEj9DqE',
#             access_token_key='897912397666668544-AAxxXExtcPjd4B15QqlIiFLxFZPn1Ue',
#             access_token_secret='y9OSL1V2YyzBME2UW8J4UdzC9IoNGvDEatEh0QfcrZPPI')

# results = twit.GetSearch(raw_query="q=appl&result_type=recent&count=10")

# for r in results:
#     pprint(r.text)

"""
MORNINGSTAR - data

Portfolio Analytics API <- Maybe
"""
# import pandas as pd
# ticker = "FB"
# url = 'http://financials.morningstar.com/ajax/exportKR2CSV.html?&callback=?&t='+ticker+'&region=usa&culture=en-US&cur=USD&order=desc'
# df = pd.read_csv(url, skiprows=2, index_col=0)

# report = "bs"
# frequency = "3"
# url = 'http://financials.morningstar.com/ajax/ReportProcess4CSV.html?&t='+ticker+'&region=usa&culture=en-US&cur=USD&reportType='+report+'&period='+frequency+'&dataType=R&order=desc&columnYear=5&rounding=3&view=raw&r=640081&denominatorView=raw&number=3'
# df = pd.read_csv(url, skiprows=1, index_col=0)
# pprint(df)

"""
AYLIEN - sentiment analysis
"""
# from aylienapiclient import textapi

# client = textapi.Client("5da4ba8a", "3df445b4a8264c62f873c5ffb6ef183a")
# text = 'John is a very good football player'
# sentiment = client.Sentiment({'text': text})
# print(sentiment)