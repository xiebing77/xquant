#!/usr/bin/python
from pymongo import MongoClient
from bson import ObjectId
import logging
import pandas
from pymongo.errors import BulkWriteError

def get_datetime_by_id(id):
    return ObjectId(id).generation_time


class MongoDB(object):
    """docstring for MongoDB"""
    def __init__(self, user, password, db_name, db_url):
        client = MongoClient(db_url)
        self.__client = eval('%s.%s' % (client, db_name))
        self.__client.authenticate(user, password)
        self.__client.kline.create_index("open_time", unique=True)

    def insert_order(self, **datas):
        logging.debug('mongodb orders insert : %s', datas)
        _id = self.__client.orders.insert_one(datas).inserted_id
        return _id

    def update_order(self, id, **datas):
        logging.debug('mongodb orders(_id=%s) update : %s', id, datas)
        self.__client.orders.update_one({'_id': ObjectId(id)}, {'$set':datas})

    def get_orders(self, **querys):
        orders = []
        ret = self.__client.orders.find(querys)
        for i in ret:
            orders.append(i)

        return orders

    def insert_kline(self, symbol, df):
        """DataFrame数据写入mongodb"""
        try:
            collection = "kline_%s" % symbol
            result = self.__client[collection].insert_many(df.to_dict('records'))
            return result
        except BulkWriteError as exc:
            print(exc.details)
            return None

    def get_kline(self, symbol, interval, size, since, sort=-1, no_id=True):
        """查询数据库，导出DataFrame类型数据
        （symbol：btc_usdt alike
         interval(ms)：1min - 60000
                   1Hour - 3600000
         since(ms): start time"""
        collection = "kline_%s" % symbol
        item = "open_time"
        query = {item: {"$gte": since, "$mod": [interval, 0]}}
        cursor = self.__client[collection].find(query).sort(item, sort).limit(size)
        df = pandas.DataFrame(list(cursor))
        if no_id:
            del df['_id']
        return df
