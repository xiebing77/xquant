#!/usr/bin/python3
import sys
import os
#sys.path.append('../')
import argparse
import time
import copy
from datetime import datetime, timedelta
from multiprocessing import Queue, Pool, Manager
from multiprocessing import cpu_count
import uuid
import pprint
import utils.tools as ts
import common.xquant as xq
import common.kline as kl
import common.log as log
from exchange.exchange import get_exchange_names
from exchange.binanceExchange import BinanceExchange
import exchange.okex
from engine.backtestengine import BackTest
from engine.signalengine import TestSignal
from chart.chart import chart, chart_add_all_argument
from db.mongodb import get_mongodb
from md.dbmd import DBMD

BACKTEST_INSTANCES_COLLECTION_NAME = 'bt_instances'

bt_db = get_mongodb('backtest')

def create_instance_id():
    instance_id = datetime.now().strftime("%Y%m%d-%H%M%S_") + str(uuid.uuid1())  # 每次回测都是一个独立的实例
    print('new id of instance: %s' % instance_id)
    return instance_id

def get_time_range(md, symbol, time_range):
    if time_range:
        start_time, end_time = ts.parse_date_range(time_range)
    else:
        start_time = end_time = None
    oldest_time = md.get_oldest_time(symbol, kl.KLINE_INTERVAL_1MINUTE)
    if not start_time or start_time < oldest_time:
        start_time = oldest_time
    latest_time = md.get_latest_time(symbol, kl.KLINE_INTERVAL_1MINUTE)
    if not end_time or end_time > latest_time:
        end_time = latest_time
    print("  time range: %s ~ %s" % (start_time.strftime("%Y-%m-%d %H:%M:%S"), end_time.strftime("%Y-%m-%d %H:%M:%S")))
    return start_time, end_time


def run(engine, md, strategy, start_time, end_time):
    """ run """
    secs = strategy.config["sec"]
    if secs < 60:
        secs = 60
    td_secs = timedelta(seconds=secs)

    pre_tick_cost_time = total_tick_cost_start = datetime.now()
    md.tick_time = start_time
    tick_count = 0
    while md.tick_time < end_time:
        engine.log_info("tick_time: %s" % md.tick_time.strftime("%Y-%m-%d %H:%M:%S"))

        strategy.on_tick()

        tick_cost_time = datetime.now()
        engine.log_info("tick  cost: %s \n\n" % (tick_cost_time - pre_tick_cost_time))

        tick_count += 1
        md.tick_time += td_secs
        progress = (md.tick_time - start_time).total_seconds() / (
            end_time - start_time
        ).total_seconds()
        sys.stdout.write(
            "%s  progress: %d%%,  cost: %s,  tick: %s\r"
            % (
                " "*36,
                progress * 100,
                tick_cost_time - total_tick_cost_start,
                md.tick_time.strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
        sys.stdout.flush()

    return tick_count


def update_kl(md, kl, tick_kl):
    kl[md.kline_key_close] = tick_kl[md.kline_key_close]
    kl[md.kline_key_close_time] = tick_kl[md.kline_key_close_time]
    if kl[md.kline_key_high] < tick_kl[md.kline_key_high]:
        kl[md.kline_key_high] = tick_kl[md.kline_key_high]
    if kl[md.kline_key_low] > tick_kl[md.kline_key_low]:
        kl[md.kline_key_low] = tick_kl[md.kline_key_low]


def run2(engine, md, strategy, start_time, end_time, progress_disp=True):
    """ run advance"""
    secs = strategy.config["sec"]
    if secs < 60:
        secs = 60
    td_secs = timedelta(seconds=secs)

    if "micro_interval" in strategy.config["kline"]:
        return run_2kls(engine, md, strategy, start_time, end_time, progress_disp)
    else:
        return run_1kls(engine, md, strategy, start_time, end_time, progress_disp)


def run_1kls(engine, md, strategy, start_time, end_time, progress_disp=True):
    symbol = strategy.config["symbol"]

    tick_interval = kl.KLINE_INTERVAL_1MINUTE
    tick_collection = kl.get_kline_collection(symbol, tick_interval)
    tick_td = kl.get_interval_timedelta(tick_interval)

    kline_cfg = strategy.config["kline"]
    size = kline_cfg["size"]

    master_interval = kline_cfg["interval"]
    master_td = kl.get_interval_timedelta(master_interval)
    master_kls = md.get_original_klines(kl.get_kline_collection(symbol, master_interval),
        start_time - master_td * size, end_time)

    if hasattr(strategy, "before_backtest"):
        strategy.before_backtest(master_kls)

    for i in range(size+1):
        if md.get_kline_open_time(master_kls[i]) >= start_time:
            break
    master_idx = i

    pre_tick_cost_time = total_tick_cost_start = datetime.now()
    tick_count = 0
    for i in range(master_idx, len(master_kls)):
        start_i = i - size
        if start_i < 0:
            start_i = 0
        history_master_kls = master_kls[start_i:i]

        master_open_time = md.get_kline_open_time(master_kls[i])

        tick_klines = md.get_original_klines(tick_collection, master_open_time, master_open_time + master_td)
        for j, tick_kl in enumerate(tick_klines):
            tick_open_time = md.get_kline_open_time(tick_kl)
            engine.log_info("tick_time: %s" % tick_open_time.strftime("%Y-%m-%d %H:%M:%S"))
            #print(tick_open_time)
            if j == 0:
                new_master_kl = tick_kl
            else:
                update_kl(md, new_master_kl, tick_kl)

            kls = history_master_kls + [new_master_kl]
            if md.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
                kls = kl.trans_from_json_to_list(kls, md.kline_column_names)
            md.tick_time = tick_open_time + tick_td

            strategy.on_tick(kls)

            tick_cost_time = datetime.now()
            engine.log_info("tick  cost: %s \n\n" % (tick_cost_time - pre_tick_cost_time))
            pre_tick_cost_time = tick_cost_time
            tick_count += 1

        if progress_disp:
            progress = (i + 1 - master_idx) / (len(master_kls) - master_idx)
            sys.stdout.write(
                "%s  progress: %d%%,  cost: %s, next open time: %s\r"
                % (
                    " "*36,
                    progress * 100,
                    tick_cost_time - total_tick_cost_start,
                    (master_open_time+master_td).strftime("%Y-%m-%d %H:%M:%S"),
                )
            )
            sys.stdout.flush()

    return tick_count


def run_2kls(engine, md, strategy, start_time, end_time, progress_disp=True):
    symbol = strategy.config["symbol"]

    tick_interval = kl.KLINE_INTERVAL_1MINUTE
    tick_collection = kl.get_kline_collection(symbol, tick_interval)
    tick_td = kl.get_interval_timedelta(tick_interval)

    kline_cfg = strategy.config["kline"]
    size = kline_cfg["size"]

    master_interval = kline_cfg["interval"]
    master_td = kl.get_interval_timedelta(master_interval)
    master_original_kls = md.get_original_klines(kl.get_kline_collection(symbol, master_interval),
        start_time - master_td * size, end_time)

    micro_interval = kline_cfg["micro_interval"]
    micro_td = kl.get_interval_timedelta(micro_interval)
    micro_original_kls = md.get_original_klines(kl.get_kline_collection(symbol, micro_interval),
        start_time - micro_td * size, end_time)

    if hasattr(strategy, "before_backtest"):
        strategy.before_backtest(master_original_kls, micro_original_kls)

    for master_start_idx in range(size+1):
        master_start_open_time = md.get_kline_open_time(master_original_kls[master_start_idx])+master_td
        if master_start_open_time >= start_time:
            break

    for micro_idx in range(size+1+int(master_td/micro_td)):
        micro_start_open_time = md.get_kline_open_time(micro_original_kls[micro_idx]) + micro_td
        if micro_start_open_time >= master_start_open_time:
            break

    pre_tick_cost_time = total_tick_cost_start = datetime.now()
    tick_count = 0
    tick_klines = []
    tick_idx = 0
    for master_idx in range(master_start_idx, len(master_original_kls)):
        pre_start_i = master_idx - size
        if pre_start_i < 0:
            pre_start_i = 0
        history_master_kls = master_original_kls[pre_start_i:master_idx+1]

        new_master_open_time = md.get_kline_open_time(history_master_kls[-1]) + master_td
        new_master_close_time = new_master_open_time + master_td
        new_master_kl = None
        #print("new master open time: %s" % (new_master_open_time))

        if tick_idx >= len(tick_klines):
            tick_klines = md.get_original_klines(tick_collection, new_master_open_time, new_master_open_time + 7*master_td)
            tick_idx = 0

        while (micro_idx < len(micro_original_kls)):
            if md.get_kline_open_time(micro_original_kls[micro_idx]) + micro_td >= new_master_close_time:
                break
            if micro_idx > size:
                history_micro_kls = micro_original_kls[(micro_idx - size):micro_idx+1]
            else:
                history_micro_kls = micro_original_kls[:micro_idx+1]
            micro_idx += 1

            new_micro_open_time = md.get_kline_open_time(history_micro_kls[-1]) + micro_td
            new_micro_close_time = new_micro_open_time + micro_td
            new_micro_kl = None
            #print("new micro open time: %s" % (new_micro_open_time))

            while (tick_idx < len(tick_klines)):
                tick_kl = tick_klines[tick_idx]
                tick_open_time = md.get_kline_open_time(tick_kl)
                if tick_open_time >= new_micro_close_time:
                    break
                tick_idx += 1
                engine.log_info("tick_time: %s" % tick_open_time.strftime("%Y-%m-%d %H:%M:%S"))
                #print(tick_open_time)

                if not new_master_kl:
                    new_master_kl = copy.copy(tick_kl)
                else:
                    update_kl(md, new_master_kl, tick_kl)
                master_kls = history_master_kls + [new_master_kl]

                if not new_micro_kl:
                    new_micro_kl = copy.copy(tick_kl)
                else:
                    update_kl(md, new_micro_kl, tick_kl)
                micro_kls = history_micro_kls + [new_micro_kl]

                if md.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
                    master_kls = kl.trans_from_json_to_list(master_kls, md.kline_column_names)
                    micro_kls = kl.trans_from_json_to_list(micro_kls, md.kline_column_names)
                md.tick_time = tick_open_time + tick_td

                strategy.on_tick(master_kls, micro_kls)

                tick_cost_time = datetime.now()
                engine.log_info("tick  cost: %s \n\n" % (tick_cost_time - pre_tick_cost_time))
                pre_tick_cost_time = tick_cost_time
                tick_count += 1


        if progress_disp:
            progress = (master_idx + 1 - master_start_idx) / (len(master_original_kls) - master_start_idx)
            sys.stdout.write(
                "%s  progress: %d%%,  cost: %s, open time: %s\r"
                % (
                    " "*36,
                    progress * 100,
                    tick_cost_time - total_tick_cost_start,
                    new_master_open_time.strftime("%Y-%m-%d %H:%M:%S"),
                )
            )
            sys.stdout.flush()

    return tick_count

def refresh(engine, md, strategy, times):
    """ refresh """
    total_tick_count = len(times)
    total_tick_start = datetime.now()
    tick_count = 0
    for t in times:
        md.tick_time = t
        engine.log_info("tick_time: %s" % md.tick_time.strftime("%Y-%m-%d %H:%M:%S"))
        tick_start = datetime.now()

        strategy.on_tick()

        tick_end = datetime.now()
        engine.log_info("tick  cost: %s \n\n" % (tick_end - tick_start))

        tick_count += 1
        progress = tick_count / total_tick_count
        sys.stdout.write(
            "%s  progress: %d%%,  cost: %s,  tick: %s\r"
            % (
                " "*36,
                progress * 100,
                tick_end - total_tick_start,
                md.tick_time.strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
        sys.stdout.flush()

    total_tick_end = datetime.now()
    print(
        "\n  total tick count: %d cost: %s"
        % (tick_count, total_tick_end - total_tick_start)
    )


def sub_cmd_signal(args):
    if not (args.m and args.sc):
        exit(1)

    instance_id = create_instance_id()

    config = xq.get_strategy_config(args.sc)
    pprint.pprint(config)

    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]

    symbol = config['symbol']
    interval = config["kline"]["interval"]

    if args.log:
        logfilename = class_name + "_"+ symbol + "_" + instance_id + ".log"
        print(logfilename)
        log.init("testsignal", logfilename)
        log.info("strategy name: %s;  config: %s" % (class_name, config))

    md = DBMD(args.m, kl.KLINE_DATA_TYPE_JSON)
    engine = TestSignal(md, instance_id, config, args.log)
    strategy = ts.createInstance(module_name, class_name, config, engine)
    start_time, end_time = get_time_range(md, symbol, args.r)

    print("run2  kline_data_type: %s "% (md.kline_data_type))
    tick_count = run2(engine, md, strategy, start_time, end_time)
    print("\n  total tick count: %d" % (tick_count))

    #pprint.pprint(engine.signals)
    print("signal count: ", len(engine.signals))
    '''
    _id = bt_db.insert_one(
        BACKTEST_INSTANCES_COLLECTION_NAME,
        {
            "instance_id": instance_id,
            "start_time": start_time,
            "end_time": end_time,
            "signals": engine.signals,
            "mds": args.m,
            "sc": args.sc,
        },
    )
    '''
    if args.chart:
        signalsets = engine.get_signalsets()
        title = "signal:  " + symbol + '  ' + config['kline']['interval'] + ' '
        if strategy.name:
            title += strategy.name
        else:
            title += config['class_name']
        chart(title, engine.md, symbol, interval, start_time, end_time, [], args, signalsets)


def sub_cmd_run(args):
    if not (args.m and args.sc):
        exit(1)

    instance_id = create_instance_id()
    config = xq.get_strategy_config(args.sc)
    pprint.pprint(config)

    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]
    symbol = config['symbol']
    if args.log:
        logfilename = class_name + "_"+ symbol + "_" + instance_id + ".log"
        print(logfilename)
        log.init("backtest", logfilename)
        log.info("strategy name: %s;  config: %s" % (class_name, config))

    engine = BackTest(instance_id, args.m, config, args.log)
    strategy = ts.createInstance(module_name, class_name, config, engine)
    md = engine.md
    start_time, end_time = get_time_range(md, symbol, args.r)

    print("run2  kline_data_type: %s "% (md.kline_data_type))
    tick_count = run2(engine, md, strategy, start_time, end_time)
    print("\n  total tick count: %d" % (tick_count))

    engine.analyze_orders(engine.orders)
    _id = bt_db.insert_one(
        BACKTEST_INSTANCES_COLLECTION_NAME,
        {
            "instance_id": instance_id,
            "start_time": start_time,
            "end_time": end_time,
            "orders": engine.orders,
            "mds": args.m,
            "sc": args.sc,
        },
    )

    engine.display(symbol, engine.orders, strategy.cur_price, end_time, True, args.rmk)

    if args.chart:
        ordersets = []
        ordersets.append(engine.orders)
        chart(md, engine.config, start_time, end_time, ordersets, args)


def sub_cmd_search(args):
    if not (args.m and args.sc):
        exit(1)

    instance_id = create_instance_id()
    config = xq.get_strategy_config(args.sc)
    pprint.pprint(config)

    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]
    symbol = config['symbol']
    engine = BackTest(instance_id, args.m, config, args.log)
    strategy = ts.createInstance(module_name, class_name, config, engine)
    md = engine.md
    start_time, end_time = get_time_range(md, symbol, args.r)

    count = args.count
    result = []
    for i in range(count):
        rs = strategy.search_init()
        print("%d/%d    %s" % (i, count, rs))
        tick_count = run2(engine, md, strategy, start_time, end_time)
        result.append((i, rs, engine.search_calc(symbol, engine.orders)))
        engine.orders = []

    sorted_rs = sorted(result, key=lambda x: x[2][0], reverse=True)
    for r in sorted_rs:
        info = "%6s    %30s    %s " % r
        print(info)
        engine.log_debug(info)


def child_process(name, task_q, result_q, md_name, config, module_name, class_name, start_time, end_time):
    #print("child process name %s, id %s start" % (name, os.getpid()))

    engine = BackTest(create_instance_id(), md_name, config)
    strategy = ts.createInstance(module_name, class_name, config, engine)
    while not task_q.empty():
        value = task_q.get(True, 1)
        rs = strategy.search_init()
        #print("child_process(%s)  %s, rs: %s" % (name, value, rs))
        tick_count = run2(engine, engine.md, strategy, start_time, end_time, False)
        #print("tick_count: %s" % (tick_count) )
        symbol = config['symbol']
        result_q.put((value, engine.search_calc(symbol, engine.orders), rs))
        engine.orders = []

    #print("child process name %s, id %s finish" % (name, os.getpid()))
    return


def sub_cmd_multisearch(args):
    if not (args.m and args.sc):
        exit(1)

    config = xq.get_strategy_config(args.sc)
    pprint.pprint(config)

    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]
    symbol = config['symbol']
    md = DBMD(args.m, kl.KLINE_DATA_TYPE_JSON)
    start_time, end_time = get_time_range(md, symbol, args.r)

    count = args.count
    cpus = cpu_count()
    print("count: %s,  cpus: %s" % (count, cpus) )

    result_q = Manager().Queue()#Manager中的Queue才能配合Pool
    task_q = Manager().Queue()#Manager中的Queue才能配合Pool
    for index in range(count):
        task_q.put(index)

    print('Parent process %s.' % os.getpid())
    p = Pool(cpus)
    for i in range(cpus):
        #p.apply_async(child_process_test, args=(i, task_q, result_q))
        p.apply_async(child_process, args=(i, task_q, result_q, args.m, config, module_name, class_name, start_time, end_time))
    print('Waiting for all subprocesses done...')
    p.close()

    start_time = datetime.now()
    result = []
    while len(result) < count:
        if result_q.empty():
            time.sleep(1)
        else:
            value = result_q.get()
            print("result value: ", value)
            result.append(value)

        sys.stdout.write(
            "  %d/%d,  cost: %s,  progress: %g%% \r"
            % (
                len(result),
                count,
                datetime.now() - start_time,
                round((len(result) / count) * 100, 2)
            )
        )
        sys.stdout.flush()

    print("")
    #print("result queue(len: %s)" % (result_q.qsize()))

    p.join()
    print('All subprocesses done.')

    sorted_rs = sorted(result, key=lambda x: x[1][0], reverse=True)
    for r in sorted_rs:
        #print("r: ", r)
        info = "%6s    %30s    %s " % r
        print(info)
        #engine.log_debug(info)


def get_instance(instance_id):
    if not (instance_id):
        exit(1)

    instances = bt_db.find(
        BACKTEST_INSTANCES_COLLECTION_NAME,
        {"instance_id": instance_id}
    )
    #print("instances: %s" % instances)
    if len(instances) <= 0:
        exit(1)
    instance = instances[0]
    return instance


def view(args):
    instance_id = args.sii
    instance = get_instance(instance_id)

    config = xq.get_strategy_config(instance['sc'])

    engine = BackTest(instance_id, instance['mds'], config)
    engine.view(config['symbol'], instance['orders'])


def analyze(args):
    instance_id = args.sii
    instance = get_instance(instance_id)
    print('marketing data src: %s  strategy config path: %s  ' % (instance['mds'], instance['sc']))

    config = xq.get_strategy_config(instance['sc'])
    pprint.pprint(config, indent=4)

    engine = BackTest(instance_id, instance['mds'], config)
    engine.analyze(config['symbol'], instance['orders'], args.hl, args.rmk, args.deal, args.lock)


def sub_cmd_continue(args):
    old_instance = get_instance(args.sii)
    mds_name = old_instance['mds']
    sc = old_instance['sc']
    print('marketing data src: %s  strategy config path: %s  ' % (mds_name, sc))

    config = xq.get_strategy_config(sc)
    pprint.pprint(config, indent=4)

    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]
    symbol = config['symbol']

    instance_id = create_instance_id()
    if args.log:
        logfilename = class_name + "_"+ symbol + "_" + instance_id + ".log"
        print(logfilename)
        log.init("backtest", logfilename)
        log.info("strategy name: %s;  config: %s" % (class_name, config))


    engine = BackTest(instance_id, mds_name, config, args.log)
    strategy = ts.createInstance(module_name, class_name, config, engine)
    engine.orders = old_instance["orders"]

    continue_time = old_instance["end_time"]
    oldest_time = engine.md.get_oldest_time(strategy.config['symbol'], kl.KLINE_INTERVAL_1MINUTE)
    if continue_time < oldest_time:
        continue_time = oldest_time
    latest_time = engine.md.get_latest_time(strategy.config['symbol'], kl.KLINE_INTERVAL_1MINUTE)
    end_time = latest_time
    print("  time range old( %s ~ %s );    continue( %s ~ %s )" % (
        old_instance["start_time"].strftime("%Y-%m-%d %H:%M"),
        old_instance["end_time"].strftime("%Y-%m-%d %H:%M"),
        continue_time.strftime("%Y-%m-%d %H:%M"),
        end_time.strftime("%Y-%m-%d %H:%M")))

    print("run2  kline_data_type: %s "% (engine.md.kline_data_type))
    tick_count = run2(engine, engine.md, strategy, continue_time, end_time)
    print("\n  total tick count: %d" % (tick_count))
    engine.analyze_orders(engine.orders)
    _id = bt_db.insert_one(
        BACKTEST_INSTANCES_COLLECTION_NAME,
        {
            "instance_id": instance_id,
            "start_time": old_instance["start_time"],
            "end_time": end_time,
            "orders": engine.orders,
            "mds": mds_name,
            "sc": sc,
        },
    )
    engine.display(symbol, engine.orders, strategy.cur_price, end_time, True, args.rmk)


def sub_cmd_refresh(args):
    instance_id = args.sii
    instance = get_instance(instance_id)
    print('marketing data src: %s  strategy config path: %s  ' % (instance['mds'], instance['sc']))

    config = xq.get_strategy_config(instance['sc'])
    pprint.pprint(config, indent=4)

    engine = BackTest(instance_id, instance['mds'], config)
    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]
    strategy = ts.createInstance(module_name, class_name, config, engine)
    refresh(engine, engine.md, strategy, [ datetime.fromtimestamp(order["create_time"]) for order in instance['orders']])
    orders = engine.orders
    for idx, order in enumerate(engine.orders):
        old_order = instance['orders'][idx]
        if "high" in old_order:
            order["high"] = old_order["high"]
            order["high_time"] = old_order["high_time"]
            order["low"] = old_order["low"]
            order["low_time"] = old_order["low_time"]
    engine.analyze(config['symbol'], engine.orders, True, True)


def sub_cmd_chart(args):
    instance_id = args.sii
    instance = get_instance(instance_id)

    start_time = instance['start_time']
    end_time = instance['end_time']
    orders = instance['orders']

    md = DBMD(instance['mds'])
    md.tick_time = end_time

    config = xq.get_strategy_config(instance['sc'])
    symbol = config["symbol"]
    interval = config["kline"]["interval"]
    title = symbol + '  ' + config['kline']['interval'] + ' ' + config['class_name']

    ordersets = []
    ordersets.append(orders)

    chart(title, md, symbol, interval, start_time, end_time, ordersets, args)


def sub_cmd_chart_diff(args):
    print(args.siis)
    print(len(args.siis))
    siis = args.siis
    if len(siis) != 2:
        exit(1)

    instance_a = get_instance(siis[0])
    instance_b = get_instance(siis[1])
    if instance_a['sc'] != instance_b['sc']:
        print(instance_a['sc'])
        print(instance_b['sc'])
        exit(1)

    start_time = min(instance_a['start_time'], instance_b['start_time'])
    end_time = max(instance_a['end_time'], instance_b['end_time'])
    orders_a = instance_a['orders']
    orders_b = instance_b['orders']

    md = DBMD(instance_a['mds'])
    md.tick_time = end_time

    config = xq.get_strategy_config(instance_a['sc'])
    symbol = config["symbol"]
    interval = config["kline"]["interval"]
    title = symbol + '  ' + config['kline']['interval'] + ' ' + config['class_name']

    ordersets = []
    ordersets.append(orders_a)
    ordersets.append(orders_b)

    chart(title, md, symbol, interval, start_time, end_time, ordersets, args)


def sub_cmd_merge(args):
    print(args.siis)
    print(len(args.siis))
    siis = args.siis
    if len(siis) != 2:
        exit(1)

    instance_a = get_instance(siis[0])
    instance_b = get_instance(siis[1])

    sc = instance_a['sc']
    if sc != instance_b['sc']:
        print(instance_a['sc'])
        print(instance_b['sc'])
        exit(1)

    mds = instance_a['mds']
    if mds != instance_b['mds']:
        print(instance_a['mds'])
        print(instance_b['mds'])
        exit(1)

    start_time = min(instance_a['start_time'], instance_b['start_time'])
    end_time = max(instance_a['end_time'], instance_b['end_time'])

    orders_a = instance_a['orders']
    orders_b = instance_b['orders']
    if instance_a['start_time'] < instance_b['start_time']:
        orders = orders_a + orders_b
    else:
        orders = orders_b + orders_a

    _id = bt_db.insert_one(
        BACKTEST_INSTANCES_COLLECTION_NAME,
        {
            "instance_id": create_instance_id(),
            "start_time": start_time,
            "end_time": end_time,
            "orders": orders,
            "mds": mds,
            "sc": sc,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='backtest')

    subparsers = parser.add_subparsers(help='sub-command help')

    """
    parser_run = subparsers.add_parser('run', help='run help')
    parser_run.add_argument('-m', help='market data source')
    parser_run.add_argument('-sc', help='strategy config')
    parser_run.add_argument('-r', help='time range (2018-7-1T8' + xq.time_range_split + '2018-8-1T8)')
    parser_run.add_argument('--cs', help='chart show', action="store_true")
    parser_run.add_argument('--log', help='log', action="store_true")
    add_argument_overlap_studies(parser_run)
    parser_run.set_defaults(func=sub_cmd_run)
    """
    default_exchange_name = BinanceExchange.name
    exchange_names = get_exchange_names()
    parser.add_argument('-m', default=default_exchange_name, choices=exchange_names, help='market data source')
    parser.add_argument('-sc', help='strategy config')
    parser.add_argument('-r', help='time range (2018-7-1T8' + xq.time_range_split + '2018-8-1T8)')
    parser.add_argument('--chart', help='chart', action="store_true")
    parser.add_argument('--log', help='log', action="store_true")
    parser.add_argument('--rmk', help='remark', action="store_true")

    parser_signal = subparsers.add_parser('signal', help='test signal')
    parser_signal.add_argument('-m', default=default_exchange_name, choices=exchange_names, help='market data source')
    parser_signal.add_argument('-sc', help='strategy config')
    parser_signal.add_argument('-r', help='time range (2018-7-1T8' + xq.time_range_split + '2018-8-1T8)')
    parser_signal.add_argument('--chart', help='chart', default=True, action="store_true")
    parser_signal.add_argument('--log', help='log', action="store_true")
    parser_signal.add_argument('--volume', action="store_true", help='volume')
    parser_signal.add_argument('--okls', nargs='*', help='other klines')
    chart_add_all_argument(parser_signal)
    parser_signal.set_defaults(func=sub_cmd_signal)

    parser_view = subparsers.add_parser('view', help='view help')
    parser_view.add_argument('-sii', help='strategy instance id')
    parser_view.set_defaults(func=view)

    parser_analyze = subparsers.add_parser('analyze', help='analyze help')
    parser_analyze.add_argument('-sii', help='strategy instance id')
    parser_analyze.add_argument('--hl', help='high low', action="store_true")
    parser_analyze.add_argument('--lock', help='lock info', action="store_true")
    parser_analyze.add_argument('--deal', help='deal info', action="store_true")
    parser_analyze.add_argument('--rmk', help='remark', action="store_true")
    parser_analyze.set_defaults(func=analyze)

    parser_continue = subparsers.add_parser('continue', help='run continue')
    parser_continue.add_argument('-sii', help='strategy instance id')
    parser_continue.add_argument('--log', help='log', action="store_true")
    parser_continue.add_argument('--rmk', help='remark', action="store_true")
    parser_continue.set_defaults(func=sub_cmd_continue)

    parser_refresh = subparsers.add_parser('refresh', help='refresh order info')
    parser_refresh.add_argument('-sii', help='strategy instance id')
    parser_refresh.set_defaults(func=sub_cmd_refresh)

    parser_chart = subparsers.add_parser('chart', help='chart help')
    parser_chart.add_argument('-sii', help='strategy instance id')
    parser_chart.add_argument('--volume', action="store_true", help='volume')
    parser_chart.add_argument('--tp', action="store_true", help=' total profit ratio')
    parser_chart.add_argument('--okls', nargs='*', help='other klines')
    chart_add_all_argument(parser_chart)
    parser_chart.set_defaults(func=sub_cmd_chart)

    parser_chart_diff = subparsers.add_parser('chart_diff', help='chart diff')
    parser_chart_diff.add_argument('-siis', nargs='*', help='strategy instance ids')
    parser_chart_diff.add_argument('--volume', action="store_true", help='volume')
    parser_chart_diff.add_argument('--tp', action="store_true", help=' total profit ratio')
    parser_chart_diff.add_argument('--okls', nargs='*', help='other klines')
    chart_add_all_argument(parser_chart_diff)
    parser_chart_diff.set_defaults(func=sub_cmd_chart_diff)

    parser_merge = subparsers.add_parser('merge', help='merge')
    parser_merge.add_argument('-siis', nargs='*', help='strategy instance ids')
    parser_merge.set_defaults(func=sub_cmd_merge)

    parser_search = subparsers.add_parser('search', help='search')
    parser_search.add_argument('-m', default=default_exchange_name, help='market data source')
    parser_search.add_argument('-sc', help='strategy config')
    parser_search.add_argument('-r', help='time range (2018-7-1T8' + xq.time_range_split + '2018-8-1T8)')
    parser_search.add_argument('-count', type=int, default=10, help=' search count')
    parser_search.set_defaults(func=sub_cmd_search)

    parser_multisearch = subparsers.add_parser('multisearch', help='multisearch')
    parser_multisearch.add_argument('-m', default=default_exchange_name, help='market data source')
    parser_multisearch.add_argument('-sc', help='strategy config')
    parser_multisearch.add_argument('-r', help='time range (2018-7-1T8' + xq.time_range_split + '2018-8-1T8)')
    parser_multisearch.add_argument('-count', type=int, default=10, help=' multisearch count')
    parser_multisearch.set_defaults(func=sub_cmd_multisearch)

    args = parser.parse_args()
    # print(args)
    if hasattr(args, 'func'):
        args.func(args)
    else:
        #parser.print_help()
        sub_cmd_run(args)
