#!/usr/bin/python
"""xquant公共定义及公用函数"""

import utils.tools as ts
from datetime import datetime, timedelta, time
import json


time_range_split = "~"

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


def get_balance_coin(balance):
    return balance["coin"]


def get_balance_free(balance):
    """ 获取可用数 """
    return float(balance["free"])


def get_balance_frozen(balance):
    """ 获取冻结数 """
    return float(balance["frozen"])


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

def get_strategy_config(config_path):
    fo = open(config_path, "r")
    config = json.loads(fo.read())
    fo.close()
    return config
