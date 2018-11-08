#!/usr/bin/python
"""回测求解最优引擎"""
import sys
from datetime import datetime, timedelta, time
from multiprocessing import cpu_count, Queue, Pool, Manager
import uuid
import os
import time
import utils.tools as ts
import common.xquant as xq
from .backtest import BackTest


def child_process(name, task_q, result_q, instance_id, engine_config, module_name, class_name, strategy_config, start_time, end_time):
    #print("child process name %s, id %s start" % (name, os.getpid()))

    child_engine = MultiSearchChild(instance_id, engine_config)
    child_strategy = ts.createInstance(module_name, class_name, strategy_config, child_engine)

    while not task_q.empty():
        value = task_q.get(True, 1)
        rs = child_strategy.search_init()
        print("child_process(%s)  %s, rs: %s" % (name, value, rs))

        result_q.put((value, child_engine.handle_one(child_strategy, start_time, end_time), rs))

    #print("child process name %s, id %s finish" % (name, os.getpid()))

class MultiSearchChild(BackTest):
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

        symbol = strategy.config["symbol"]
        return self.calc(symbol, self.orders)

class MultiSearch(BackTest):
    """回测求解最优引擎"""

    def __init__(self, instance_id, config, *symbols):
        super().__init__(instance_id, config)

    def run(self, count, module_name, class_name, strategy_config):
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

        result_q = Manager().Queue()#Manager中的Queue才能配合Pool
        task_q = Manager().Queue()#Manager中的Queue才能配合Pool
        for index in range(count):
            task_q.put(index)

        #print('Parent process %s.' % os.getpid())
        cpu_num = cpu_count()
        """
        if cpu_count > 1:
            cpu_count -= 1
        """
        p = Pool(cpu_num)
        for i in range(cpu_num):
            #p.apply_async(child_process_test, args=(i, task_q, result_q))
            p.apply_async(child_process, args=(i, task_q, result_q, self.instance_id, self.config, module_name, class_name, strategy_config, start_time, end_time))
        print('Waiting for all subprocesses done...')
        p.close()

        start_time = datetime.now()
        while result_q.qsize() < count:
            time.sleep(1)
            q_len = result_q.qsize()
            sys.stdout.write(
                "  %d/%d,  cost: %s,  progress: %d%% \r"
                % (
                    result_q.qsize(),
                    count,
                    datetime.now() - start_time,
                    (q_len / count) * 100,
                )
            )
            sys.stdout.flush()
        print("")
        #print("result queue(len: %s)" % (result_q.qsize()))

        p.join()
        print('All subprocesses done.')

        #print("result queue(len: %s) process start!"%(result_q.qsize()))
        result = []
        while not result_q.empty():
            value = result_q.get()
            #print("result queue get value: ", (value))
            result.append(value)
        #print("result queue process finish")

        sorted_rs = sorted(result, key=lambda x: x[1][0], reverse=True)
        for r in sorted_rs:
            #print("r: ", r)
            info = "%6s    %30s    %s " % r
            print(info)
            self.log_debug(info)


