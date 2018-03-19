import datetime
import gzip
import pickle
import os

import matplotlib.pyplot as plt

def sample(ticker="BPMX"):
    d = datetime.date(month=3, day=8, year=2018)
    return get_stock_data(ticker, d, d)

def plot_pktr(prices, pk, tr):
    plt.plot(tr, [prices[x] for x in tr], marker='o', color='b', ls='')
    plt.plot(pk, [prices[x] for x in pk], marker='o', color='y', ls='')
    plt.plot(prices)
    plt.show()

def get_peaks_troughs(prices):
    tr = []
    pk = []
    for i in range(1, len(prices)-1):
        if prices[i-1] < prices[i] > prices[i+1]:
            pk.append(i)
        elif prices[i-1] > prices[i] < prices[i+1]:
            tr.append(i)
    return (pk, tr)

def minute_from_datelabel(date, minute):
    # calculates minute from Jan 1, 2000

    assert len(date) == 8, "date in incorrect format"
    assert len(minute) == 5, "minute in incorrect format"

    d2 = datetime.datetime(year=2000, month=1, day=1, minute=0, hour=0)
    d = datetime.datetime(year=int(date[:4]), month=int(date[4:6]), day=int(date[6:]),\
            minute=int(minute[3:5]), hour=int(minute[:2]))
    return int(round((d-d2).total_seconds() / 60.0))


def get_stock_data(ticker, start_date, end_date):
    # retrieves stock data from pkl.gz files

    # returns list of 1-minute intervals in (high, low, ave, volume) format

    d = start_date
    data = []
    while True:
        filename = d.strftime("stock_data/%Y-%m-%d.pkl.gz")
        if os.path.isfile(filename):
            with gzip.open(filename, "rb") as f:
                f_data = pickle.loads(f.read())
                assert len(f_data[ticker]["chart"]) == 390,\
                    "incorrect number of minutes for {} - {}"\
                    .format(ticker, d.strftime("%Y-%m-%d"))
                for idx, j in enumerate(f_data[ticker]["chart"]):
                    assert j["marketLow"] != -1,\
                            "{} - {} marketLow at minute {} not defined"\
                            .format(ticker, d.strftime("%Y-%m-%d"), idx)
                    assert j["marketHigh"] != -1,\
                            "{} - {} marketHigh at minute {} not defined"\
                            .format(ticker, d.strftime("%Y-%m-%d"), idx)
                    assert j["marketAverage"] != -1,\
                            "{} - {} marketAverage at minute {} not defined"\
                            .format(ticker, d.strftime("%Y-%m-%d"), idx)
                    assert j["marketVolume"] != -1,\
                            "{} - {} marketVolume at minute {} not defined"\
                            .format(ticker, d.strftime("%Y-%m-%d"), idx)
                    data.append((j["marketHigh"], j["marketLow"], j["marketAverage"], j["marketVolume"]))
        else:  # it's a weekend or holiday probably
            pass
        if d == end_date:
            break
        d += datetime.timedelta(days=1)
    return data

