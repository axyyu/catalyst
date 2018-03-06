"""
Robinhood Sentiment Analysis and Machine Learning Algorithm

Variables:
    Potential Training Data - stores the history of the market from pipeline data for 30 days
        - Retains a small sample of data each time the pipeline is run
        - Incorpates a random sample of new data
    Stock Training Data - stores the past volume and price fluctuations of a stock
        - Includes 'price', 'open', 'high', 'low', 'close', 'volume'

Every day:
    - Retrieves stock data from pipeline
        - Restricted to NYSE, NASDAQ, and ASE for Robinhood purposes
    - Uses a classifier to determine whether the stock has potential
        - Twitter and StockTwit Sentiment (PsychSignal)
        - News and Journals Sentiment (Sentdex)
        - Fundamental Data
            - pe_ratio
            - peg_ratio
            - pcf_ratio
            - pb_ratio
            - ps_ratio
            - ev_to_ebitda

            Liquidity
            - current_ratio
            - quick_ratio
            - days_in_sales
            - inventory_turnover

            Profitability
            - normalized_net_profit_margin
            - gross_margin
            - operation_margin

            Debt
            - long_term_debt_equity_ratio
            - long_term_debt_total_capital_ratio
            - total_debt_equity_ratio
            - free_cash_flow
    - Trains classifiers

Every minute:
    - Retrieves historic data from potential and portfolio stocks
    - Uses classifier on stock to determine buy or sell
"""

# Algorithm
from quantopian.algorithm import attach_pipeline, pipeline_output

# Pipeline
from quantopian.pipeline import Pipeline, CustomFactor
from quantopian.pipeline.data import Fundamentals
from quantopian.pipeline.data import morningstar as ms
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import Q1500US, Q500US

from quantopian.pipeline.classifiers.fundamentals import Sector
from quantopian.pipeline.factors import RSI

# Psychsignal
from quantopian.pipeline.data.psychsignal import stocktwits as ps_st
from quantopian.pipeline.data.psychsignal import twitter_noretweets as ps_tw

# Sklearn
from sklearn.ensemble import ExtraTreesClassifier # For before_trading_start
from sklearn.ensemble import AdaBoostClassifier # For handle_data

# Other
import random
import numpy as np
from operator import itemgetter

def initialize(context):

    # For Robinhood
    context.day_trade_protection = True
    context.day_trade_tracker = [0 for a in range(5)] # Chronologically left -> right
    
    set_long_only()
    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))

    # Hyperparams
    context.potential_data_size = 1000
    context.potential_splice = .7
    context.potential_model = ExtraTreesClassifier()
    context.potential_model.n_estimators = 100 #Number of trees
    context.potential_model.min_samples_leaf = 10 #Minimum number of results in the leaves

    context.stock_data_size = 1000
    context.stock_splice = .7
    context.stock_lookback = 10
    context.stock_model = AdaBoostClassifier()
    context.stock_model.n_estimators = 100 #Number of trees
    context.stock_model.min_samples_leaf = 10 #Minimum number of results in the leaves

    # Parameters
    context.order_value = 100

    # Data
    context.potential_training_data = []
    
    attach_pipeline(make_pipeline(), 'pipeline')

"""
Pipeline
"""
class CloseNotLatest(CustomFactor):  
    inputs = [Fundamentals.pe_ratio]
    window_length = 2 
    
    def compute(self, today, assets, out, close):  
        out[:] = close[0]

class CloseLatest(CustomFactor):  
    inputs = [Fundamentals.pe_ratio]
    window_length = 1
    
    def compute(self, today, assets, out, close):  
        out[:] = close[0]

def addElements(pipe, data_call, identifier):
    # Price
    pipe.add( data_call( inputs = [ USEquityPricing.close ] ), 'price' + "_" + identifier )
    pipe.add( data_call( inputs = [ RSI() ] ), 'rsi' + "_" + identifier )

    # Valuation Ratios
    pipe.add( data_call( inputs = [ Fundamentals.pe_ratio ] ), 'pe_ratio' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.peg_ratio ] ), 'peg_ratio' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.pcf_ratio ] ), 'pcf_ratio' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.pb_ratio ] ), 'pb_ratio' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.ps_ratio ] ), 'ps_ratio' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.ev_to_ebitda ] ), 'ev_to_ebitda' + "_" + identifier )

    # Liquidity
    pipe.add( data_call( inputs = [ Fundamentals.current_ratio ] ), 'current_ratio' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.quick_ratio ] ), 'quick_ratio' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.days_in_sales ] ), 'days_in_sales' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.inventory_turnover ] ), 'inventory_turnover' + "_" + identifier )

    # Profitability
    pipe.add( data_call( inputs = [ Fundamentals.normalized_net_profit_margin ] ), 'normalized_net_profit_margin' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.gross_margin ] ), 'gross_margin' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.operation_margin ] ), 'operation_margin' + "_" + identifier )

    # Debt
    pipe.add( data_call( inputs = [ Fundamentals.long_term_debt_equity_ratio ] ), 'long_term_debt_equity_ratio' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.long_term_debt_total_capital_ratio ] ), 'long_term_debt_total_capital_ratio' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.total_debt_equity_ratio ] ), 'total_debt_equity_ratio' + "_" + identifier )
    pipe.add( data_call( inputs = [ Fundamentals.free_cash_flow ] ), 'free_cash_flow' + "_" + identifier )

    # Sentiment
    # pipe.add( data_call( inputs = [ sd.sentiment_signal ] ), 'sentdex' + "_" + identifier )
    # pipe.add( data_call( inputs = [ ps_st.bull_bear_msg_ratio ] ), 'bull_bear_msg_ratio_st' + "_" + identifier )
    pipe.add( data_call( inputs = [ ps_st.bullish_intensity  ] ), 'bullish_intensity_st' + "_" + identifier )
    pipe.add( data_call( inputs = [ ps_st.bearish_intensity  ] ), 'bearish_intensity_st' + "_" + identifier )
    # pipe.add( data_call( inputs = [ ps_tw.bull_bear_msg_ratio ] ), 'bull_bear_msg_ratio_tw' + "_" + identifier )
    pipe.add( data_call( inputs = [ ps_tw.bullish_intensity  ] ), 'bullish_intensity_tw' + "_" + identifier )
    pipe.add( data_call( inputs = [ ps_tw.bearish_intensity  ] ), 'bearish_intensity_tw' + "_" + identifier )

def make_pipeline():

    base_universe = Q500US()

    # Exchange filter
    exchange_id = ms.share_class_reference.exchange_id.latest
    exchange_filter = exchange_id.startswith('NYS') | exchange_id.startswith('NAS') | exchange_id.startswith('ASE')

    pipe = Pipeline(
        screen= base_universe & exchange_filter
    )

    addElements(pipe, CloseNotLatest, "yesterday")
    addElements(pipe, CloseLatest, "today")

    return pipe

"""
Before Trading
"""
def before_trading_start(context, data):
    context.output = pipeline_output('pipeline')

    # Shift Pattern Day Trader
    context.day_trade_tracker.pop()
    context.day_trade_tracker.insert(0, 0)

    # Machine Learning Portion
    context.potential_securities = predict_potential_securities(context)

"""
Data Manipulation
"""
def splice_data(dataset, extra, length, percen):
    """
    Updates dataset
    """
    if len(dataset) < length:
        sample_size = min( len(extra[0]), length - len(dataset) )
        sample_set = random.sample( range(len(extra[0])), sample_size )

        input_data = np.concatenate( dataset[0], [ extra[0][x] for x in sample_set ] )
        output_data = np.concatenate( dataset[1], [ extra[1][x] for x in sample_set ] )

        return [ input_data, output_data ]
    else:

        ex_sample_size = min( len(extra[0]), random.randint( 0, percen*length ) )
        ex_sample_set = random.sample( range(len(extra[0])), ex_sample_size )

        da_sample_size = length - ex_sample_size
        da_sample_set = random.sample( range(len(dataset)), da_sample_size )

        input_data = np.concatenate( dataset[0], [ extra[0][x] for x in ex_sample_set ] )
        output_data = np.concatenate( dataset[1], [ extra[1][x] for x in da_sample_set ] )

        return [ input_data, output_data ]

def reformat_data(results):
    """
    Changes dataframe to arrays
    """
    training_data = [[],[]]
    testing_data = {}

    for r in results.index:
        old_data = []
        new_data = []
        for p in results:
            if "today" in p:
                if "price" not in p:
                    new_data.append( results[p][r] )
            elif "yesterday" in p:
                if "price" not in p:
                    old_data.append( results[p][r] )
        
        training_data[0].append(old_data)
        training_data[1].append( results["price_today"][r] - results["price_yesterday"][r] )
        testing_data[r] = np.nan_to_num(new_data)

    return training_data, testing_data

def process_data(train, test):
    """
    Removes empty data
    """
    train[0] = np.nan_to_num(train[0])
    train[1] = np.clip( np.nan_to_num(train[1]), -1, 1)
    
    test = np.nan_to_num(test)
    return train, test

def reformat_stock_data(res):
    training_data = [[],[]]
    testing_data = []

    for b in range(len(res.index)-1):
        temp = []
        for a in res:
            if 'price' != a:
                temp.append(res[a][res.index[b]])
            
        training_data[0].append(temp)
        training_data[1].append( res['price'][res.index[b+1]] - res['price'][res.index[b]] )
        
    for a in res:
        if 'price' != a:
            testing_data.append(res[a][res.index[len(res.index)-1]])
    return training_data, testing_data

"""
Machine Learning
"""
def predict_potential_securities(context):
    training_data, testing_data = reformat_data(context.output)
    training_data, testing_data = process_data( training_data, testing_data )

    context.potential_training_data = splice_data(context.potential_training_data, training_data, context.potential_data_size, context.potential_splice )
    context.potential_model.fit( context.potential_training_data[0], context.potential_training_data[1] )

    return [ d for d in testing_data if context.potential_model.predict( testing_data[d] ) > 0 ]

def predict_stock_purchase(context, data, security):
    results = data.history(security, fields=["price", "open", "high", "low", "close", "volume"], bar_count=(context.stock_lookback), frequency="1d")
    
    training_data, testing_data = reformat_data(results)
    training_data, testing_data = process_data( training_data, testing_data )

    context.stock_model.fit( training_data[0] , training_data[1] )
    return context.stock_model.predict( testing_data )

"""
Trading Methods
"""

def handle_data(context, data):
    """
    Called every minute.
    """

    portfolio_sec = []
    for sec,pos in context.portfolio.positions.iteritems():
        portfolio_sec.append( (sec, predict_stock_purchase(context, data, sec)) )
    portfolio_sec = [ a[0] for a in portfolio_sec if a[1] < 0 ]
    sell_securities( context, data, portfolio_sec )

    potential_sec = []
    for sec in context.potential_securities:
        potential_sec.append( (sec, predict_stock_purchase(context, data, sec)) )
    potential_sec = [ a[0] for a in portfolio_sec if a[1] > 0 ]
    potential_sec = sorted(potential_sec, key=itemgetter(1), reverse=True)

"""
Buying and Selling
"""

def pattern_day_trader(context):
    if len([1 for t in context.day_trade_tracker if t == 1]) >= 3:
        return True
    return False

def buy(context, data, securities):
    if context.day_trade_protection:
        if context.portfolio.portfolio_value > 25000 or not pattern_day_trader(context):
            for sec in securities:
                order_value(sec, context.order_value )

def sell_securities(context, data, securities):
    for sec in securities:
        order(sec, -context.portfolio.positions[sec] )