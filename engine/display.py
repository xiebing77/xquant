#!/usr/bin/python
"""回测求解最优引擎"""
import sys
from datetime import datetime, timedelta, time
import uuid
import utils.tools as ts
import common.xquant as xq
import common.kline as kl
from .engine import Engine
from setup import mongo_user, mongo_pwd, db_url
import db.mongodb as md


class Display(Engine):
    """回测求解最优引擎"""

    def __init__(self, instance_id, config, *symbols):
        super().__init__(instance_id, config)

    def log_info(self, info):
        return

    def run(self, strategy, db_name):
        """ run """
        symbol = strategy.config["symbol"]

        db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)
        orders = db.find("orders", {"instance_id": self.instance_id})

        self.analyze(symbol, orders)

       # if display_switch:
        #interval = strategy.config["kline"]["interval"]
        #klines = self.get_klines(symbol, interval, (end_time - start_time).total_seconds()/kl.get_interval_seconds(interval))
        #self.display(symbol, orders, klines)        

