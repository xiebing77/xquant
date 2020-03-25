#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import os
import json
import uuid
import utils.tools as ts
import common.xquant as xq
import common.log as log
from engine.realengine import RealEngine

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='real')
    parser.add_argument('-e', help='exchange')
    parser.add_argument('-sc', help='strategy config')
    parser.add_argument('-sii', help='strategy instance id')
    parser.add_argument('-v', help='value')
    parser.add_argument('--debug', help='debug', action="store_true")
    parser.add_argument('--log', help='log', action="store_true")
    args = parser.parse_args()
    # print(args)
    if not (args.e and args.sc and args.sii and args.v):
        parser.print_help()
        exit(1)

    fo = open(args.sc, "r")
    config = json.loads(fo.read())
    fo.close()
    print("config: ", config)

    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]

    instance_id = args.sii

    if args.log:
        logfilename = instance_id + ".log"
        print(logfilename)

        server_ip = os.environ.get('LOG_SERVER_IP')
        server_port = os.environ.get('LOG_SERVER_PORT')
        print('Log server IP: %s, Log server port: %s' % (server_ip, server_port))

        log.init('real', logfilename, server_ip, server_port)
        log.info("args: %s" % (args))
        log.info("strategy name: %s;  config: %s" % (class_name, config))

    engine = RealEngine(instance_id, args.e, config)
    strategy = ts.createInstance(module_name, class_name, config, engine)

    engine.value = args.v
    engine.run(strategy, args.debug)
