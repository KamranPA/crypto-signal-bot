# strategy/fusion.py

def generate_signal(row):
    rsi = row['rsi']
    macd = row['macd']
    macd_signal = row['macd_signal']
    price = row['close']
    bb_high = row['bb_high']
    bb_low = row['bb_low']

    # Long Signal
    if (macd > macd_signal and 
        rsi < 60 and 
        price < bb_low):
        return 1

    # Short Signal
    elif (macd < macd_signal and 
          rsi > 40 and 
          price > bb_high):
        return -1

    return 0
