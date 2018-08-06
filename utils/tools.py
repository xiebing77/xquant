#!/usr/bin/python
"""小工具函数"""


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
