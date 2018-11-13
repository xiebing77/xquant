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
    print("./xp.sh config/kdjmacd_btc_usdt.jsn real True       实盘，debug默认是关闭的")
    print("./xp.sh config/kdjmacd_btc_usdt.jsn backtest        回测")
    print("./xp.sh config/kdjmacd_btc_usdt.jsn search          寻优")
    print("./xp.sh config/kdjmacd_btc_usdt.jsn multisearch     多进程寻优")


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
        instance_id = config["real"]["instance_id"]  # 实盘则暂时由config配置
        logfilename = instance_id + ".log"
    elif select == "backtest" or select == "search" or select == "multisearch":
        instance_id = str(uuid.uuid1())  # 每次回测都是一个独立的实例

        start_time = datetime.strptime(
            config["backtest"]["start_time"], "%Y-%m-%d %H:%M:%S"
        )
        end_time = datetime.strptime(
            config["backtest"]["end_time"], "%Y-%m-%d %H:%M:%S"
        )

        logfilename = (
            select
            +"_"
            + class_name
            + "_"
            + config["symbol"]
            + "_"
            + start_time.strftime("%Y%m%d")
            + "_"
            + end_time.strftime("%Y%m%d")
            + "_"
            + instance_id
            + ".log"
        )
    else:
        help_print()
        exit(1)

    print(logfilename)
    log.init(logfilename)

    log.info("strategy name: %s;  config: %s" % (class_name, config))
    log.info("engine config: %s" % config)

    if select == "real":
        engine = RealEngine(instance_id, config)
        strategy = ts.createInstance(module_name, class_name, config, engine)

        if len(sys.argv) > params_index:
            debug = bool(sys.argv[params_index])
            params_index += 1
        else:
            debug = False
        print("debug: ", debug)
        engine.run(strategy, debug)

    elif select == "backtest":
        engine = BackTest(instance_id, config)
        strategy = ts.createInstance(module_name, class_name, config, engine)
        engine.run(strategy)

    elif select == "search":
        engine = BackTestSearch(instance_id, config)
        strategy = ts.createInstance(module_name, class_name, config, engine)
        if len(sys.argv) > params_index:
            count = int(sys.argv[params_index])
            params_index += 1
        else:
            count = 10
        print("count: ", count)
        engine.run(count, strategy)

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
        bts_engine.run(count, cpus, module_name, class_name, config)

    else:
        print("select engine error!")
        exit(1)

