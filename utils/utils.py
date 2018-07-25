#!/usr/bin/python

def reserve_float(value, float_digits=0):
    value_str = '%.11f' % value
    value_list = value_str.split('.')
    if len(value_list) == 2:
        new_value_str = '.'.join([value_list[0], value_list[1][0:float_digits]])
    else:
        new_value_str = value_list[0]
    return float(new_value_str)

