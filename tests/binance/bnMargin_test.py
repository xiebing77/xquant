#!/usr/bin/python3
import os
from exchange.binanceMargin import BinanceMargin
# from exchange.binance.enums import *

api_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_SECRET_KEY')

if __name__ == "__main__":
    client = BinanceMargin(debug=True)
    # ret = client.get_account()
    # ret = client.transfer_to_margin(asset='BTC', amount=0.01)
    # ret = client.transfer_from_margin(asset='BTC', amount=0.01)
    # ret = client.loan(asset='USDT', amount='0.01')
    # ret = client.repay(asset='USDT', amount='0.01')
    # ret = client.get_loan(asset='USDT', startTime=1570700000000)
    # ret = client.get_repay(asset='USDT', startTime=1570700000000)
    # ret = client.get_klines_1hour(symbol="BTC_USDT", size=10)
    # ret = client.get_klines_1day(symbol="BTC_USDT", size=10)
    # ret = client.get_balances("USDT")
    # ret = client.get_trades("BTC_USDT")
    # ret = client.get_deals("BTC_USDT")
    # ret = client.get_open_orders("BTC_USDT")
    # ret = client.get_open_order_ids(symbol='ETH_USDT')
    # ret = client.get_order_book(symbol='ETH_USDT', limit=20)
    # ret = client.order_status_is_close(symbol='BTC_USDT', order_id=726519783)
    # ret = client.send_order(direction='SHORT', action='OPEN', type='LIMIT', symbol='ETH_USDT', amount=0.234123, price=200)
    ret = client.send_order(direction='LONG', action='OPEN', type='LIMIT', symbol='ETH_USDT', amount=10000.12234, price=80.213)
    # ret = client.cancel_order(symbol='ETH_USDT', order_id='498421194')
    # ret = client.cancel_orders(symbol='ETH_USDT', order_ids=[498425779, 498425781, 498426026, 498426027, 498424836])
    
    print(ret)
