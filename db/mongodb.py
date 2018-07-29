#!/usr/bin/python
from pymongo import MongoClient
from bson import ObjectId
import logging


def get_datetime_by_id(id):
    return ObjectId(id).generation_time


class MongoDB(object):
    """docstring for MongoDB"""
    def __init__(self, user, password, db_name, db_url):
        client = MongoClient(db_url)
        self.__client = eval('%s.%s' % (client, db_name))
        self.__client.authenticate(user, password)


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

