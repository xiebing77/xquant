#!/usr/bin/python3
from db.mongodb import get_mongodb
import setup

STRATEGY_INSTANCE_COLLECTION_NAME = 'strategies'

def get_strategy_instance(sii):
    db = get_mongodb(setup.db_order_name)
    db.ensure_index(STRATEGY_INSTANCE_COLLECTION_NAME, [("instance_id",1)])

    instances = db.find(STRATEGY_INSTANCE_COLLECTION_NAME, {"instance_id": sii})
    print(instances)
    if len(instances) is 0:
        print("strategy instance id (%s) not exist!" % (sii))
        exit(1)
    elif len(instances) > 1:
        exit(1)
    return instances[0]

