# First Algorithm

## Requirements

 - Sklearn
 - Tensorflow/PyTorch

## Important Factors

### Data
 - List of viable stocks (reddit? twitter? or just filter through entire NASDAQ ticker list)

### Input
 - Sentiment
    - News
    - Twitter
    - Reddit

 - Stock Data
    - Price (open, close, current)
    - Volume (open, close, current)
    - Liquidity Ratios #best if these > 1, but should be >0.5 to buy
        - current ratio # greater the better
        - quick ratio # greater the better, better than current ratio
        - cash conversion cycle #less the better
    - Leverage Ratios #needs to be >2
        - interest coverage #greater the better
    - Performance ratios #look at trend, pass in array
        - gross profit
        - normalized net profit margin
        - assets turnover #higher the better
        - sales per employee #higher the better
    
    - Valuation Ratios
        - peg ratio  #Lower, under 1
        - pe ratio #lower pe_ratio
    
        - only if pe & peg < 0 
            - ps ratio #Lower is better, less than 2
            - pcf ratio  #Lower is better, low single digits

    - Security Ratios
        - ev to ebitda #Important
        - fcf ratio
        
        - forward pe ratio
        - pe ratio #lower pe ratio
        
        - payout ratio est #Lower is better
        - pb ratio #Lower is better, means undervalued
        - pcf ratio  #a ratio in the low single digits may indicate the stock is undervalued, while a higher ratio may suggest potential overvaluation
        
        - peg ratio  #Lower, under 1
        - ps ratio #Lower is better
    

 - Evaluations
    - 10 day SMA for company
    - 10 day SMA for sector
    - 30 day EMA for company
    - 30 day EMA for sector
    - 200 day SMA for company
    - 200 day SMA for sector
    - Check 52-wk high
    - Mark all cross over points
    - 50-day moving average
    - Bull Power = Daily High - n-period EMA 
    - Bear Power = Daily Low - n-period EMA



### Output
 - Classifier (buy, 1
                constant, 0
                sell, -1)

### Trading
 - Don't trade more than 10% of daily volume

## Neural Network
1. Use MinMaxScaler
2. Use ReLU activation
3. Consider MSE (Mean Squared Error)
4. Consider Adam Optimizer function