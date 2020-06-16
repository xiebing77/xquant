#!/usr/bin/python
"""各种指标"""
import numpy as np
import pandas as pd
import talib

def py_ma(klines, index, period):
    """
    vs = []
    for kline in klines[-period:]:
        vs.append(float(kline[index]))
    """
    vs = [ float(kline[index]) for kline in klines[-period:]]

    return sum(vs)/len(vs)

def py_mas(klines, index, period):
    arr = []
    vs = []
    for kline in klines:
        if len(vs) >= period:
            vs.pop(0)
        vs.append(float(kline[index]))
        arr.append(sum(vs)/len(vs))

    return arr

def py_emas(klines, index, period):
    arr = []

    for i in range(period):
        if i==0:
            ema = float(klines[0][index])
        elif i >= len(klines):
            return arr
        else:
            k = 2 / (i + 2)
            v = float(klines[i][index])
            ema = v * k + ema_y * (1 - k)

        arr.append(ema)
        ema_y = ema


    k = 2 / (period + 1)
    for kline in klines[period:]:
        v = float(kline[index])
        ema = v * k + ema_y * (1 - k)

        arr.append(ema)
        ema_y = ema

    return arr


def py_json_kdj(klines, period=9):
    M1 = 3
    M2 = 3

    kline = klines[0]
    close = float(kline["close"])
    high = float(kline["high"])
    low = float(kline["low"])
    if high > low:
        rsv = (close - low) / (high - low) * 100
    else:
        rsv = 0
    kline["rsv"] = kline["k"] = kline["d"] = kline["j"] = rsv
    klines[0] = kline

    pre_kline = kline
    highs = [high]
    lows = [low]
    for idx, kline in enumerate(klines[1:]):
        if len(highs) >= period:
            highs.pop(0)
            lows.pop(0)

        highs.append(float(kline["high"]))
        lows.append(float(kline["low"]))
        close = float(kline["close"])
        min_low = min(lows)
        rsv = (close - min_low) / (max(highs) - min_low) * 100

        k = 1 / M1 * rsv + (M1 - 1) / M1 * pre_kline["k"]
        d = 1 / M2 * k + (M2 - 1) / M2 * pre_kline["d"]
        j = 3 * k - 2 * d

        kline["rsv"] = rsv
        kline["k"] = k
        kline["d"] = d
        kline["j"] = j

        klines[idx] = kline
        pre_kline = kline

    return klines

def py_kdj(klines, highindex, lowindex, closeindex, period=9):
    M1 = 3
    M2 = 3

    kdj_arr = []

    kline = klines[0]
    close = float(kline[closeindex])
    high = float(kline[highindex])
    low = float(kline[lowindex])
    if high > low:
        rsv = (close - low) / (high - low) * 100
    else:
        rsv = 0
    kdj_arr.append(list((rsv, rsv, rsv, rsv)))

    highs = [high]
    lows = [low]
    for kline in klines[1:]:
        if len(highs) >= period:
            highs.pop(0)
            lows.pop(0)

        highs.append(float(kline[highindex]))
        lows.append(float(kline[lowindex]))
        close = float(kline[closeindex])
        min_low = min(lows)
        rsv = (close - min_low) / (max(highs) - min_low) * 100

        k = 1 / M1 * rsv + (M1 - 1) / M1 * kdj_arr[-1][1]
        d = 1 / M2 * k + (M2 - 1) / M2 * kdj_arr[-1][2]
        j = 3 * k - 2 * d
        kdj_arr.append(list((rsv, k, d, j)))

    #print(kdjarr)
    return kdj_arr


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


def pd_kdj(klines_df, period=9, ksgn="close"):
    """kdj"""

    low_list = pd.Series(klines_df["low"]).rolling(period).min()
    low_list.fillna(value=pd.Series(klines_df["low"]).expanding().min(), inplace=True)

    high_list = pd.Series(klines_df["high"]).rolling(period).max()
    high_list.fillna(value=pd.Series(klines_df["high"]).expanding().max(), inplace=True)

    ksgn_list = klines_df[ksgn].apply(pd.to_numeric)
    rsv = (ksgn_list - low_list) / (high_list - low_list) * 100
    k = rsv.ewm(com=2, adjust=False).mean()  # pd.ewma(rsv,com=2)
    d = k.ewm(com=2, adjust=False).mean() # pd.ewma(klines['kdj_k'],com=2)，注意需要加adjust=False才能和np_kdj的结果相同，要不有些许差别
    j = 3.0 * k - 2.0 * d

    #klines_df["rsv"] = rsv
    #klines_df["k"] = k
    #klines_df["d"] = d
    #print(klines_df)
    return k, d, j


def ta_kdj(klines_df, period=9, ksgn="close"):
    kd = talib.STOCH(high=klines_df["high"], low=klines_df["low"], close=klines_df[ksgn],
        fastk_period=period, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)

    return kd

def py_macd(klines, closeindex, fastperiod=12, slowperiod=26, signalperiod=9):
    arr = []

    close = float(klines[0][closeindex])
    arr.append(list((close, close, 0, 0, close)))

    for kline in klines[1:]:
        close = float(kline[closeindex])

        fast_ema = close * (2/(fastperiod+1)) + arr[-1][0] * ((fastperiod-1)/(fastperiod+1))
        slow_ema = close * (2/(slowperiod+1)) + arr[-1][1] * ((slowperiod-1)/(slowperiod+1))

        dif = fast_ema - slow_ema
        dea = dif * (2/(signalperiod+1)) + arr[-1][3] * ((signalperiod-1)/(signalperiod+1))

        arr.append(list((fast_ema, slow_ema, dif, dea, close)))

    #print(arr)
    return arr


def pd_macd(klines_df, fastperiod=12, slowperiod=26, signalperiod=9):
    """macd"""
    fast_ema = klines_df["close"].ewm(span=fastperiod, adjust=False).mean()
    slow_ema = klines_df["close"].ewm(span=slowperiod, adjust=False).mean()

    klines_df["12ema"] = fast_ema
    klines_df["26ema"] = slow_ema
    klines_df["dif"] = fast_ema - slow_ema
    klines_df["dea"] = klines_df["dif"].ewm(span=signalperiod, adjust=False).mean()
    klines_df["macd"] = klines_df["dif"] - klines_df["dea"]

    #print(klines_df)
    return klines_df

def py_rsi2(klines, closeindex, period=14):
    closes = [kline[closeindex] for kline in klines[-period:]]
    ur = []
    dr = []
    pre_close = float(closes[0])
    for close in closes[1:]:
        close = float(close)
        r = close / pre_close
        pre_close = close
        if r > 1:
            ur.append(r-1)
        else:
            dr.append(1-r)
    if ur:
        ua = sum(ur)/len(ur)
    else:
        ua = 0
    if dr:
        da = sum(dr)/len(dr)
    else:
        da = 0
    return 100*ua/(ua+da)

def py_rsis2(klines, closeindex, period=14):
    arr = []
    for i in range(2, len(klines)):
        rsi = py_rsi2(klines[:i], closeindex, period)
        arr.append(rsi)
    return arr

def py_rsi(klines, closeindex, period=14):
    closes = [kline[closeindex] for kline in klines[-period:]]
    us = []
    ds = []
    pre_close = float(closes[0])
    for close in closes[1:]:
        close = float(close)
        if close > pre_close:
            us.append(close-pre_close)
        else:
            ds.append(pre_close-close)
        pre_close = close
    if us:
        ua = sum(us)/len(us)
    else:
        ua = 0
    if ds:
        da = sum(ds)/len(ds)
    else:
        da = 0
    return 100*ua/(ua+da)
    #rs = ua / da
    #return 100*(1-1/(1+rs))

def py_rsis(klines, closeindex, period=14):
    arr = []
    for i in range(2, len(klines)):
        rsi = py_rsi(klines[:i], closeindex, period)
        arr.append(rsi)
    return arr

def py_hl(klines, highindex, lowindex, opentimeindex, period):

    max_high = float(klines[-1][highindex])
    min_low = float(klines[-1][lowindex])
    high_time = low_time = klines[-1][opentimeindex]
    for kline in klines[-period:-1]:
        if max_high < float(kline[highindex]):
            max_high = float(kline[highindex])
            high_time = kline[opentimeindex]
        if min_low > float(kline[lowindex]):
            min_low = float(kline[lowindex])
            low_time = kline[opentimeindex]

    return max_high, high_time, min_low, low_time

def py_wr(klines, highindex, lowindex, closeindex, period=14):

    close = float(klines[-1][closeindex])
    max_high = float(klines[-1][highindex])
    min_low = float(klines[-1][lowindex])
    for kline in klines[-period:-1]:
        if max_high < float(kline[highindex]):
            max_high = float(kline[highindex])
        if min_low > float(kline[lowindex]):
            min_low = float(kline[lowindex])

    wr = (max_high - close) / (max_high - min_low) * 100
    #print("py_wr(%g, %g, %g, %g)" % (max_high, min_low, close, wr))
    return wr

def py_wrs(klines, highindex, lowindex, closeindex, period=14):
    arr = []
    highs = []
    lows = []
    for kline in klines:
        if len(highs) >= period:
            highs.pop(0)
            lows.pop(0)
        highs.append(float(kline[highindex]))
        lows.append(float(kline[lowindex]))

        max_high = max(highs)
        min_low = min(lows)
        wr = (max_high - float(kline[closeindex])) / (max_high - min_low) * 100
        arr.append(wr)

    #print(arr)
    return arr

def py_ad(k, highindex, lowindex, openindex, closeindex, volumeindex):
    m = float(k[highindex]) - float(k[lowindex])
    if m==0:
        return 0

    l = float(k[volumeindex])
    ad = (float(k[closeindex]) - float(k[openindex])) / m * l
    return ad

def py_ads(klines, highindex, lowindex, openindex, closeindex, volumeindex):
    ads = []
    for k in klines:
        ads.append(py_ad(k, highindex, lowindex, openindex, closeindex, volumeindex))
    return ads
