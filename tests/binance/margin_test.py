#!/usr/bin/python3
import os
from exchange.binance.margin import Client
from exchange.binance.enums import *

api_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_SECRET_KEY')

if __name__ == "__main__":
    client = Client(api_key, secret_key)
    # ret = client.transfer(asset='USDT', amount='10', type=1)
    # ret = client.transfer(asset='USDT', amount='0.1', type=2)
    # ret = client.loan(asset='USDT', amount='0.01')
    # ret = client.repay(asset='USDT', amount='0.01')
    # ret = client.order_limit_buy(symbol='ETHUSDT', quantity=0.1, price=180)
    # ret = client.transfer(asset='ETH', amount='0.1', type=1)
    # ret = client.order_limit_sell(symbol='ETHUSDT', quantity=0.1, price=200)
    # print(ret)
    # ret = client.cancel_order(symbol='ETHUSDT', orderId='445856389')
    # ret = client.get_order(symbol='ETHUSDT', orderId='445862537')
    # ret = client.get_open_order()
    # ret = client.get_all_orders(symbol='ETHUSDT')
    # ret = client.get_loan(asset='USDT', startTime=1570700000000)
    # ret = client.get_repay(asset='USDT', startTime=1570700000000)
    # ret = client.get_account()
    # ret = client.get_asset(asset='ETH')
    # ret = client.get_pair(symbol='ETHUSDT')
    # ret = client.get_all_assets()
    ret = client.get_all_pairs()
    # ret = client.get_price_index(symbol='ETHUSDT')
    # ret = client.get_transfer_history(asset='ETH', type='ROLL_IN')
    # ret = client.get_transfer_history(type='ROLL_OUT')
    # ret = client.get_interest_history()
    # ret = client.get_force_liquidation_record()
    # ret = client.get_my_trades(symbol='ETHUSDT')
    # ret = client.get_max_borrowable(asset='ETH')
    # ret = client.get_max_transferable(asset='USDT')
    # ret = client.stream_get_listen_key()
    # ret = client.stream_keepalive(listenKey='BpJlFdbgdqQm9n7WQHG2URKSeu8qF1NZxFY02YgcyWzXNSMvHS065qNdJZqq')
    # ret = client.stream_close(listenKey='BpJlFdbgdqQm9n7WQHG2URKSeu8qF1NZxFY02YgcyWzXNSMvHS065qNdJZqq')
    
    print(ret)
