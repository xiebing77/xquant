#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from datetime import datetime

time_range_split = "~"

def split_time_range(range):
    time_range = range.split(time_range_split)
    start_time = datetime.strptime(time_range[0], "%Y-%m-%d")
    end_time = datetime.strptime(time_range[1], "%Y-%m-%d")
    return start_time, end_time

def add_common_arguments(description):
    parser = argparse.ArgumentParser(description='klines print or check')
    parser.add_argument('-s', help='symbol (btc_usdt)')
    parser.add_argument('-r', help='time range (2018-7-1' + time_range_split + '2018-8-1)')
    parser.add_argument('-k', help='kline type (1m、4h、1d...)')
    return parser

