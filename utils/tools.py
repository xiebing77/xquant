#!/usr/bin/python
"""小工具函数"""
import math
from datetime import datetime, timedelta, time
import logging
import pandas as pd
from decimal import Decimal
import numpy as np

MATH_FLOOR = 0  # 向下，舍去多余
MATH_CEIL = 1  # 向上，
MATH_ROUND = 2  # 四舍五入

def parse_date_range(date_range):
    print("time range: [ %s )" % date_range)
    dates = date_range.split("~")

    start_time = datetime.strptime(dates[0], "%Y-%m-%d")
    end_time = datetime.strptime(dates[1], "%Y-%m-%d")
    return start_time, end_time

def parse_ic_keys(ss):
    print("keys: [ %s )" % ss)
    keys = {}

    if not ss:
        return keys
    for key in ss.split(","):
        keys[key] = True
    return keys

def ax(ax, ic_key, x, y, c, drawstyle="default"):
    ax.set_ylabel(ic_key)
    ax.grid(True)
    ax.plot(x, y, c, label=ic_key, drawstyle=drawstyle)

def createInstance(module_name, class_name, *args, **kwargs):
    # print("args  :", args)
    # print("kwargs:", kwargs)
    module_meta = __import__(module_name, globals(), locals(), [class_name])
    class_meta = getattr(module_meta, class_name)
    obj = class_meta(*args, **kwargs)
    return obj

def get_decimal(number):
    return len(str(Decimal(str(number))-Decimal(number).to_integral()).split('.')[1])

def reserve_float_ceil(flo, float_digits=0):
    return reserve_float(flo, float_digits, MATH_CEIL)

def multiply_ceil(var, const):
    decimal = get_decimal(var)
    return reserve_float_ceil(var * const, decimal)

def multiply_floor(var, const):
    decimal = get_decimal(var)
    return reserve_float(var * const, decimal)

def reserve_float(flo, float_digits=0, flag=MATH_FLOOR):
    """调整精度"""
    value_str = "%.11f" % flo
    return str_to_float(value_str, float_digits, flag)


def str_to_float(string, float_digits=0, flag=MATH_FLOOR):
    """字符转浮点，并调整精度"""
    value_list = string.split(".")
    if len(value_list) == 1:
        return float(value_list[0])

    elif len(value_list) == 2:
        new_value_str = ".".join([value_list[0], value_list[1][0:float_digits]])
        new_value = float(new_value_str)
        if flag == MATH_FLOOR:
            pass
        elif flag == MATH_CEIL:
            if float(value_list[1][float_digits:]) > 0:
                new_value += math.pow(10, -float_digits)
        else:
            return None

        return new_value
    else:
        return None


def cacl_today_fall_rate(klines, cur_price):
    """ 计算当天最高价的回落比例 """
    today_high_price = pd.to_numeric(klines["high"].values[-1])
    today_fall_rate = 1 - cur_price / today_high_price
    logging.info(
        "today  high price(%f);  fall rate(%f)", today_high_price, today_fall_rate
    )
    return today_fall_rate


def cacl_period_fall_rate(klines, start_time, cur_price):
    """ 计算开仓日期到现在最高价的回落比例 """
    if start_time is None:
        return

    start_timestamp = start_time.timestamp()
    period_df = klines[
        klines["open_time"].map(lambda x: int(x)) > start_timestamp * 1000
    ]
    period_high_price = period_df["high"].apply(pd.to_numeric).max()

    period_fall_rate = 1 - cur_price / period_high_price
    logging.info(
        "period high price(%f), fall rate(%f), start time(%s)"
        % (period_high_price, period_fall_rate, start_time)
    )
    return period_fall_rate


def is_increment(arr):
    for i in range(1, len(arr)):
        if arr[i-1] >= arr[i]:
            return False
    return True

def is_decrement(arr):
    for i in range(1, len(arr)):
        if arr[i-1] <= arr[i]:
            return False
    return True

def get_inc_step(arr):
    i = -1
    while i >= -len(arr)+1:
        if arr[i-1] > arr[i]:
            break
        i -= 1

    return -i-1

def get_dec_step(arr):
    i = -1
    while i >= -len(arr)+1:
        if arr[i-1] < arr[i]:
            break
        i -= 1

    return -i-1

def is_more(arr, c=2):
    for i in range(c, len(arr)):
        if min(arr[i-c:i]) > arr[i]:
            return False
    return True

def is_less(arr, c=2):
    for i in range(c, len(arr)):
        if max(arr[i-c:i]) < arr[i]:
            return False
    return True

def get_more_step(arr, c=2):
    i = -1
    while i >= -len(arr)+c:
        if min(arr[i-c:i]) > arr[i]:
            break
        i -= 1

    if i == -1:
        return 0

    return -1-i

def get_less_step(arr, c=2):
    i = -1
    while i >= -len(arr)+c:
        if max(arr[i-c:i]) < arr[i]:
            break
        i -= 1

    if i == -1:
        return 0

    return -1-i

def get_min_seat(arr):
    i_min  = -len(arr)
    v_min = arr[i_min]
    for i in range(i_min+1, -1):
        v = arr[i]
        if v_min > v:
            v_min = v
            i_min = i
    return i_min

def get_tops(arr, c):
    tops = []
    #print(arr)
    for i in range(-len(arr), 0):
        bi = i-c
        if bi < -len(arr):
            bi = -len(arr)

        ei = i + 1 + c
        if ei >= 0:
            sub_arr = arr[bi:]
        else:
            sub_arr = arr[bi:ei]
        if arr[i] == max(sub_arr):
            tops.append(i)
    return tops

def get_bottoms(arr, c):
    bottoms = []
    #print(arr)
    for i in range(-len(arr), 0):
        bi = i-c
        if bi < -len(arr):
            bi = -len(arr)

        ei = i + 1 + c
        if ei >= 0:
            sub_arr = arr[bi:]
        else:
            sub_arr = arr[bi:ei]

        if arr[i] == min(sub_arr):
            bottoms.append(i)
    return bottoms

def get_macd_tops(arr):
    tops = []
    bi = -len(arr)
    for i in range(bi+1, 0):
        v = arr[i]
        if v > 0:
            if arr[bi] < v:
                bi = i
        else:
            if arr[bi] > 0:
                tops.append(bi)
                bi = i
    if arr[bi] > 0:
        tops.append(bi)

    return tops

def get_macd_bottoms(arr):
    bottoms = []
    bi = -len(arr)
    for i in range(bi+1, 0):
        v = arr[i]
        if v < 0:
            if arr[bi] > v:
                bi = i
        else:
            if arr[bi] < 0:
                bottoms.append(bi)
                bi = i
    if arr[bi] < 0:
        bottoms.append(bi)

    return bottoms

def get_trend(ema1, ema2, std_diff_std=0.01, ema_diff_std=0.02, period=-5):
    # diff_data = ema1[period:] + ema2[period:] + price[period:]
    diff_data = ema1[period:] + ema2[period:]
    std_diff = np.std(diff_data)/sum(diff_data) * len(diff_data)
    # print(round(std_diff,5), round(abs(ema1[-1]/ema2[-1]), 3))
    if std_diff < std_diff_std or abs(ema1[-1] - ema2[-1]) < ema2[-1] * ema_diff_std:
        ret = 0
    elif ema1[-1] < ema2[-1]:
        ret = -1
    else:
        ret = 1

    return ret, std_diff
