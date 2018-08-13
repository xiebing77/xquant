#!/usr/bin/python
"""strategy"""

import datetime
import logging
import uuid
import pandas as pd
from engine.realengine import RealEngine
from engine.backtest import BackTest
import common.xquant as xq


class Strategy:
    """Strategy"""

    def __init__(self, strategy_config, engine_config, debug):
        self.config = strategy_config
        self.debug_flag = debug

        self.instance_id = self.__class__.__name__ + "_" + self.config["symbol"] + "_"
        if engine_config["select"] == "real":
            self.instance_id += engine_config["real"]["instance_id"]  # 实盘则暂时由config配置
        else:
            self.instance_id += str(uuid.uuid1())  # 每次回测都是一个独立的实例

        logfilename = (
            self.instance_id + "_" + datetime.datetime.now().strftime("%Y%m%d") + ".log"
        )
        print(logfilename)
        logging.basicConfig(level=logging.NOTSET, filename=logfilename)

        logging.info(
            "strategy name: %s;  config: %s", self.__class__.__name__, self.config
        )

        if engine_config["select"] == "real":
            self.engine = RealEngine(self.instance_id, engine_config)
        else:
            self.engine = BackTest(self.instance_id, engine_config)

    def run(self):
        """ run """
        if self.debug_flag:
            self.engine.run(self)
        else:
            try:
                self.engine.run(self)
            except Exception as ept:
                logging.critical(ept)
