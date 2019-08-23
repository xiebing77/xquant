#!/usr/bin/python3
import os
from exchange.binance.client import Client
from exchange.binance.enums import *

api_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_SECRET_KEY')

if __name__ == "__main__":
    client  = Client(api_key, secret_key)

    # ret = client.create_order(symbol='ETHUSDT', side=SIDE_BUY, type=ORDER_TYPE_LIMIT,
            # timeInForce=TIME_IN_FORCE_GTC, price=180, quantity=0.1)
    # ret = client.get_all_orders(symbol='ETHUSDT')
    # ret = client.get_order(symbol='ETHUSDT', orderId='391540562')
    # ret = client.get_open_orders(symbol='ETHUSDT')
    # ret = client.get_my_trades(symbol='ETHUSDT')
    ret = client.get_account()
    print(ret)
