from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data import morningstar as ms
from quantopian.pipeline.data import Fundamentals
from quantopian.pipeline.data.builtin import USEquityPricing

import talib
import numpy as np
import pandas as pd

"""
The initialize function sets any data or variables 
that you'll use in your algorithm. It's only called 
once at the beginning of your algorithm.
"""
def initialize(context):
    # Hyperparams -----------------------


    # Fundamentals
    context.pe_cap = 5;
    context.peg_cap = 5;
    context.ps_floor = 0.1;
    context.cash_flow_floor = 100;
    context.pm_floor = 0
    context.cr_floor = 1
    context.qr_floor = 1
    context.at_floor = 1

    # MACD
    context.fastperiod = 30; #12
    context.slowperiod = 40; #26
    context.signalperiod = 45; #9

    # Trading
    context.buy_threshold = 0;
    context.sell_threshold = 0;


    # -----------------------------------

    # For Robinhood
    context.day_trade_protection = True
    context.day_trade_tracker = [0 for a in range(5)] # Chronologically left -> right
    
    set_long_only()
    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))
    
    attach_pipeline(make_pipeline(context), 'pipeline')

def make_pipeline(context):
    price_filter = USEquityPricing.close.latest < context.portfolio.cash

    # Fundamental Filters ---------------------------------

    # PRICE
    pe_filter = Fundamentals.pe_ratio.latest < context.pe_cap
    peg_filter = Fundamentals.peg_ratio.latest < context.peg_cap
    ps_filter = Fundamentals.ps_ratio.latest > context.ps_floor
    cash_flow_filter = Fundamentals.free_cash_flow.latest > context.cash_flow_floor

    price_ratio = pe_filter & peg_filter & ps_filter & cash_flow_filter

    # PRICE
    pm_filter = Fundamentals.normalized_net_profit_margin.latest > context.pm_floor

    profit_ratio = pm_filter

    # LIQUIDITY
    current_ratio = Fundamentals.current_ratio.latest > context.cr_floor
    quick_ratio = Fundamentals.quick_ratio.latest > context.qr_floor

    liquid_ratio = current_ratio & quick_ratio

    # EFFICIENCY
    assets_turnover = Fundamentals.assets_turnover.latest > context.at_floor

    effciency_ratio = assets_turnover

    # ------------------------------------------------------

    # Exchange filter
    exchange_id = ms.share_class_reference.exchange_id.latest
    exchange_filter = exchange_id.startswith('NYS') | exchange_id.startswith('NAS') | exchange_id.startswith('ASE')

    pipe = Pipeline(
        screen=exchange_filter & price_filter & price_ratio & profit_ratio
    )

    return pipe

"""
Reset trading status
"""
def before_trading_start(context, data):
    context.traded = []

    context.purchased_sec = []
    context.output = pipeline_output('pipeline')
    context.security_list = context.output.index

    # Shift Pattern Day Trader
    context.day_trade_tracker.pop()
    context.day_trade_tracker.insert(0, 0)

    record(pos=len(context.security_list))

"""
Processing
"""
def handle_data(context, data):
    return
    sell_secs = []
    for sec in context.portfolio.positions:
        macd = get_macd(context, data, sec)

        if macd < context.sell_threshold and data.can_trade(sec) and sec not in context.traded:
            sell_secs.append(sec)

    sell(context, sell_secs)

    buy_secs = []
    for sec in context.security_list:
        macd = get_macd(context, data, sec)

        if macd > context.buy_threshold and data.can_trade(sec) and sec not in context.traded:
            buy_secs.append(sec)
    if len(buy_secs) > 0:
        buy(context, buy_secs,  1/len(buy_secs))
            
    

def get_macd(context, data, sec):
    price_history = data.history(
        sec,
        fields='price',
        bar_count=3000,
        frequency='1m')
    price_history = price_history[::30]

    macd_raw, signal, macd_hist = talib.MACD(price_history, 
                                             fastperiod=context.fastperiod, 
                                             slowperiod=context.slowperiod, 
                                             signalperiod=context.signalperiod)

    return macd_hist[-1]

"""
Trading
"""
def pattern_day_trader(context):
    if len([1 for t in context.day_trade_tracker if t == 1]) >= 3:
        return True
    return False

def buy(context, securities, percent):
    if context.day_trade_protection:
        if context.portfolio.portfolio_value > 25000 or not pattern_day_trader(context):
            for sec in securities:
                order_percent(sec, percent)
                context.purchased_sec.append(sec)
                context.traded.append(sec)

def sell(context, securities):
    for sec in securities:
        order_target_percent(sec, 0)
        if sec in context.purchased_sec:
            context.day_trade_tracker[-1] += 1
            context.traded.append(sec)