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
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data import Fundamentals
from quantopian.pipeline.data import morningstar as ms
from quantopian.pipeline.classifiers.fundamentals import Sector 

# Sentdex
from quantopian.pipeline.data.sentdex import sentiment_free as sd

# Psychsignal
from quantopian.interactive.data.psychsignal import stocktwits as ps_st
from quantopian.interactive.data.psychsignal import twitter_noretweets as ps_tw

# Sklearn
from sklearn.ensemble import ExtraTreesClassifier # For before_trading_start
from sklearn.ensemble import AdaBoostClassifier # For handle_data

def initialize(context):

    # For Robinhood
    context.day_trade_protection = True
    context.day_trade_tracker = [0 for a in range(5)] # Chronologically left -> right
    
    set_long_only()
    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))

    # Data
    potential_training_data = []
    stock_training_data = []

    # Machine Learning
    potential_classifer = ExtraTreesClassifier()
    trade_classifier = AdaBoostClassifier()
    
    attach_pipeline(make_pipeline(), 'pipeline')

def make_pipeline():

    # Exchange filter
    exchange_id = ms.share_class_reference.exchange_id.latest
    exchange_filter = exchange_id.startswith('NYS') | exchange_id.startswith('NAS') | exchange_id.startswith('ASE')

    pipe = Pipeline(
        screen=exchange_filter
    )

    pipe.add( Sector(), 'Sector' )

    # Valuation Ratios
    pipe.add( Fundamentals.pe_ratio.latest, 'pe_ratio' )
    pipe.add( Fundamentals.peg_ratio.latest, 'peg_ratio' )
    pipe.add( Fundamentals.pcf_ratio.latest, 'pcf_ratio' )
    pipe.add( Fundamentals.pb_ratio.latest, 'pb_ratio' )
    pipe.add( Fundamentals.ps_ratio.latest, 'ps_ratio' )
    pipe.add( Fundamentals.ev_to_ebitda.latest, 'ev_to_ebitda' )

    # Liquidity
    pipe.add( Fundamentals.current_ratio.latest, 'current_ratio' )
    pipe.add( Fundamentals.quick_ratio.latest, 'quick_ratio' )
    pipe.add( Fundamentals.days_in_sales.latest, 'days_in_sales' )
    pipe.add( Fundamentals.inventory_turnover.latest, 'inventory_turnover' )

    # Profitability
    pipe.add( Fundamentals.normalized_net_profit_margin.latest, 'normalized_net_profit_margin' )
    pipe.add( Fundamentals.gross_margin.latest, 'gross_margin' )
    pipe.add( Fundamentals.operation_margin.latest, 'operation_margin' )

    # Debt
    pipe.add( Fundamentals.long_term_debt_equity_ratio.latest, 'long_term_debt_equity_ratio' )
    pipe.add( Fundamentals.long_term_debt_total_capital_ratio.latest, 'long_term_debt_total_capital_ratio' )
    pipe.add( Fundamentals.total_debt_equity_ratio.latest, 'total_debt_equity_ratio' )
    pipe.add( Fundamentals.free_cash_flow.latest, 'free_cash_flow' )

    # Sentiment
    pipe.add( sd.sentiment_signal.latest, 'sentdex' )
    pipe.add( ps_st.bull_bear_msg_ratio.latest, 'bull_bear_msg_ratio_st')
    pipe.add( ps_st.bullish_intensity .latest, 'bullish_intensity_st')
    pipe.add( ps_tw.bull_bear_msg_ratio.latest, 'bull_bear_msg_ratio_tw')
    pipe.add( ps_tw.bullish_intensity .latest, 'bullish_intensity_tw')

    return pipe

"""
Before Training
"""
def before_trading_start(context, data):
    context.output = pipeline_output('pipeline')
    context.security_list = context.output.index

    # Shift Pattern Day Trader
    context.day_trade_tracker.pop()
    context.day_trade_tracker.insert(0, 0)

    # Machine Learning Portion
    train(context, data)

def train(context, data):
    pass

"""
Trading Methods
"""

def handle_data(context, data):
    """
    Called every minute.
    """
    pass


"""
Buying and Selling
"""

def pattern_day_trader(context):
    if len([1 for t in context.day_trade_tracker if t == 1]) >= 3:
        return True
    return False

def buy(context):
    if context.day_trade_protection:
        if context.portfolio.portfolio_value > 25000 or not pattern_day_trader(context):
            return True
    return False

def sell(context):
    pass