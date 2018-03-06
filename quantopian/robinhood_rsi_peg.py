"""
Trading using RSI and PEG only

PEG 
    buy < 1
    sell > 1
RSI
    buy < .3
    sell > .7
"""
from quantopian.algorithm import attach_pipeline, pipeline_output

from quantopian.pipeline import Pipeline
from quantopian.pipeline.data import morningstar as ms
from quantopian.pipeline.data import Fundamentals
from quantopian.pipeline.factors import RSI
from quantopian.pipeline.data.builtin import USEquityPricing

def initialize(context):
    # Trading Price Cap
    context.price_cap = 100
    context.price_floor = 5

    context.price_value = 100

    # For Robinhood
    context.day_trade_protection = True
    context.day_trade_tracker = [0 for a in range(5)] # Chronologically left -> right
    
    set_long_only()
    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))
    
    attach_pipeline(make_pipeline(context), 'pipeline')
    schedule_function(trade, date_rules.every_day(), time_rules.market_open())

def make_pipeline(context):

    # Price Filter
    price_filter = (USEquityPricing.close.latest < context.price_cap) & (USEquityPricing.close.latest > context.price_floor)

    # Exchange filter
    exchange_id = ms.share_class_reference.exchange_id.latest
    exchange_filter = exchange_id.startswith('NYS') | exchange_id.startswith('NAS') | exchange_id.startswith('ASE')

    # Relative Strength Index
    rsi = RSI()
    rsi_filter = (rsi > .7) | (rsi < .3)

    peg = Fundamentals.peg_ratio.latest
    peg_filter = (peg > 1) | (peg < 1)

    pipe = Pipeline(
        screen = exchange_filter & price_filter & rsi_filter & peg_filter,
        columns = {
            "RSI": rsi,
            "PEG": peg
        }
    )
    return pipe

"""
Trading Methods
"""

def before_trading_start(context, data):
    context.purchased_sec = []
    context.output = pipeline_output('pipeline')
    context.security_list = context.output.index

    # Shift Pattern Day Trader
    context.day_trade_tracker.pop()
    context.day_trade_tracker.insert(0, 0)

def trade(context, data):
    """
    Called Every Day
    """
    bad_secs = [sec for sec in context.portfolio.positions if sec not in context.output]
    sell(context, bad_secs)

    buy(context, context.security_list)

"""
Buying and Selling
"""

def pattern_day_trader(context):
    if len([1 for t in context.day_trade_tracker if t == 1]) >= 3:
        return True
    return False

def buy(context, securities):
    if context.day_trade_protection:
        if context.portfolio.portfolio_value > 25000 or not pattern_day_trader(context):
            pur_limit = context.portfolio.cash/context.price_value
            count = 0
            for sec in securities:
                if count >= pur_limit:
                    return
                order_value(sec, context.price_value)
                context.purchased_sec.append(sec)
                count+=1

def sell(context, securities):
    for sec in securities:
        order(sec, -context.portfolio.positions[sec].amount )
        if sec in context.purchased_sec:
            context.day_trade_tracker[-1] += 1