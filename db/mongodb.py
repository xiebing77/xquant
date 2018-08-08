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

    def insert_one(self, collection, **datas):
        """insert_one"""
        logging.debug("mongodb %s insert : %s", collection, datas)
        _id = self.__client[collection].insert_one(datas).inserted_id
        return _id

    def update_one(self, collection, _id, **datas):
        """update_one"""
        logging.debug("mongodb %s(_id=%s) update : %s", collection, _id, datas)
        self.__client[collection].update_one({"_id": ObjectId(_id)}, {"$set": datas})

    def find(self, collection, **querys):
        """find"""
        records = []
        ret = self.__client[collection].find(querys)
        for i in ret:
            records.append(i)
        return records
