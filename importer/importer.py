#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from datetime import datetime
import common.xquant as xq

def split_time_range(range):
    time_range = range.split(xq.time_range_split)
    start_time = datetime.strptime(time_range[0], "%Y-%m-%dT%H")
    end_time = datetime.strptime(time_range[1], "%Y-%m-%dT%H")
    return start_time, end_time

def add_common_arguments(description):
    parser = argparse.ArgumentParser(description='klines print or check')
    parser.add_argument('-m', help='market data source')
    parser.add_argument('-s', help='symbol (btc_usdt)')
    parser.add_argument('-r', help='time range (2018-7-1T8' + xq.time_range_split + '2018-8-1T8)')
    parser.add_argument('-k', help='kline type (1m、4h、1d...)')
    return parser

