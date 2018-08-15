#!/usr/bin/python
"""小工具函数"""
import math
import time
import logging
import pandas as pd

MATH_FLOOR = 0 # 向下，舍去多余
MATH_CEIL  = 1 # 向上，
MATH_ROUND = 2 # 四舍五入

def reserve_float_ceil(flo, float_digits=0):
    return reserve_float(flo, float_digits, MATH_CEIL)

def reserve_float(flo, float_digits=0, flag=MATH_FLOOR):
    """调整精度"""
    value_str = "%.11f" % flo
    return str_to_float(value_str, float_digits, flag=MATH_FLOOR)


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
                new_value += math.pow(10,-float_digits)
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

    start_timestamp = time.mktime(start_time.timetuple())
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

