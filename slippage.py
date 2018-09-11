#!/usr/bin/python3
import argparse

from exchange.binanceExchange import BinanceExchange

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Slippage Calculation')
    parser.add_argument('-b', help='base coin')
    parser.add_argument('-t', help='target coin')
    parser.add_argument('-d', help='direction')
    parser.add_argument('-a', help='amount')

    args = parser.parse_args()
    # print(args)
    if not (args.b and args.t and args.d and args.a):
        parser.print_help()
        exit(1)

    base_coin = args.b
    target_coin = args.t
    direction = args.d
    amount = float(args.a)

    exchange = BinanceExchange()
    symbol = "%s_%s" % (target_coin, base_coin)
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
