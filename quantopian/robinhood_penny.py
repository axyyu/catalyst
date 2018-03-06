#Quantopian
from quantopian.pipeline import Pipeline, CustomFactor
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline.factors import Latest
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.data import Fundamentals
from quantopian.pipeline.data import morningstar as ms
from quantopian.pipeline.classifiers.morningstar import Sector
from quantopian.pipeline.factors import SimpleMovingAverage, ExponentialWeightedMovingAverage, AverageDollarVolume
from quantopian.pipeline.filters import Q1500US, Q500US

#Sentiment Analysis from StockTwits and Twitter
from quantopian.pipeline.data.psychsignal import aggregated_twitter_withretweets_stocktwits as st

#Other
import numpy as np
import math
import random

def initialize(context):
    context.price_cap = 10
    context.max_clip = 50
    context.purchased = {}
    
    #Hyperparameters
    context.per_gain = 1.5
    context.money_mult = 1.5
    context.weight_random = 10
    context.random_size = 50
    # context.percent_money_each = .1
    
    context.metric_weight = 1 # Metric made from company values
    context.avg_weight = 1 # Ratios
    context.avg_diff_weight = 1 # Ratio differences
    context.sent_a_weight = 1 # Ratio differences

    #Robinhood Setup
    set_long_only()
    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))
    context.day_trade_protection = True
    context.day_trade_tracker = [0 for a in range(5)] # Chronologically left -> right
    
    attach_pipeline(make_pipeline(context), 'my_pipeline')
    schedule_function(trade, date_rules.every_day(), time_rules.market_open())
    schedule_function(end_of_day, date_rules.every_day(), time_rules.market_close())

def make_pipeline(context):
    metric = Metric()
    ratios = Ratios()
    
    #Fields
    yesterday_close = USEquityPricing.close.latest
    current_volume = USEquityPricing.volume.latest
    adv_12 = AverageDollarVolume(window_length=12)
    adv_24 = AverageDollarVolume(window_length=24)
    adv_ratio = adv_24/adv_12
    exchange_id = ms.share_class_reference.exchange_id.latest
    
    #Sentiment Analysis
    bull_msg = st.bull_scored_messages.latest
    bull_inten = st.bullish_intensity.latest
    bear_msg = st.bear_scored_messages.latest
    bear_inten = st.bearish_intensity.latest
    total_msg = st.total_scanned_messages
    
    net_inten = st.bull_minus_bear
    net_ratio = (bull_msg - bear_msg) / total_msg
    
    sent_weight = SentimentWeight() #(( ( total_msg / 6 ) ** 2 ) - 10 ) / ( 10 * ( total_msg / 6 ) ** 2 + 10 ) +1
    
    #Moving Averages
    sma_12 = SimpleMovingAverage(inputs = [USEquityPricing.close], window_length=12)
    sma_24 = SimpleMovingAverage(inputs = [USEquityPricing.close], window_length=24)
    ema_12 = ExponentialWeightedMovingAverage(inputs = [USEquityPricing.close], window_length=12, decay_rate=.5)
    ema_24 = ExponentialWeightedMovingAverage(inputs = [USEquityPricing.close], window_length=24, decay_rate=.5)
    
    sma_ratio = sma_12/sma_24
    ema_ratio = ema_12/ema_24
    ratio_12 = ema_12/sma_12
    ratio_24 = ema_24/sma_24
    
    #Filters
    price_filter = (yesterday_close < 10)
    exchange_filter = exchange_id.startswith('NYS') | exchange_id.startswith('NAS') | exchange_id.startswith('ASE')
    volume_filter = current_volume >= 500000
    
    req_filters = price_filter & exchange_filter & volume_filter
    
    sma_filters = (sma_12 > 0) & (sma_24 > 0) & ((ema_12 >= sma_12) | (ema_24 >= sma_24))
    
    eval_metric = metric + 1/ratios
    eval_avg_diff = np.clip( (ema_12 - sma_12)/ema_12 + (ema_24 - sma_24)/ema_24, -context.max_clip, context.max_clip)
    eval_avg = np.clip( sma_ratio + ema_ratio + ratio_12 + ratio_24 , -context.max_clip, context.max_clip)
    eval_sent = np.clip( sent_weight * net_ratio * net_inten , -context.max_clip, context.max_clip)
    
    evaluation = eval_metric*context.metric_weight + eval_avg*context.avg_weight + eval_avg_diff*context.avg_diff_weight + eval_sent*context.sent_a_weight
    
    pipe = Pipeline(
        screen =  req_filters & sma_filters,
        columns = {
            'close': yesterday_close,
            'exchange_id':exchange_id,
            'eval': evaluation,
            'adv_ratio': adv_ratio,
            'sma_ratio': sma_ratio,
            'ema_ratio': ema_ratio,
            'ratio_12': ratio_12,
            'ratio_24': ratio_24,
        }
    )
    return pipe    
 
def before_trading_start(context, data):
    context.orders = {}
    
    context.output = pipeline_output('my_pipeline')
    context.security_list = context.output.index

    # Shift Pattern Day Trader
    context.day_trade_tracker.pop()
    context.day_trade_tracker.insert(0, 0)
    
    record(res=len(context.security_list))
    
def weighted_random(context,data):
    secs = []
    for sec in context.security_list:
        num = math.floor( context.weight_random - ( context.output['eval'][sec] / context.max_clip ) )
        if np.isinf(num) or np.isnan(num):
            num = 0
        secs += [sec] * int(num)
        
    secs = random.sample(secs, context.random_size)
    return secs
    
def trade(context, data):
    """ Every Day """
    remaining_cash = context.portfolio.cash
    # securities = context.output.sort_values('eval')
    securities = weighted_random(context,data)
    
    # money_per_stock = remaining_cash*1.5 / len(securities.index)
    money_per_stock = remaining_cash / context.random_size
    
    # for s in range(len(securities.index)):
    for sec in securities:
        if context.day_trade_protection and (pattern_day_trader(context) and context.portfolio.portfolio_value < 25000):
            return

        sec_price = data.current(sec, 'low')
        amt = math.floor(money_per_stock/sec_price)

        remaining_cash -= money_per_stock
        if amt > 0 and remaining_cash > 0 and data.can_trade(sec):
            context.orders[sec] = (5, order(sec, amt, style=LimitOrder(sec_price) ) )
            context.purchased[sec] = context.output['eval'][sec]
        
def handle_data(context,data):
    """ Every Minute """
    for sec,pos in context.portfolio.positions.iteritems():
        cur_info = data.current(sec, ['price','open','high','low'])
        hist_vol = data.history(sec, 'volume', 2, "1d")
        pur_price = pos.cost_basis
        
        hl_ratio = ( cur_info['high'] - cur_info['low'] ) / cur_info['low']
        p_ratio = ( cur_info['price'] - pur_price ) / pur_price
        o_ratio = ( cur_info['open'] - pur_price ) / pur_price
        v_ratio = ( hist_vol[1] - hist_vol[0] ) / hist_vol[0]
        
        old_eval = context.purchased[sec]
        new_eval = float("inf")

        try:
            new_eval = context.output['eval'][sec]
        except:
            pass
        
        m = (hl_ratio + p_ratio + o_ratio + v_ratio) / 4
        
        if m < 0 and p_ratio < 0:
            order_sec(context, 1, sec, pos.amount, cur_info['open'])
        elif m < 0:
            order_sec(context, 2, sec, pos.amount, pur_price)
        elif new_eval < old_eval:
            order_sec(context, 3, sec, pos.amount, pur_price*context.per_gain)
        else:
            pass
            # order_sec(context, 4, sec, pos.amount, cur_info['price']*context.per_gain)
            
def order_sec(context, priority, sec, amount, price):
    if sec in context.orders:
        order_status = get_order( context.orders[sec][1] )

        if order_status == 0:
            # if priority <= context.orders[sec][0]:
            cancel_order(context.orders[sec][1])
            context.orders[sec] = (priority, order(sec, -amount, style=LimitOrder(price) ) )
        elif order_status == 1:
            context.day_trade_tracker[-1] += 1
    else:
        context.orders[sec] = (priority, order(sec, -amount, style=LimitOrder(price) ) )

def end_of_day(context, data):
    for S in get_open_orders():  
       for O in get_open_orders(S):  
          cancel_order(O)

def pattern_day_trader(context):
    if sum([t for t in context.day_trade_tracker]) >= 3:
        return True
    return False

"""
Custom Factors
"""
class SentimentWeight(CustomFactor):
    inputs = [st.total_scanned_messages]
    window_length = 1

    def compute(self, today, assets, out, total_msg):
        out[:] = np.clip( (( ( np.nan_to_num(total_msg) / 6 ) ** 2 ) - 10 ) / ( 10 * ( np.nan_to_num(total_msg) / 6 ) ** 2 + 10 ) +1, -50, 50)
        
class Metric(CustomFactor):
    inputs = [Fundamentals.current_ratio, Fundamentals.quick_ratio, Fundamentals.interest_coverage]
    window_length = 1

    def compute(self, today, assets, out, current_ratio, quick_ratio, interest_coverage):
        out[:] = np.clip( np.nan_to_num(current_ratio) + np.nan_to_num(quick_ratio) + np.nan_to_num(interest_coverage), -50, 50)
        
class Ratios(CustomFactor):  
    inputs = [Fundamentals.peg_ratio, Fundamentals.pe_ratio, Fundamentals.ps_ratio, Fundamentals.pcf_ratio]
    window_length = 1

    def compute(self, today, assets, out, peg_ratio, pe_ratio, ps_ratio, pcf_ratio):
        out[:] = np.clip( np.nan_to_num(peg_ratio) + np.nan_to_num(pe_ratio) + np.nan_to_num(ps_ratio) + np.nan_to_num(pcf_ratio), -50, 50)