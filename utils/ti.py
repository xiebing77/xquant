#!/usr/bin/python
"""json接口 技术指标"""
from .indicator import py_rsi_ema, py_rsi_ua
from datetime import datetime


def print_kl_info(key, kl):
    pass
    #print("%12s:  "%key, datetime.fromtimestamp(kl["open_time"]/1000), ""*10, datetime.fromtimestamp(kl["close_time"]/1000) )



##### EMA ####################################################################
def get_ema_key(period):
    return "ema_%s" % (period)

def calc_ema(kls, vkey, key, k, idx):
    kls[idx][key] = float(kls[idx][vkey]) * k + kls[idx-1][key] * (1 - k)

def EMA(kls, vkey, period):
    k = 2 / (float(period) + 1)
    key = get_ema_key(period)

    if key in kls[-2]:
        calc_ema(kls, vkey, key, k, -1)
        return key

    if key in kls[-3]:
        calc_ema(kls, vkey, key, k, -2)
        calc_ema(kls, vkey, key, k, -1)
        return key

    if len(kls) < period:
        return

    print_kl_info(key, kls[-1])

    vs_init = [ float(kl[vkey]) for kl in kls[:period]]
    kls[period-1][key] = sum(vs_init) / period

    for i in range(period, len(kls)):
        calc_ema(kls, vkey, key, k, i)
    return key


##### BIAS ####################################################################
def get_bias_key(period_s, period_l):
    return "bias_%s_%s" % (period_s, period_l)

def calc_bias(kl, eskey, elkey, key):
    kl[key] = (kl[eskey] - kl[elkey]) / kl[elkey]

def BIAS(kls, period_s, period_l):
    key = get_bias_key(period_s, period_l)
    eskey = get_ema_key(period_s)
    elkey = get_ema_key(period_l)

    kl = kls[-1]
    if key in kls[-2] and eskey in kl and elkey in kl:
        calc_bias(kls[-1], eskey, elkey, key)
        return key

    kl = kls[-2]
    if key in kls[-3] and eskey in kl and elkey in kl:
        calc_bias(kls[-2], eskey, elkey, key)
        calc_bias(kls[-1], eskey, elkey, key)
        return key

    if len(kls) < period_l:
        return

    print_kl_info(key, kls[-1])

    for kl in kls:
        if eskey in kl and elkey in kl:
            calc_bias(kl, eskey, elkey, key)
    return key


##### RSI ####################################################################
def get_rsi_key(period):
    return "rsi_%s" % (period)

def get_rsi_ema_u_key(period):
    return "%s_ema_u" % get_rsi_key(period)

def get_rsi_ema_d_key(period):
    return "%s_ema_d" % get_rsi_key(period)

def calc_rsi(kls, vkey, ukey, dkey, key, period, idx):
    u, d = py_rsi_ua(float(kls[idx-1][vkey]), float(kls[idx][vkey]))
    kls[idx][ukey] = ema_u = py_rsi_ema(kls[idx-1][ukey], u, period)
    kls[idx][dkey] = ema_d = py_rsi_ema(kls[idx-1][dkey], d, period)
    kls[idx][key] = 100 * (ema_u / (ema_u + ema_d))

def RSI(kls, vkey, period=14):
    key = get_rsi_key(period)
    ukey = get_rsi_ema_u_key(period)
    dkey = get_rsi_ema_d_key(period)

    if key in kls[-2]:
        calc_rsi(kls, vkey, ukey, dkey, key, period, -1)
        return key

    if key in kls[-3]:
        calc_rsi(kls, vkey, ukey, dkey, key, period, -2)
        calc_rsi(kls, vkey, ukey, dkey, key, period, -1)
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
        calc_rsi(kls, vkey, ukey, dkey, key, period, i)
    return key

##### STEP ####################################################################

def get_above_step(kls, vkey, v):
    for idx in range(-1, -len(kls)-1, -1):
        kl = kls[idx]
        if (vkey not in kl) or kl[vkey] >= v:
            return -1-idx
    return len(kls)

def get_below_step(kls, vkey, v):
    for idx in range(-1, -len(kls)-1, -1):
        kl = kls[idx]
        if (vkey not in kl) or  kl[vkey] <= v:
            return -1-idx
    return len(kls)

