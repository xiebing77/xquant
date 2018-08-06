#!/usr/bin/python
"""各种指标"""
import pandas as pd


def calc_kdj(klines, period=9, ksgn="close"):
    """kdj"""

    low_list = pd.Series(klines["low"]).rolling(period).min()
    low_list.fillna(value=pd.Series(klines["low"]).expanding().min(), inplace=True)

    high_list = pd.Series(klines["high"]).rolling(period).max()
    high_list.fillna(value=pd.Series(klines["high"]).expanding().max(), inplace=True)

    ksgn_list = klines[ksgn].apply(pd.to_numeric)
    rsv = (ksgn_list - low_list) / (high_list - low_list) * 100
    klines["RSV"] = rsv
    klines["kdj_k"] = rsv.ewm(com=2, adjust=False).mean()  # pd.ewma(rsv,com=2)
    klines["kdj_d"] = klines["kdj_k"].ewm(com=2).mean()  # pd.ewma(klines['kdj_k'],com=2)
    klines["kdj_j"] = 3.0 * klines["kdj_k"] - 2.0 * klines["kdj_d"]


def calc_macd(klines, fastperiod=12, slowperiod=26, signalperiod=9):
    """macd"""
    fast_ema = klines["close"].ewm(span=fastperiod).mean()
    slow_ema = klines["close"].ewm(span=slowperiod).mean()

    klines["12ema"] = fast_ema
    klines["26ema"] = slow_ema
    klines["macd dif"] = fast_ema - slow_ema
    klines["macd dea"] = klines["macd dif"].ewm(span=signalperiod).mean()
