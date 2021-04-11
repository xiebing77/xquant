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
    parser.add_argument('-direction', choices=bl.directions, help='direction')
    parser.add_argument('-action', choices=bl.actions, help='action')
    #parser.add_argument('-pr', type=float, default=0, help='postion rate')
    parser.add_argument('-rmk', help='remark')
    args = parser.parse_args()
    print(args)
    if not (args.sii and args.action):
        parser.print_help()
        exit(1)

    instance = get_strategy_instance(args.sii)
    config = xq.get_strategy_config(instance['config_path'])
    re = RealEngine(args.sii, instance['exchange'], config, instance['value'])

    symbol = config['symbol']
    klines = re.md.get_klines(symbol, config["kline"]["interval"], 1)
    if len(klines) <= 0:
        exit(1)

    cur_price = float(klines[-1][re.md.get_kline_seat_close()])
    pst_info = re.get_position(symbol, cur_price)
    if args.action in [bl.OPEN_POSITION, bl.UNLOCK_POSITION]:
        pst_rate = 1
    else:
        pst_rate = 0

    print('before position info: %s' % (pst_info))
    print('args.action: %s, pst_rate: %g' % (args.action, pst_rate))
    if args.rmk:
        rmk = args.rmk
    else:
        rmk = args.action
    rmk += ":  "
    re.send_order(symbol, pst_info, cur_price, args.direction, args.action, pst_rate, None, rmk)

    after_pst_info = re.get_position(symbol, cur_price)
    print('after  position info: %s' % (after_pst_info))
