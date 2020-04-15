#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import common.xquant as xq
import common.bill as bl
from common.instance import get_strategy_instance
from engine.realengine import RealEngine

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='close postion')
    parser.add_argument('-sii', help='strategy instance id')
    parser.add_argument('-action', choices=[bl.OPEN_POSITION, bl.CLOSE_POSITION], help='action')
    #parser.add_argument('-pr', type=float, default=0, help='postion rate')
    parser.add_argument('-rmk', help='remark')
    args = parser.parse_args()
    print(args)
    if not (args.sii and args.action):
        parser.print_help()
        exit(1)

    instance = get_strategy_instance(args.sii)
    config = xq.get_strategy_config(instance['config_path'])
    re = RealEngine(args.sii, instance['exchange'], config)
    re.value = instance['value']

    direction = config["direction"]
    symbol = config['symbol']
    klines = re.md.get_klines(symbol, config["kline"]["interval"], 1)
    if len(klines) <= 0:
        exit(1)

    cur_price = float(klines[-1][re.md.closeindex])
    pst_info = re.get_position(symbol, cur_price)
    if args.action == bl.OPEN_POSITION:
        pst_rate = 1
    else:
        pst_rate = 0

    print(pst_info)
    print('args.action: %s, pst_rate: %g' % (args.action, pst_rate))
    re.send_order(symbol, pst_info, cur_price, direction, args.action, pst_rate, None, args.rmk)

