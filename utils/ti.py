#!/usr/bin/python
"""json接口 技术指标"""
from .indicator import py_rsi_ema, py_rsi_ua
from datetime import datetime


def print_kl_info(key, kl):
    pass
    #print("%12s:  "%key, datetime.fromtimestamp(kl["open_time"]/1000), ""*10, datetime.fromtimestamp(kl["close_time"]/1000) )


##### MA ####################################################################
def get_ma_key(vkey, period):
    return "%s_ma_%s" % (vkey, period)

def calc_ma(kls, vkey, key, period, idx):
    kls[idx][key] = (float(kls[idx][vkey]) - float(kls[idx-period][vkey])) / period + kls[idx-1][key]

def MA(kls, vkey, period):
    key = get_ma_key(vkey, period)

    if key in kls[-2]:
        calc_ma(kls, vkey, key, period, -1)
        return key

    if key in kls[-3]:
        calc_ma(kls, vkey, key, period, -2)
        calc_ma(kls, vkey, key, period, -1)
        return key

    if len(kls) < period:
        return

    vs_init = [ float(kl[vkey]) for kl in kls[:period]]
    kls[period-1][key] = sum(vs_init) / period

    for i in range(period, len(kls)):
        calc_ma(kls, vkey, key, period, i)
    return key


##### EMA ####################################################################
def get_ema_key(vkey, period):
    return "%s_ema_%s" % (vkey, period)

def calc_ema(kls, vkey, key, k, idx):
    kls[idx][key] = float(kls[idx][vkey]) * k + kls[idx-1][key] * (1 - k)

def get_ema_k(period):
    return 2 / (float(period) + 1)

def EMA(kls, vkey, period, start_idx=0):
    k = get_ema_k(period)
    key = get_ema_key(vkey, period)

    if key in kls[-2]:
        calc_ema(kls, vkey, key, k, -1)
        return key

    if key in kls[-3]:
        calc_ema(kls, vkey, key, k, -2)
        calc_ema(kls, vkey, key, k, -1)
        return key

    if len(kls) < start_idx+period:
        return

    print_kl_info(key, kls[-1])

    vs_init = [ float(kl[vkey]) for kl in kls[start_idx:start_idx+period]]
    kls[start_idx+period-1][key] = sum(vs_init) / period

    for i in range(start_idx+period, len(kls)):
        calc_ema(kls, vkey, key, k, i)
    return key


##### BIAS ####################################################################
def get_bias_key(period_s, period_l):
    return "bias_%s_%s" % (period_s, period_l)

def calc_bias(kl, vskey, vlkey, key):
    kl[key] = (kl[vskey] - kl[vlkey]) / kl[vlkey]


def BIAS(kls, vskey, vlkey):
    key = "bias_%s_%s" % (vskey, vlkey)

    kl = kls[-1]
    if key in kls[-2] and vskey in kl and vlkey in kl:
        calc_bias(kls[-1], vskey, vlkey, key)
        return key

    kl = kls[-2]
    if key in kls[-3] and vskey in kl and vlkey in kl:
        calc_bias(kls[-2], vskey, vlkey, key)
        calc_bias(kls[-1], vskey, vlkey, key)
        return key

    for kl in kls:
        if vlkey not in kl:
            continue
        calc_bias(kl, vskey, vlkey, key)
    return key

def BIAS_EMA(kls, vkey, period_s, period_l):
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
    return "u_ema_%s" % get_rsi_key(period)

def get_rsi_ema_d_key(period):
    return "d_ema_%s" % get_rsi_key(period)

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
        return None, None, None
    EMA(kls, vkey, fastperiod)

    if len(kls) < slowperiod:
        return None, None, None
    EMA(kls, vkey, slowperiod)

    for kl in kls[slowperiod-1:]:
        kl[difkey] =  kl[fastkey] - kl[slowkey]

    EMA(kls, difkey, signalperiod, slowperiod-1)

    for kl in kls[signalperiod+slowperiod:]:
        kl[histkey] = kl[difkey] - kl[signalkey]

    return difkey, signalkey, histkey


##### KD ####################################################################
def get_rsv_key(period):
    return "rsv_%s" % (period)

def calc_rsv(kls, closekey, rsvkey, max_high, min_low, idx):
    kls[idx][rsvkey] = 100 * (float(kls[idx][closekey]) - min_low) / (max_high - min_low)

def calc_kd(kls, rsvkey, kkey, dkey, idx):
    M_K = 3
    M_D = 3
    a_k = 1 / M_K
    a_d = 1 / M_D

    kls[idx][kkey] = a_k * kls[idx][rsvkey] + (1 - a_k) * kls[idx-1][kkey]
    kls[idx][dkey] = a_d * kls[idx][kkey] + (1 - a_d) * kls[idx-1][dkey]

def calc_kd_all(kls, closekey, highkey, lowkey, rsvkey, kkey, dkey, period, idx):
    highs = [float(kl[highkey]) for kl in kls[-period:]]
    lows = [float(kl[lowkey]) for kl in kls[-period:]]
    calc_rsv(kls, closekey, rsvkey, max(highs), min(lows), idx)
    calc_kd(kls, rsvkey, kkey, dkey, idx)

def KD(kls, closekey, highkey, lowkey, period=9):
    rsvkey = get_rsv_key(period)
    kkey = "KD_K_%s" % (period)
    dkey = "KD_D_%s" % (period)

    '''
    if dkey in kls[-2]:
        calc_kd_all(kls, closekey, highkey, lowkey, rsvkey, kkey, dkey, period, -1)
    if dkey in kls[-3]:
        calc_kd_all(kls, closekey, highkey, lowkey, rsvkey, kkey, dkey, period, -2)
        calc_kd_all(kls, closekey, highkey, lowkey, rsvkey, kkey, dkey, period, -1)
    '''
    if len(kls) < period:
        return None, None

    highs = [float(kl[highkey]) for kl in kls[:period]]
    lows = [float(kl[lowkey]) for kl in kls[:period]]
    calc_rsv(kls, closekey, rsvkey, max(highs), min(lows), period-1)
    kls[period-1][dkey] = kls[period-1][kkey] = kls[period-1][rsvkey]

    for i in range(period, len(kls)):
        highs.pop(0)
        lows.pop(0)
        highs.append(float(kls[i][highkey]))
        lows.append(float(kls[i][lowkey]))
        calc_rsv(kls, closekey, rsvkey, max(highs), min(lows), i)
        calc_kd(kls, rsvkey, kkey, dkey, i)
    return kkey, dkey


##### ATR ####################################################################
def get_truerange_key():
    return "truerange"

def calc_truerange(kls, highkey, lowkey, closekey, trkey, idx):
    pre_close = float(kls[idx-1][closekey])
    kls[idx][trkey] = max(float(kls[idx][highkey]), pre_close) - min(float(kls[idx][lowkey]), pre_close)

def TrueRange(kls, highkey, lowkey, closekey, period=14):
    key = get_truerange_key()

    if key in kls[-2]:
        calc_truerange(kls, highkey, lowkey, closekey, key, -1)
        return key

    if key in kls[-3]:
        calc_truerange(kls, highkey, lowkey, closekey, key, -2)
        calc_truerange(kls, highkey, lowkey, closekey, key, -1)
        return key

    if len(kls) < period:
        return

    for i in range(1, len(kls)):
        calc_truerange(kls, highkey, lowkey, closekey, key, i)
    return key


def _ATR(kls, highkey, lowkey, closekey, period=14):
    trkey = TrueRange(kls, highkey, lowkey, closekey, period)
    key = EMA(kls, trkey, period, 1)
    return key


##### TRIX ####################################################################
def get_trix_key(period):
    return "trix_%d" % (period)

def calc_trix(kls, closekey, ema_key_1, ema_key_2, ema_key_3, key, k, period, idx):
    calc_ema(kls, closekey, ema_key_1, k, idx)
    calc_ema(kls, ema_key_1, ema_key_2, k, idx)
    calc_ema(kls, ema_key_2, ema_key_3, k, idx)
    kls[idx][key] = ((kls[idx][ema_key_3] / kls[idx-1][ema_key_3]) -1 ) * 100

def TRIX(kls, closekey, period=30):
    key = get_trix_key(period)
    ema_key_1 = get_ema_key(closekey, period)
    ema_key_2 = get_ema_key(ema_key_1, period)
    ema_key_3 = get_ema_key(ema_key_2, period)
    k = get_ema_k(period)

    if key in kls[-2]:
        calc_trix(kls, closekey, ema_key_1, ema_key_2, ema_key_3, key, k, period, -1)
        return key
    if key in kls[-3]:
        calc_trix(kls, closekey, ema_key_1, ema_key_2, ema_key_3, key, k, period, -2)
        calc_trix(kls, closekey, ema_key_1, ema_key_2, ema_key_3, key, k, period, -1)
        return key

    kls_len = len(kls)
    if kls_len < period:
        return
    EMA(kls, closekey, period)
    if kls_len < 2*period:
        return
    EMA(kls, ema_key_1, period, period)
    if kls_len < 3*period:
        return
    EMA(kls, ema_key_2, period, 2*period)
    for i in range(3*period, kls_len):
        kls[i][key] = ((kls[i][ema_key_3] / kls[i-1][ema_key_3]) -1 ) * 100
    return key


#####  ####################################################################

def MAX(kls, vkey):
    if vkey not in kls[-1]:
        return
    max_v = float(kls[-1][vkey])
    for kl in kls[-2::-1]:
        if vkey not in kl:
            break
        cur_v = float(kl[vkey])
        if cur_v > max_v:
            max_v = cur_v
    return max_v

def MIN(kls, vkey):
    if vkey not in kls[-1]:
        return
    min_v = float(kls[-1][vkey])
    for kl in kls[-2::-1]:
        if vkey not in kl:
            break
        cur_v = float(kl[vkey])
        if cur_v < min_v:
            min_v = cur_v
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

