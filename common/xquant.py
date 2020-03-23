#!/usr/bin/python
"""xquant公共定义及公用函数"""

import utils.tools as ts
from datetime import datetime, timedelta, time

time_range_split = "~"


KLINE_INTERVAL_1MINUTE = '1m'
KLINE_INTERVAL_3MINUTE = '3m'
KLINE_INTERVAL_5MINUTE = '5m'
KLINE_INTERVAL_15MINUTE = '15m'
KLINE_INTERVAL_30MINUTE = '30m'
KLINE_INTERVAL_1HOUR = '1h'
KLINE_INTERVAL_2HOUR = '2h'
KLINE_INTERVAL_4HOUR = '4h'
KLINE_INTERVAL_6HOUR = '6h'
KLINE_INTERVAL_8HOUR = '8h'
KLINE_INTERVAL_12HOUR = '12h'
KLINE_INTERVAL_1DAY = '1d'
KLINE_INTERVAL_3DAY = '3d'
KLINE_INTERVAL_1WEEK = '1w'
KLINE_INTERVAL_1MONTH = '1M'


ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_MARKET = "MARKET"

ORDER_STATUS_WAIT = "wait"
ORDER_STATUS_OPEN = "open"
ORDER_STATUS_CLOSE = "close"
ORDER_STATUS_CANCELLING = "cancelling"
ORDER_STATUS_CANCELLED = "cancelled"

SECONDS_MINUTE = 60
SECONDS_HOUR = 60 * SECONDS_MINUTE
SECONDS_DAY = 24 * SECONDS_HOUR

def get_kline_collection(symbol, interval):
    return "kline_%s_%s" % (symbol, interval)

def get_open_time(interval, dt):
    if interval == KLINE_INTERVAL_1MINUTE:
        return datetime.combine(dt.date(), time(dt.hour, dt.minute, 0))
    elif interval == KLINE_INTERVAL_3MINUTE:
        open_minute = (dt.minute // 3) * 3
        return datetime.combine(dt.date(), time(dt.hour, open_minute, 0))
    elif interval == KLINE_INTERVAL_5MINUTE:
        open_minute = (dt.minute // 5) * 5
        return datetime.combine(dt.date(), time(dt.hour, open_minute, 0))
    elif interval == KLINE_INTERVAL_15MINUTE:
        open_minute = (dt.minute // 15) * 15
        return datetime.combine(dt.date(), time(dt.hour, open_minute, 0))
    elif interval == KLINE_INTERVAL_30MINUTE:
        if dt.minute < 30:
            open_minute = 0
        else:
            open_minute = 30
        return datetime.combine(dt.date(), time(dt.hour, open_minute, 0))

    elif interval == KLINE_INTERVAL_1HOUR:
        open_hour = dt.hour
        return datetime.combine(dt.date(), time(open_hour, 0, 0))
    elif interval == KLINE_INTERVAL_2HOUR:
        open_hour = (dt.hour // 2) * 2
        return datetime.combine(dt.date(), time(open_hour, 0, 0))
    elif interval == KLINE_INTERVAL_4HOUR:
        open_hour = (dt.hour // 4) * 4
        return datetime.combine(dt.date(), time(open_hour, 0, 0))

    elif interval == KLINE_INTERVAL_6HOUR:
        if dt.hour < 2:
            return datetime.combine(dt.date() - timedelta(days=1), time(20, 0, 0))
        elif dt.hour < 8:
            return datetime.combine(dt.date(), time(2, 0, 0))
        elif dt.hour < 14:
            return datetime.combine(dt.date(), time(8, 0, 0))
        elif dt.hour < 20:
            return datetime.combine(dt.date(), time(14, 0, 0))
        else:
            return datetime.combine(dt.date(), time(20, 0, 0))

    elif interval == KLINE_INTERVAL_8HOUR:
        open_hour = (dt.hour // 8) * 8
        return datetime.combine(dt.date(), time(open_hour, 0, 0))

    elif interval == KLINE_INTERVAL_12HOUR:
        if dt.hour < 8:
            return datetime.combine(dt.date() - timedelta(days=1), time(20, 0, 0))
        elif dt.hour >= 20:
            return datetime.combine(dt.date(), time(20, 0, 0))
        else:
            return datetime.combine(dt.date(), time(8, 0, 0))

    elif interval == KLINE_INTERVAL_1DAY:
        if dt.hour < 8:
            return datetime.combine(dt.date() - timedelta(days=1), time(8, 0, 0))
        else:
            return datetime.combine(dt.date(), time(8, 0, 0))
    else:
        return None

def get_timedelta(interval, size):
    if interval == KLINE_INTERVAL_1MINUTE:
        return timedelta(minutes=size-1)
    elif interval == KLINE_INTERVAL_3MINUTE:
        return timedelta(minutes=3*size-1)
    elif interval == KLINE_INTERVAL_5MINUTE:
        return timedelta(minutes=5*size-1)
    elif interval == KLINE_INTERVAL_15MINUTE:
        return timedelta(minutes=15*size-1)
    elif interval == KLINE_INTERVAL_30MINUTE:
        return timedelta(minutes=30*size-1)

    elif interval == KLINE_INTERVAL_1HOUR:
        return timedelta(hours=1*size-1)
    elif interval == KLINE_INTERVAL_2HOUR:
        return timedelta(hours=2*size-1)
    elif interval == KLINE_INTERVAL_4HOUR:
        return timedelta(hours=4*size-1)
    elif interval == KLINE_INTERVAL_6HOUR:
        return timedelta(hours=6*size-1)
    elif interval == KLINE_INTERVAL_8HOUR:
        return timedelta(hours=8*size-1)
    elif interval == KLINE_INTERVAL_12HOUR:
        return timedelta(hours=12*size-1)

    elif interval == KLINE_INTERVAL_1DAY:
        return timedelta(days=size-1)

    else:
        return None

def get_interval_timedelta(interval):
    if interval == KLINE_INTERVAL_1MINUTE:
        return timedelta(minutes=1)
    elif interval == KLINE_INTERVAL_3MINUTE:
        return timedelta(minutes=3)
    elif interval == KLINE_INTERVAL_5MINUTE:
        return timedelta(minutes=5)
    elif interval == KLINE_INTERVAL_15MINUTE:
        return timedelta(minutes=15)
    elif interval == KLINE_INTERVAL_30MINUTE:
        return timedelta(minutes=30)

    elif interval == KLINE_INTERVAL_1HOUR:
        return timedelta(hours=1)
    elif interval == KLINE_INTERVAL_2HOUR:
        return timedelta(hours=2)
    elif interval == KLINE_INTERVAL_4HOUR:
        return timedelta(hours=4)
    elif interval == KLINE_INTERVAL_6HOUR:
        return timedelta(hours=6)
    elif interval == KLINE_INTERVAL_8HOUR:
        return timedelta(hours=8)
    elif interval == KLINE_INTERVAL_12HOUR:
        return timedelta(hours=12)

    elif interval == KLINE_INTERVAL_1DAY:
        return timedelta(days=1)

    else:
        return None

def get_interval_seconds(interval):
    if interval == KLINE_INTERVAL_1MINUTE:
        return 1 * SECONDS_MINUTE
    elif interval == KLINE_INTERVAL_3MINUTE:
        return 3 * SECONDS_MINUTE
    elif interval == KLINE_INTERVAL_5MINUTE:
        return 5 * SECONDS_MINUTE
    elif interval == KLINE_INTERVAL_15MINUTE:
        return 15 * SECONDS_MINUTE
    elif interval == KLINE_INTERVAL_30MINUTE:
        return 30 * SECONDS_MINUTE

    elif interval == KLINE_INTERVAL_1HOUR:
        return 1 * SECONDS_HOUR
    elif interval == KLINE_INTERVAL_2HOUR:
        return 2 * SECONDS_HOUR
    elif interval == KLINE_INTERVAL_4HOUR:
        return 4 * SECONDS_HOUR
    elif interval == KLINE_INTERVAL_6HOUR:
        return 6 * SECONDS_HOUR
    elif interval == KLINE_INTERVAL_8HOUR:
        return 8 * SECONDS_HOUR
    elif interval == KLINE_INTERVAL_12HOUR:
        return 12 * SECONDS_HOUR

    elif interval == KLINE_INTERVAL_1DAY:
        return SECONDS_DAY

    else:
        return None

def get_next_open_time(interval, dt):
    return get_open_time(interval, dt) + get_interval_timedelta(interval)

def get_next_open_timedelta(interval, dt):
    return get_next_open_time(interval, dt) - dt



def creat_symbol(target_coin, base_coin):
    """create symbol"""
    return "%s_%s" % (target_coin.lower(), base_coin.lower())


def get_symbol_coins(symbol):
    """获取coins"""
    coins = symbol.split("_")
    return tuple(coins)


def create_balance(coin, free, frozen):
    """ 创建余额 """
    return {"coin": coin, "free": free, "frozen": frozen}


def get_balance_free(balance):
    """ 获取可用数 """
    return ts.str_to_float(balance["free"])


def get_balance_frozen(balance):
    """ 获取冻结数 """
    return ts.str_to_float(balance["frozen"])


def down_area(ss, ls):
    total_len = len(ss)

    ei = -1
    i = -2
    while i >= -total_len:
        v = ss[i]-ls[i]
        if v > 0:
            return -1, -1, -1
        if v < ss[ei]-ls[ei]:
            break
        ei = i
        i -= 1

    mi = i
    bi = i
    while i >= -total_len:
        v = ss[i]-ls[i]
        if v > 0:
            break

        if ss[mi] - ls[mi] > v:
            mi = i
        bi = i
        i -= 1

    return bi, mi, ei
