#!/usr/bin/python3
import sys
import json
from datetime import datetime
import common.log as log
import uuid
from multiprocessing import cpu_count
import utils.tools as ts
from engine.realengine import RealEngine
from engine.backtest import BackTest
from engine.backtestsearch import BackTestSearch
from engine.multisearch import MultiSearch

def help_print():
    print("./xp.sh config/kdjmacd_btc_usdt.jsn  real         xbtc1               100  True  实盘，debug默认是关闭的")
    print("./xp.sh config/kdjmacd_btc_usdt.jsn  backtest     2018-12-1~2019-1-1             回测")
    print("./xp.sh config/kdjmacd_btc_usdt.jsn  search       2018-12-1~2019-1-1             寻优")
    print("./xp.sh config/kdjmacd_btc_usdt.jsn  multisearch  2018-12-1~2019-1-1             多进程寻优")

def parse_date_range(date_range):
    print("time range: [ %s )" % date_range)
    dates = date_range.split("~")

    start_time = datetime.strptime(dates[0], "%Y-%m-%d")
    end_time = datetime.strptime(dates[1], "%Y-%m-%d")
    return start_time, end_time


if __name__ == "__main__":

    print(sys.argv)
    params_index = 1
    fo = open(sys.argv[params_index], "r")
    params_index += 1
    config = json.loads(fo.read())
    fo.close()
    print("config: ", config)

    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]

    select = sys.argv[params_index]
    params_index += 1
    print("select: ", select)

    if select == "real":
        if len(sys.argv) > params_index:
            instance_id = sys.argv[params_index]
            params_index += 1
        else:
            help_print()
            exit(1)

        if len(sys.argv) > params_index:
            value = float(sys.argv[params_index])
            params_index += 1
        else:
            help_print()
            exit(1)

        if len(sys.argv) > params_index:
            debug = bool(sys.argv[params_index])
            params_index += 1
        else:
            debug = False

        print("value: %s, debug: %s" % (value, debug))

        logfilename = instance_id + ".log"
    elif select == "backtest" or select == "search" or select == "multisearch":
        instance_id = str(uuid.uuid1())  # 每次回测都是一个独立的实例

        if len(sys.argv) > params_index:
            date_range = sys.argv[params_index]
            params_index += 1
        else:
            help_print()
            exit(1)

        logfilename = (
            select
            +"_"
            + class_name
            + "_"
            + config["symbol"]
            + "_"
            + date_range
            + "_"
            + instance_id
            + ".log"
        )
        start_time, end_time = parse_date_range(date_range)

    else:
        help_print()
        exit(1)

    print(logfilename)
    log.init(logfilename)

    log.info("strategy name: %s;  config: %s" % (class_name, config))

    if select == "real":
        engine = RealEngine(instance_id, config)
        strategy = ts.createInstance(module_name, class_name, config, engine)

        engine.value = value
        engine.run(strategy, debug)

    elif select == "backtest":
        engine = BackTest(instance_id, config)
        strategy = ts.createInstance(module_name, class_name, config, engine)

        engine.run(strategy, start_time, end_time)

    elif select == "search":
        engine = BackTestSearch(instance_id, config)
        strategy = ts.createInstance(module_name, class_name, config, engine)
        if len(sys.argv) > params_index:
            count = int(sys.argv[params_index])
            params_index += 1
        else:
            count = 10
        print("count: ", count)
        engine.run(count, strategy, start_time, end_time)

    elif select == "multisearch":
        if len(sys.argv) > params_index:
            count = int(sys.argv[params_index])
            params_index += 1
        else:
            count = 10
        print("count: ", count)

        if len(sys.argv) > params_index:
            cpus = int(sys.argv[params_index])
            params_index += 1
        else:
            cpus = cpu_count()
        print("cpus: ", cpus)

        bts_engine = MultiSearch(instance_id, config)
        bts_engine.run(count, cpus, module_name, class_name, config, start_time, end_time)

    else:
        print("select engine error!")
        exit(1)

