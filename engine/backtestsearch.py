#!/usr/bin/python
"""回测求解最优引擎"""
import sys
from datetime import datetime, timedelta, time
import uuid
import utils.tools as ts
import common.xquant as xq
from .backtest import BackTest


class BackTestSearch(BackTest):
    """回测求解最优引擎"""

    def __init__(self, instance_id, config, *symbols):
        super().__init__(instance_id, config)

    def log_info(self, info):
        return

    def handle_one(self, strategy, start_time, end_time):
        self.orders = []

        total_tick_start = datetime.now()
        self.tick_time = start_time
        tick_count = 0
        while self.tick_time < end_time:
            tick_start = datetime.now()

            strategy.on_tick()

            tick_end = datetime.now()

            tick_count += 1
            self.tick_time += timedelta(seconds=strategy.config["sec"])
            progress = (self.tick_time - start_time).total_seconds() / (
                end_time - start_time
            ).total_seconds()
            sys.stdout.write(
                "  tick: %d - %s,  cost: %s,  progress: %d%% \r"
                % (
                    tick_count,
                    self.tick_time.strftime("%Y-%m-%d %H:%M:%S"),
                    tick_end - total_tick_start,
                    progress * 100,
                )
            )
            sys.stdout.flush()
        print("")

        symbol = strategy.config["symbol"]
        return self.calc(symbol, self.orders)

    def run(self, strategy, debug):
        """ run """
        print(
            "backtest time range: [ %s , %s )"
            % (
                self.config["backtest"]["start_time"],
                self.config["backtest"]["end_time"],
            )
        )

        start_time = datetime.strptime(
            self.config["backtest"]["start_time"], "%Y-%m-%d %H:%M:%S"
        )
        end_time = datetime.strptime(
            self.config["backtest"]["end_time"], "%Y-%m-%d %H:%M:%S"
        )

        count = strategy.config["search"]["count"]
        result = []
        for i in range(count):
            print("%d/%d " % (i, count), end="  ")
            rs = strategy.search_init()
            result.append((i, rs, self.handle_one(strategy, start_time, end_time)))

        sorted_rs = sorted(result, key=lambda x: x[2][0], reverse=True)
        
        for r in sorted_rs:
            print(r)
            self.log_debug(" %s  %s  %s " % r)


