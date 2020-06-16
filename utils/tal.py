#!/usr/bin/python
"""各种指标"""
import talib
import utils.tools as ts

def STOCHRSI(klines_df, timeperiod=14):
    fastk, fastd = talib.STOCHRSI(klines_df["close"], timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)
    return [ts.reserve_float(a, 6) for a in fastk], [ts.reserve_float(a, 6) for a in fastd]

def APO(klines_df, timeperiod=14):
    real = talib.APO(klines_df["close"], fastperiod=12, slowperiod=26, matype=0)
    return [ts.reserve_float(a, 6) for a in real]

def DX(klines_df, timeperiod=14):
    real = talib.DX(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
    return [ts.reserve_float(a, 6) for a in real]

def ADX(klines_df, timeperiod=14):
    real = talib.ADX(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
    return [ts.reserve_float(a, 6) for a in real]

def ADXR(klines_df, timeperiod=14):
    real = talib.ADXR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
    return [ts.reserve_float(a, 6) for a in real]

def CCI(klines_df, timeperiod=14):
    real = talib.CCI(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
    return [ts.reserve_float(a, 6) for a in real]

def MFI(klines_df, timeperiod=14):
    real = talib.MFI(klines_df["high"], klines_df["low"], klines_df["close"], klines_df["volume"], timeperiod=14)
    return [ts.reserve_float(a, 6) for a in real]

def PLUS_DM(klines_df, timeperiod=14):
    real = talib.PLUS_DM(klines_df["high"], klines_df["low"], timeperiod=14)
    return [ts.reserve_float(a, 6) for a in real]

def MINUS_DM(klines_df, timeperiod=14):
    real = talib.MINUS_DM(klines_df["high"], klines_df["low"], timeperiod=14)
    return [ts.reserve_float(a, 6) for a in real]

def WILLR(klines_df, timeperiod=14):
    real = talib.WILLR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
    return [ts.reserve_float(a, 6) for a in real]
