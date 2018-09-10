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
