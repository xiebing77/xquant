#!/usr/bin/python3
import os
from exchange.binanceFuture import BinanceFuture
# from exchange.binance.enums import *

api_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_SECRET_KEY')

if __name__ == "__main__":
    client = BinanceFuture(debug=True)
    # ret = client.get_account()
    # ret = client.get_balances("USDT")
    # ret = client.get_all_balances()
    # ret = client.get_trades("BTC_USDT")
    # ret = client.get_deals("BTC_USDT")
    # ret = client.send_order(direction='SHORT', action='OPEN', type='LIMIT', symbol='ETH_USDT', amount=0.1, price=450)
    # ret = client.send_order(direction='LONG', action='OPEN', type='LIMIT', symbol='ETH_USDT', amount=0.1, price=350)
    # ret = client.get_open_orders("ETH_USDT")
    # ret = client.get_open_order_ids(symbol='ETH_USDT')
    # ret = client.cancel_order(symbol='ETH_USDT', order_id='2892556980')
    # ret = client.cancel_orders(symbol='ETH_USDT', order_ids=[2892581474, 2892581810])
    # ret = client.get_order_book(symbol='ETH_USDT', limit=20)
    # ret = client.order_status_is_close(symbol='ETH_USDT', order_id=2892581810)
    # ret = client.transfer_to_future(asset='USDT', amount=5)
    # ret = client.transfer_from_future(asset='USDT', amount=5)
    # ret = client.get_klines_1hour(symbol="BTC_USDT", size=10)
    ret = client.get_klines_1day(symbol="BTC_USDT", size=10)
    
    print(ret)
