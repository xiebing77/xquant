#!/usr/bin/python
"""小工具函数"""

import time
import pandas as pd

def reserve_float(flo, float_digits=0):
    """调整精度"""
    value_str = "%.11f" % flo
    return str_to_float(value_str, float_digits)


def str_to_float(string, float_digits=0):
    """字符转浮点，并调整精度"""
    value_list = string.split(".")
    if len(value_list) == 2:
        new_value_str = ".".join([value_list[0], value_list[1][0:float_digits]])
    else:
        new_value_str = value_list[0]
    return float(new_value_str)

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

