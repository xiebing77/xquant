#!/usr/bin/python
"""xquant公共定义及公用函数"""

import utils.tools as ts

SIDE_BUY = "BUY"
SIDE_SELL = "SELL"

ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_MARKET = "MARKET"

ORDER_STATUS_WAIT = "wait"
ORDER_STATUS_OPEN = "open"
ORDER_STATUS_CLOSE = "close"
ORDER_STATUS_CANCELLING = "cancelling"
ORDER_STATUS_CANCELLED = "cancelled"


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

def create_signal(side, pst_rate, rmk):
    """创建交易信号"""
    return {"side": side, "pst_rate": pst_rate, "rmk": rmk}


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
        return None, None

    side = None
    for signal in signals:
        new_side = signal["side"]
        new_rate = signal["pst_rate"]
        new_rmk = signal["rmk"]

        if side is None:
            side = new_side
            rate = new_rate
            rmk = new_rmk
        elif side is new_side:
            if rate > new_rate:
                rate = new_rate
                rmk = new_rmk
        else:
            if side is xq.SIDE_BUY:
                side = new_side
                rate = new_rate
                rmk = new_rmk

    return side, rate, rmk
