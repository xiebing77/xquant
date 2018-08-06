#!/usr/bin/python
"""mongodb"""
import logging
from pymongo import MongoClient
from bson import ObjectId


def get_datetime_by_id(_id):
    """get datetime from _id"""
    return ObjectId(_id).generation_time


class MongoDB:
    """MongoDB"""

    def __init__(self, user, password, db_name, db_url):
        client = MongoClient(db_url)
        self.__client = eval("%s.%s" % (client, db_name))
        self.__client.authenticate(user, password)

    def insert_order(self, **datas):
        """新增order"""
        logging.debug("mongodb orders insert : %s", datas)
        _id = self.__client.orders.insert_one(datas).inserted_id
        return _id

    def update_order(self, _id, **datas):
        """根据id修改order"""
        logging.debug("mongodb orders(_id=%s) update : %s", _id, datas)
        self.__client.orders.update_one({"_id": ObjectId(_id)}, {"$set": datas})

    def get_orders(self, **querys):
        """查询order"""
        orders = []
        ret = self.__client.orders.find(querys)
        for i in ret:
            orders.append(i)

        return orders
