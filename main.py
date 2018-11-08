#!/usr/bin/python3
import sys
import json
from datetime import datetime
import common.log as log
import uuid
import utils.tools as ts
from engine.realengine import RealEngine
from engine.backtest import BackTest
from engine.backtestsearch import BackTestSearch
from engine.multisearch import MultiSearch


if __name__ == "__main__":

    #print(sys.argv)
    module_name = sys.argv[1].replace("/", ".")

    class_name = sys.argv[2]

    strategy_config = json.loads(sys.argv[3])
    print(strategy_config)

    engine_config = json.loads(sys.argv[4])
    print(engine_config)

    select = sys.argv[5]
    print("select: ", select)

    if len(sys.argv) >= 7:
        debug = bool(sys.argv[6])
    else:
        debug = False
    print("debug: ", debug)

    if select == "real":
        instance_id = engine_config["real"]["instance_id"]  # 实盘则暂时由config配置
        logfilename = instance_id + ".log"
    else:
        instance_id = str(uuid.uuid1())  # 每次回测都是一个独立的实例

        start_time = datetime.strptime(
            engine_config["backtest"]["start_time"], "%Y-%m-%d %H:%M:%S"
        )
        end_time = datetime.strptime(
            engine_config["backtest"]["end_time"], "%Y-%m-%d %H:%M:%S"
        )

        logfilename = (
            select
            +"_"
            + class_name
            + "_"
            + strategy_config["symbol"]
            + "_"
            + start_time.strftime("%Y%m%d")
            + "_"
            + end_time.strftime("%Y%m%d")
            + "_"
            + instance_id
            + ".log"
        )

    print(logfilename)
    log.init(logfilename)

    log.info("strategy name: %s;  config: %s" % (class_name, strategy_config))
    log.info("engine config: %s" % engine_config)

    if select == "real":
        engine = RealEngine(instance_id, engine_config)
        strategy = ts.createInstance(module_name, class_name, strategy_config, engine)
        engine.run(strategy, debug)

    elif select == "backtest":
        engine = BackTest(instance_id, engine_config)
        strategy = ts.createInstance(module_name, class_name, strategy_config, engine)
        engine.run(strategy)

    elif select == "search":
        engine = BackTestSearch(instance_id, engine_config)
        strategy = ts.createInstance(module_name, class_name, strategy_config, engine)
        engine.run(strategy)

    elif select == "multisearch":
        bts_engine = MultiSearch(instance_id, engine_config)
        count = strategy_config["search"]["count"]
        bts_engine.run(count, module_name, class_name, strategy_config)

    else:
        print("select engine error!")
        exit(1)

