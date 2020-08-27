#!/usr/bin/python3.6
import argparse
import time
import db.mongodb as md
import re
from utils.email_obj import EmailObj
from setup import *

# Example:
# python3.6 insert_trade.py -i gbtc -d buy -s btc_usdt -p 11000.23 -a 1.11

db_name = trade_db_name
collection = 'orders'
record = {
    "create_time": time.time(),
    "instance_id": "",
    "symbol": "",
    "direction": "LONG",
    "action":"",
    "pst_rate": 0,
    "type": "LIMIT",
    "market_price": 0,
    "price": 0,
    "amount": 0,
    "status": "close",
    "order_id": 264988599,
    "cancle_amount": 0,
    "deal_amount": 0,
    "deal_value":  0,
    "rmk": " "
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Insert trade')
    parser.add_argument('-i', help='Instance')
    parser.add_argument('-d', help='Buy or sell')
    parser.add_argument('-s', help='Symbol like btc_usdt')
    parser.add_argument('-p', help='Price', type=float)
    parser.add_argument('-a', help='Amount', type=float)

    args = parser.parse_args()
    print(args)
    if not (args.i and args.d and args.s and args.p and args.a):
        parser.print_help()
        exit(1)

    record['instance_id'] = args.i
    record['symbol'] = args.s.lower()
    side = args.d.upper()
    if side == 'BUY':
        record['action'] = 'OPEN'
    else:
        record['action'] = 'CLOSE'
    record['price'] = record['market_price'] = args.p
    record['amount'] = record['deal_amount'] = args.a
    record['deal_value'] = round(record['price'] * record['deal_amount'], 2)

    print('record:', record)
    db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)
    db.insert_one(collection, record)
