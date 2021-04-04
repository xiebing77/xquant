#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from exchange.exchange import get_exchange_names, create_exchange
from exchange.binanceExchange import BinanceExchange

directions = ["buy", "sell"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Slippage Calculation')
    parser.add_argument('-exchange', default=BinanceExchange.name, choices=get_exchange_names(), help='exchange name')
    parser.add_argument('-symbol', required=True, help='symbol, eg: btc_usdt')
    parser.add_argument('-direction', required=True, choices=directions, help='direction')
    parser.add_argument('-amount', type=float, required=True, help='amount')

    args = parser.parse_args()
    # print(args)

    symbol = args.symbol
    direction = args.direction
    amount = args.amount

    exchange = create_exchange(args.exchange)
    if not exchange:
        print("exchange name error!")
        exit(1)
    print("%s" % (args.exchange) )
    exchange.connect()

    klines = exchange.get_klines_1day(symbol, 1)
    cur_price = float(klines[-1][4])

    book = exchange.get_order_book(symbol, 1000)
    # print(book)

    if direction == 'buy':
        orders = book['asks']
    else:
        orders = book['bids']

    deal = 0
    cost = 0
    for order in orders:
        order_amount = float(order[1])
        order_price = float(order[0])
        if amount - deal > order_amount:
            deal += order_amount
            cost += order_amount * order_price
        else:
            cost += (amount - deal) * order_price
            deal = amount
            break

    if deal < amount:
        print("The order book depth is not enough. Please get more orders")
        exit(1)
    average_price = cost / amount
    if direction == 'buy':
        slippage = (average_price - cur_price) * 100 / cur_price
    else:
        slippage = (cur_price - average_price) * 100 / cur_price
    print("Current price:     ", cur_price)
    print("Average deal price:", average_price)
    print("Deal amount:       ", amount)
    print("Total cost:        ", cost)
    print("Slippage:          ", slippage, "%")
