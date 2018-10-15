#!/usr/bin/python
"""xquant公共定义及公用函数"""

import utils.tools as ts
from datetime import datetime, timedelta, time

SIDE_BUY = "BUY"
SIDE_SELL = "SELL"

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

    elif interval == KLINE_INTERVAL_4HOUR:
        open_hour = (dt.hour // 4) * 4
        return datetime.combine(dt.date(), time(open_hour, 0, 0))

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

    elif interval == KLINE_INTERVAL_4HOUR:
        return timedelta(hours=4*size-1)

    elif interval == KLINE_INTERVAL_1DAY:
        return timedelta(days=size-1)

    else:
        return None

def get_interval_timedelta(interval):
    if interval == KLINE_INTERVAL_1MINUTE:
        return timedelta(minutes=1)

    elif interval == KLINE_INTERVAL_4HOUR:
        return timedelta(hours=4)

    elif interval == KLINE_INTERVAL_1DAY:
        return timedelta(days=1)

    else:
        return None

def get_interval_seconds(interval):
    if interval == KLINE_INTERVAL_1MINUTE:
        return SECONDS_MINUTE

    elif interval == KLINE_INTERVAL_4HOUR:
        return 4 * SECONDS_HOUR

    elif interval == KLINE_INTERVAL_1DAY:
        return SECONDS_DAY

    else:
        return None


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


def create_signal(side, pst_rate, rmk, can_buy_after=None):
    """创建交易信号"""
    return {"side": side, "pst_rate": pst_rate, "rmk": rmk, "can_buy_after": can_buy_after}

def create_buy_signal(pst_rate, rmk, can_buy_after=None):
    """创建买信号"""
    return create_signal(SIDE_BUY, pst_rate, rmk, can_buy_after)

def create_sell_signal(pst_rate, rmk, can_buy_after=None):
    """创建卖信号"""
    return create_signal(SIDE_SELL, pst_rate, rmk, can_buy_after)


def decision_signals(signals):
    """决策交易信号"""
    sdf = pd.DataFrame(signals)
    sdf_min = sdf.groupby("side")["pst_rate"].min()

    if xq.SIDE_SELL in sdf_min:
        return xq.SIDE_SELL, sdf_min[xq.SIDE_SELL]

    if xq.SIDE_BUY in sdf_min:
        return xq.SIDE_BUY, sdf_min[xq.SIDE_BUY]

    return None, None


def decision_signals2(signals):
    """决策交易信号"""
    if not signals:
        return None, None, None, None

    side = None
    for signal in signals:
        new_side = signal["side"]
        new_rate = signal["pst_rate"]
        new_rmk = signal["rmk"]
        new_cba = signal["can_buy_after"]

        if side is None:
            side = new_side
            rate = new_rate
            rmk = new_rmk
            cba = new_cba
        elif side is new_side:
            if rate > new_rate:
                rate = new_rate
                rmk = new_rmk
            elif rate == new_rate:
                rmk += ", " + new_rmk
                if new_cba:
                    if cba:
                        if new_cba > cba:
                            cba = new_cba
                    else:
                        cba = new_cba

        else:
            if side is SIDE_BUY:
                side = new_side
                rate = new_rate
                rmk = new_rmk
                cba = new_cba

    return side, rate, rmk, cba
