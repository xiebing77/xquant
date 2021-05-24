#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import common.xquant as xq
import common.instance as si
from real import real_run
from real import real_view
from real import real_analyze
from engine.realengine import RealEngine
from db.mongodb import get_mongodb
import setup
from pprint import pprint


def real2_run(args):
    instance = si.get_strategy_instance(args.sii)
    config = xq.get_strategy_config(instance['config_path'])

    real_run(config, args.sii, instance['exchange'], instance['value'], args)

def real2_view(args):
    instance = si.get_strategy_instance(args.sii)
    config = xq.get_strategy_config(instance['config_path'])

    real_view(config, args.sii, instance['exchange'], instance['value'])

def real2_analyze(args):
    instance = si.get_strategy_instance(args.sii)
    config = xq.get_strategy_config(instance['config_path'])

    real_analyze(config, args.sii, instance['exchange'], instance['value'], args.hl, args.rmk, args.deal, args.lock)


def real2_list(args):
    td_db = get_mongodb(setup.trade_db_name)
    ss = td_db.find(si.STRATEGY_INSTANCE_COLLECTION_NAME, {"user": args.user})
    #pprint(ss)
    all_value = 0
    all_his_profit = 0
    all_flo_profit = 0
    all_commission = 0

    title_head_fmt = "%-30s  %10s%12s"
    head_fmt       = "%-30s  %10s(%10.0f)"

    title_profit_fmt = "%21s  %21s  %12s"
    profit_fmt       = "%12.2f(%6.2f%%)  %12.2f(%6.2f%%)  %12.2f"

    title_tail_fmt = "    %-60s  %-20s  %10s"


    print(title_head_fmt % ("instance_id", "value", "") + title_profit_fmt % ("history_profit", "floating_profit", "commission") + title_tail_fmt % ("config_path", "exchange", "status"))
    for s in ss:
        instance_id = s["instance_id"]
        exchange_name = s["exchange"]
        value = s["value"]
        config_path = s["config_path"]
        if "status" in s:
            status = s["status"]
        else:
            status = ""
        if status != args.status and status != "":
            continue

        all_value += value
        profit_info = ""
        try:
            config = xq.get_strategy_config(config_path)
            symbol = config['symbol']
            realEngine = RealEngine(instance_id, exchange_name, config, value)
            orders = realEngine.get_orders(symbol)
            pst_info = realEngine.get_pst_by_orders(orders)
            history_profit, history_profit_rate, history_commission = realEngine.get_history(pst_info)
            all_his_profit += history_profit
            floating_profit, floating_profit_rate, floating_commission, cur_price = realEngine.get_floating(symbol, pst_info)
            all_flo_profit += floating_profit
            commission = history_commission + floating_commission
            all_commission += commission
            profit_info = profit_fmt % (history_profit, history_profit_rate*100, floating_profit, floating_profit_rate*100, commission)

        except Exception as ept:
            profit_info = "error:  %s" % (ept)

        print(head_fmt % (instance_id, value, (value+history_profit+floating_profit)) + profit_info + title_tail_fmt % (config_path, exchange_name, status))

    if args.stat:
        print(head_fmt % ("all", all_value, all_value+all_his_profit+all_flo_profit) + profit_fmt % (all_his_profit, all_his_profit/all_value*100, all_flo_profit, all_flo_profit/all_value*100, all_commission))


def real2_update(args):
    record = {}
    if args.user:
        record["user"] = args.user
    if args.instance_id:
        record["instance_id"] = args.instance_id
    if args.config_path:
        record["config_path"] = args.config_path
    if args.exchange:
        record["exchange"] = args.exchange
    if args.value:
        instance = si.get_strategy_instance(args.sii)
        instance_id = instance["instance_id"]
        exchange_name = instance["exchange"]
        if not exchange_name:
            exchange_name = record["exchange_name"]
        config_path = instance["config_path"]
        if not config_path:
            config_path = record["config_path"]
        value = instance["value"]
        config = xq.get_strategy_config(config_path)
        symbol = config['symbol']
        realEngine = RealEngine(instance_id, exchange_name, config, value)
        orders = realEngine.get_orders(symbol)
        if orders:
            return

        record["value"] = args.value
    if args.status:
        record["status"] = args.status

    if record:
        si.update_strategy_instance({"instance_id": args.sii}, record)


def real2_add(args):
    record = {
        "user": args.user,
        "instance_id": args.sii,
        "config_path": args.config_path,
        "exchange": args.exchange,
        "value": args.value,
        "status": args.status,
    }
    si.add_strategy_instance(record)


def real2_delete(args):
    si.delete_strategy_instance({"instance_id": args.sii})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='real')
    parser.add_argument('-sii', help='strategy instance id')
    parser.add_argument('--debug', help='debug', action="store_true")
    parser.add_argument('--log', help='log', action="store_true")

    subparsers = parser.add_subparsers(help='sub-command help')

    parser_view = subparsers.add_parser('view', help='view strategy instance')
    parser_view.add_argument('-sii', required=True, help='strategy instance id')
    parser_view.set_defaults(func=real2_view)

    parser_analyze = subparsers.add_parser('analyze', help='analyze strategy instance')
    parser_analyze.add_argument('-sii', required=True, help='strategy instance id')
    parser_analyze.add_argument('--hl', help='high low', action="store_true")
    parser_analyze.add_argument('--rmk', help='remark', action="store_true")
    parser_analyze.add_argument('--deal', help='deal amount', action="store_true")
    parser_analyze.set_defaults(func=real2_analyze)

    parser_list = subparsers.add_parser('list', help='list of strategy instance')
    parser_list.add_argument('-user', help='user name')
    parser_list.add_argument('--status', default=si.STRATEGY_INSTANCE_STATUS_START, choices=si.strategy_instance_statuses, help='strategy instance status')
    parser_list.add_argument('--stat', help='stat all', action="store_true")
    parser_list.set_defaults(func=real2_list)

    parser_update = subparsers.add_parser('update', help='update strategy instance')
    parser_update.add_argument('-sii', required=True, help='strategy instance id')
    parser_update.add_argument('--user', help='user name')
    parser_update.add_argument('--instance_id', help='new strategy instance id')
    parser_update.add_argument('--config_path', help='strategy config path')
    parser_update.add_argument('--exchange', help='strategy instance exchange')
    parser_update.add_argument('--value', type=int, help='strategy instance value')
    parser_update.add_argument('--status', choices=si.strategy_instance_statuses, help='strategy instance status')
    parser_update.set_defaults(func=real2_update)

    parser_add = subparsers.add_parser('add', help='add new strategy instance')
    parser_add.add_argument('-user', required=True, help='user name')
    parser_add.add_argument('-sii', required=True, help='strategy instance id')
    parser_add.add_argument('-config_path', required=True, help='strategy config path')
    parser_add.add_argument('-exchange', required=True, help='strategy instance exchange')
    parser_add.add_argument('-value', required=True, type=int, help='strategy instance value')
    parser_add.add_argument('-status', choices=si.strategy_instance_statuses, default=si.STRATEGY_INSTANCE_STATUS_START, help='strategy instance status')
    parser_add.set_defaults(func=real2_add)

    parser_delete = subparsers.add_parser('delete', help='delete strategy instance')
    parser_delete.add_argument('-sii', required=True, help='strategy instance id')
    parser_delete.set_defaults(func=real2_delete)

    args = parser.parse_args()
    #print(args)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        real2_run(args)
