#!/usr/bin/python
'''各种指标'''
import pandas as pd


def calc_kdj(kbar, period=9, ksgn="close"):
    '''kdj'''

    low_list = pd.Series(kbar["low"]).rolling(period).min()
    low_list.fillna(value=pd.Series(kbar["low"]).expanding().min(), inplace=True)

    high_list = pd.Series(kbar["high"]).rolling(period).max()
    high_list.fillna(value=pd.Series(kbar["high"]).expanding().max(), inplace=True)

    ksgn_list = kbar[ksgn].apply(pd.to_numeric)
    rsv = (ksgn_list - low_list) / (high_list - low_list) * 100
    kbar["RSV"] = rsv
    kbar["kdj_k"] = rsv.ewm(com=2, adjust=False).mean()  # pd.ewma(rsv,com=2)
    kbar["kdj_d"] = kbar["kdj_k"].ewm(com=2).mean()  # pd.ewma(kbar['kdj_k'],com=2)
    kbar["kdj_j"] = 3.0 * kbar["kdj_k"] - 2.0 * kbar["kdj_d"]


def calc_macd(kbar, fastperiod=12, slowperiod=26, signalperiod=9):
    '''macd'''
    fast_ema = kbar["close"].ewm(span=fastperiod).mean()
    slow_ema = kbar["close"].ewm(span=slowperiod).mean()

    kbar["12ema"] = fast_ema
    kbar["26ema"] = slow_ema
    kbar["macd dif"] = fast_ema - slow_ema
    kbar["macd dea"] = kbar["macd dif"].ewm(span=signalperiod).mean()
