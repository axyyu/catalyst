"""
This is a Robinhood Trading Template
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data import morningstar as ms

def initialize(context):
    # For Robinhood
    context.day_trade_protection = True
    context.day_trade_tracker = [0 for a in range(5)] # Chronologically left -> right
    
    set_long_only()
    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))
    
    attach_pipeline(make_pipeline(), 'pipeline')
    schedule_function(trade, date_rules.every_day(), time_rules.market_open())

def make_pipeline():

     # Exchange filter
    exchange_id = ms.share_class_reference.exchange_id.latest
    exchange_filter = exchange_id.startswith('NYS') | exchange_id.startswith('NAS') | exchange_id.startswith('ASE')

    pipe = Pipeline(
        screen=exchange_filter
    )
    return pipe


"""
Trading Methods
"""

def before_trading_start(context, data):
    context.output = pipeline_output('pipeline')
    context.security_list = context.output.index

    # Shift Pattern Day Trader
    context.day_trade_tracker.pop()
    context.day_trade_tracker.insert(0, 0)

def trade(context, data):
    pass

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