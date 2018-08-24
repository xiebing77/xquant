#!/usr/bin/python
"""各种指标"""
import numpy as np
import pandas as pd


def np_kdj(klines, N=9):
    M1 = 3
    M2 = 3
    datelen = len(klines)

    arr = np.array(klines)
    kdjarr = []
    for i in range(datelen):
        if i - N < 0:
            b = 0
        else:
            b = i - N + 1
        rsvarr = arr[b : i + 1]

        close = float(rsvarr[-1, 4])
        period_higns = [float(x) for x in rsvarr[:, 2]]
        period_lows = [float(x) for x in rsvarr[:, 3]]
        period_hign = max(period_higns)
        period_low = min(period_lows)

        rsv = (close - period_low) / (period_hign - period_low) * 100
        if i == 0:
            k = rsv
            d = rsv
        else:
            k = 1 / float(M1) * rsv + (float(M1) - 1) / M1 * float(kdjarr[-1][1])
            d = 1 / float(M2) * k + (float(M2) - 1) / M2 * float(kdjarr[-1][2])
        j = 3 * k - 2 * d
        kdjarr.append(list((rsv, k, d, j)))

    #print(kdjarr)
    return kdjarr


def pd_kdj(klines, columns, period=9, ksgn="close"):
    """kdj"""
    klines_df = pd.DataFrame(klines, columns=columns)

    low_list = pd.Series(klines_df["low"]).rolling(period).min()
    low_list.fillna(value=pd.Series(klines_df["low"]).expanding().min(), inplace=True)

    high_list = pd.Series(klines_df["high"]).rolling(period).max()
    high_list.fillna(value=pd.Series(klines_df["high"]).expanding().max(), inplace=True)

    ksgn_list = klines_df[ksgn].apply(pd.to_numeric)
    rsv = (ksgn_list - low_list) / (high_list - low_list) * 100
    k = rsv.ewm(com=2, adjust=False).mean()  # pd.ewma(rsv,com=2)
    d = k.ewm(com=2).mean() # pd.ewma(klines['kdj_k'],com=2)，注意需要加adjust=False才能和np_kdj的结果相同，要不有些许差别
    j = 3.0 * k - 2.0 * d

    #klines_df["rsv"] = rsv
    #klines_df["k"] = k
    #klines_df["d"] = d
    #print(klines_df)
    return k, d, j


def calc_macd(klines, fastperiod=12, slowperiod=26, signalperiod=9):
    """macd"""
    fast_ema = klines["close"].ewm(span=fastperiod).mean()
    slow_ema = klines["close"].ewm(span=slowperiod).mean()

    klines["12ema"] = fast_ema
    klines["26ema"] = slow_ema
    klines["macd dif"] = fast_ema - slow_ema
    klines["macd dea"] = klines["macd dif"].ewm(span=signalperiod).mean()
