#!/usr/bin/python
"""json接口 技术指标"""
from .indicator import py_rsi_ema, py_rsi_ua
from datetime import datetime


def print_kl_info(key, kl):
    pass
    #print("%12s:  "%key, datetime.fromtimestamp(kl["open_time"]/1000), ""*10, datetime.fromtimestamp(kl["close_time"]/1000) )



##### EMA ####################################################################
def get_ema_key(vkey, period):
    return "ema_%s_%s" % (vkey, period)

def calc_ema(kls, vkey, key, k, idx):
    kls[idx][key] = float(kls[idx][vkey]) * k + kls[idx-1][key] * (1 - k)

def get_ema_k(period):
    return 2 / (float(period) + 1)

def EMA(kls, vkey, period):
    k = get_ema_k(period)
    key = get_ema_key(vkey, period)

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

    for start_idx in range(0, len(kls)):
        if vkey in kls[start_idx]:
            break
    vs_init = [ float(kl[vkey]) for kl in kls[start_idx:start_idx+period]]
    kls[start_idx+period-1][key] = sum(vs_init) / period

    for i in range(start_idx+period, len(kls)):
        calc_ema(kls, vkey, key, k, i)
    return key


##### BIAS ####################################################################
def get_bias_key(period_s, period_l):
    return "bias_%s_%s" % (period_s, period_l)

def calc_bias(kl, eskey, elkey, key):
    kl[key] = (kl[eskey] - kl[elkey]) / kl[elkey]

def BIAS(kls, vkey, period_s, period_l):
    key = get_bias_key(period_s, period_l)
    eskey = get_ema_key(vkey, period_s)
    elkey = get_ema_key(vkey, period_l)

    kl = kls[-1]
    if key in kls[-2] and eskey in kl and elkey in kl:
        calc_bias(kls[-1], eskey, elkey, key)
        return key

    kl = kls[-2]
    if key in kls[-3] and eskey in kl and elkey in kl:
        calc_bias(kls[-2], eskey, elkey, key)
        calc_bias(kls[-1], eskey, elkey, key)
        return key

    if len(kls) < period_s:
        return
    EMA(kls, vkey, period_s)

    if len(kls) < period_l:
        return
    EMA(kls, vkey, period_l)

    print_kl_info(key, kls[-1])

    for kl in kls[period_l-1:]:
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


##### MACD ####################################################################
def calc_macd(kls, vkey, fastkey, slowkey, difkey, signalkey, histkey, fast_k, slow_k, signal_k, idx):
    calc_ema(kls, vkey, fastkey, fast_k, idx)
    calc_ema(kls, vkey, slowkey, slow_k, idx)
    kl = kls[idx]
    kl[difkey] = kl[fastkey] - kl[slowkey]
    calc_ema(kls, difkey, signalkey, signal_k, idx)
    kl[histkey] = kl[difkey] - kl[signalkey]


def MACD(kls, vkey, fastperiod=12, slowperiod=26, signalperiod=9):
    fastkey   = get_ema_key(vkey, fastperiod)
    slowkey   = get_ema_key(vkey, slowperiod)
    difkey    = "macd_dif_%s_%s" % (fastperiod, slowperiod)
    signalkey = get_ema_key(difkey, signalperiod)
    histkey   = "macd_hist_%s_%s_%s" % (fastperiod, slowperiod, signalperiod)

    fast_k   = get_ema_k(fastperiod)
    slow_k   = get_ema_k(slowperiod)
    signal_k = get_ema_k(signalperiod)

    if histkey in kls[-2]:
        calc_macd(kls, vkey, fastkey, slowkey, difkey, signalkey, histkey, fast_k, slow_k, signal_k, -1)
        return difkey, signalkey, histkey

    if histkey in kls[-3]:
        calc_macd(kls, vkey, fastkey, slowkey, difkey, signalkey, histkey, fast_k, slow_k, signal_k, -2)
        calc_macd(kls, vkey, fastkey, slowkey, difkey, signalkey, histkey, fast_k, slow_k, signal_k, -1)
        return difkey, signalkey, histkey

    if len(kls) < fastperiod:
        return
    EMA(kls, vkey, fastperiod)

    if len(kls) < slowperiod:
        return
    EMA(kls, vkey, slowperiod)

    for kl in kls[slowperiod-1:]:
        kl[difkey] =  kl[fastkey] - kl[slowkey]

    EMA(kls, difkey, signalperiod)

    for kl in kls[signalperiod+slowperiod:]:
        kl[histkey] = kl[difkey] - kl[signalkey]

    return difkey, signalkey, histkey


#####  ####################################################################

def MAX(kls, vkey):
    if vkey not in kls[-1]:
        return
    max_v = kls[-1][vkey]
    for kl in kls[-2::-1]:
        if vkey not in kl:
            break
        if kl[vkey] > max_v:
            max_v = kl[vkey]
    return max_v

def MIN(kls, vkey):
    if vkey not in kls[-1]:
        return
    min_v = kls[-1][vkey]
    for kl in kls[-2::-1]:
        if vkey not in kl:
            break
        if kl[vkey] < min_v:
            min_v = kl[vkey]
    return min_v

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

