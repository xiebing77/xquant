#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import common.bill as bl
import common.xquant as xq
from exchange.exchange import get_exchange_names, create_exchange
from exchange.binanceExchange import BinanceExchange

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='account')
    parser.add_argument('-exchange', choicdefault=BinanceExchange.name, choices=get_exchange_names(), help='exchange')
    parser.add_argument('-symbol', help='symbol (btc_usdt)')
    parser.add_argument('-price', type=float, help='price')
    parser.add_argument('-amount', type=float, help='amount')

    parser.add_argument('-direction', choices=bl.directions, help='direction')
    parser.add_argument('-action', choices=bl.actions, help='action')
    parser.add_argument('-type', choices=xq.ordertypes, default=xq.ORDER_TYPE_LIMIT, help='order type')

    args = parser.parse_args()
    # print(args)

    exchange = create_exchange(args.exchange)
    if not exchange:
        print("exchange name error!")
        exit(1)
    exchange.connect()

    exchange.send_order(args.direction, args.action, args.type, args.symbol, args.price, args.amout)
