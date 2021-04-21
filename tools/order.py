#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import common.bill as bl
import common.xquant as xq
from exchange.exchange import get_exchange_names, create_exchange
from exchange.binanceExchange import BinanceExchange


def send_order(args):
    exchange = create_exchange(args.exchange)
    if not exchange:
        print("exchange name error!")
        exit(1)
    exchange.connect()
    exchange.send_order(args.direction, args.action, args.type, args.symbol, args.price, args.amount)


def cancel_order(args):
    exchange = create_exchange(args.exchange)
    if not exchange:
        print("exchange name error!")
        exit(1)
    exchange.connect()
    exchange.cancel_order(args.symbol, args.orderid)


def query_orders(args):
    exchange = create_exchange(args.exchange)
    if not exchange:
        print("exchange name error!")
        exit(1)
    exchange.connect()
    orders = exchange.get_open_orders(args.symbol)
    print(orders)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='account')

    subparsers = parser.add_subparsers(help='sub-command help')

    parser_send = subparsers.add_parser('send', help='send order')
    parser_send.add_argument('-exchange', default=BinanceExchange.name, choices=get_exchange_names(), help='exchange')
    parser_send.add_argument('-symbol', required=True, help='symbol (btc_usdt)')
    parser_send.add_argument('-price', required=True, type=float, help='price')
    parser_send.add_argument('-amount', required=True, type=float, help='amount')
    parser_send.add_argument('-direction', required=True, choices=bl.directions, help='direction')
    parser_send.add_argument('-action', choices=bl.actions, help='action')
    parser_send.add_argument('-type', choices=xq.ordertypes, default=xq.ORDER_TYPE_LIMIT, help='order type')
    parser_send.set_defaults(func=send_order)

    parser_cancel = subparsers.add_parser('cancel', help='cancel order')
    parser_cancel.add_argument('-exchange', default=BinanceExchange.name, choices=get_exchange_names(), help='exchange')
    parser_cancel.add_argument('-symbol', required=True, help='symbol (btc_usdt)')
    parser_cancel.add_argument('-orderid', required=True, help='order id')
    parser_cancel.set_defaults(func=cancel_order)

    parser_query = subparsers.add_parser('query', help='query open orders')
    parser_query.add_argument('-exchange', default=BinanceExchange.name, choices=get_exchange_names(), help='exchange')
    parser_query.add_argument('-symbol', required=True, help='symbol (btc_usdt)')
    parser_query.set_defaults(func=query_orders)

    args = parser.parse_args()
    # print(args)
    if hasattr(args, 'func'):
        args.func(args)
