#!/usr/bin/python
"""json接口 技术指标"""
from .indicator import py_rsi_ema, py_rsi_ua
from datetime import datetime

def print_kl_info(key, kl):
    pass
    #print("%12s:  "%key, datetime.fromtimestamp(kl["open_time"]/1000), ""*10, datetime.fromtimestamp(kl["close_time"]/1000) )

def get_ema_key(period):
    return "ema_%s" % (period)

def EMA(kls, vkey, period):
    k = 2 / (float(period) + 1)
    key = get_ema_key(period)

    if key in kls[-2]:
        kls[-1][key] = float(kls[-1][vkey]) * k + kls[-2][key] * (1 - k)
        return key

    if key in kls[-3]:
        kls[-2][key] = float(kls[-2][vkey]) * k + kls[-3][key] * (1 - k)
        kls[-1][key] = float(kls[-1][vkey]) * k + kls[-2][key] * (1 - k)
        return key

    if len(kls) < period:
        return

    print_kl_info(key, kls[-1])

    vs_init = [ float(kl[vkey]) for kl in kls[:period]]
    kls[period-1][key] = sum(vs_init) / period

    for i in range(period, len(kls)):
        kls[i][key] = float(kls[i][vkey]) * k + kls[i-1][key] * (1 - k)
    return key

def get_bias_key(period_s, period_l):
    return "bias_%s_%s" % (period_s, period_l)

def BIAS(kls, period_s, period_l):
    key = get_bias_key(period_s, period_l)
    eskey = get_ema_key(period_s)
    elkey = get_ema_key(period_l)

    kl = kls[-1]
    if key in kls[-2] and eskey in kl and elkey in kl:
        kl[key] = (kl[eskey] - kl[elkey]) / kl[elkey]
        return key

    kl = kls[-2]
    if key in kls[-3] and eskey in kl and elkey in kl:
        kl[key] = (kl[eskey] - kl[elkey]) / kl[elkey]
        kl = kls[-1]
        kl[key] = (kl[eskey] - kl[elkey]) / kl[elkey]
        return key

    if len(kls) < period_l:
        return

    print_kl_info(key, kls[-1])

    for kl in kls:
        if eskey in kl and elkey in kl:
            kl[key] = (kl[eskey] - kl[elkey]) / kl[elkey]
    return key


def get_rsi_key(period):
    return "rsi_%s" % (period)

def get_rsi_ema_u_key(period):
    return "%s_ema_u" % get_rsi_key(period)

def get_rsi_ema_d_key(period):
    return "%s_ema_d" % get_rsi_key(period)

def RSI(kls, vkey, period=14):
    key = get_rsi_key(period)
    ukey = get_rsi_ema_u_key(period)
    dkey = get_rsi_ema_d_key(period)

    if key in kls[-2]:
        u, d = py_rsi_ua(float(kls[-2][vkey]), float(kls[-1][vkey]))
        kls[-1][ukey] = ema_u = py_rsi_ema(kls[-2][ukey], u, period)
        kls[-1][dkey] = ema_d = py_rsi_ema(kls[-2][dkey], d, period)
        kls[-1][key] = 100 * (ema_u / (ema_u + ema_d))
        return key

    if key in kls[-3]:
        u, d = py_rsi_ua(float(kls[-3][vkey]), float(kls[-2][vkey]))
        kls[-2][ukey] = ema_u = py_rsi_ema(kls[-3][ukey], u, period)
        kls[-2][dkey] = ema_d = py_rsi_ema(kls[-3][dkey], d, period)
        kls[-2][key] = 100 * (ema_u / (ema_u + ema_d))

        u, d = py_rsi_ua(float(kls[-2][vkey]), float(kls[-1][vkey]))
        kls[-1][ukey] = ema_u = py_rsi_ema(kls[-2][ukey], u, period)
        kls[-1][dkey] = ema_d = py_rsi_ema(kls[-2][dkey], d, period)
        kls[-1][key] = 100 * (ema_u / (ema_u + ema_d))
        return key

    if len(kls) < period:
        return

    print_kl_info(key, kls[-1])

    us = []
    ds = []
    for i in range(1, period):
        u, d = py_rsi_ua(float(kls[i-1][vkey]), float(kls[i][vkey]))
        us.append(u)
        ds.append(d)
    kls[i][ukey] = sum(us) / period
    kls[i][dkey] = sum(ds) / period
    for i in range(period, len(kls)):
        u, d = py_rsi_ua(float(kls[i-1][vkey]), float(kls[i][vkey]))
        kls[i][ukey] = ema_u = py_rsi_ema(kls[i-1][ukey], u, period)
        kls[i][dkey] = ema_d = py_rsi_ema(kls[i-1][dkey], d, period)
        kls[i][key] = 100 * (ema_u / (ema_u + ema_d))
    return key


