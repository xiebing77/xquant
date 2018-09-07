#!/usr/bin/python
"""mongodb"""
import logging
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from bson import ObjectId


def get_datetime_by_id(_id):
    """get datetime from _id"""
    return ObjectId(_id).generation_time


class MongoDB:
    """MongoDB"""

    def __init__(self, user, password, db_name, db_url):
        client = MongoClient(db_url)
        self.__client = eval("%s.%s" % (client, db_name))
        if user:
            self.__client.authenticate(user, password)

    def create_index(self, collection, index):
        self.__client[collection].create_index(index, unique=True)

    def ensure_index(self, collection, index):
        self.__client[collection].ensure_index(index)

    def insert_one(self, collection, record):
        """insert_one"""
        try:
            logging.debug("mongodb %s insert : %s", collection, record)
            _id = self.__client[collection].insert_one(record).inserted_id
            return _id
        except Exception as exc:
            print(exc)
            return None

    def insert_many(self, collection, records):
        """insert_many"""
        try:
            ret = self.__client[collection].insert_many(records)
            return ret
        except BulkWriteError as exc:
            print(exc.details)
            return None

    def update_one(self, collection, _id, record):
        """update_one"""
        logging.debug("mongodb %s(_id=%s) update : %s", collection, _id, record)
        self.__client[collection].update_one({"_id": ObjectId(_id)}, {"$set": record})

    def find(self, collection, query, projection=None):
        """find"""
        #print(query)
        #print(projection)
        if projection:
            ret = self.__client[collection].find(query, projection=projection)
        else:
            ret = self.__client[collection].find(query)

        records = []
        for i in ret:
            records.append(i)
        return records

    def find_sort(self, collection, query, sort_field, sort_dir, projection=None):
        """find and sort
            sort_dir: 1. ASCENDING,
                     -1. DESCENDING
        """
        #print(query)
        #print(projection)
        if projection:
            ret = self.__client[collection].find(query, projection=projection).sort(sort_field, sort_dir)
        else:
            ret = self.__client[collection].find(query).sort(sort_field, sort_dir)

        records = []
        for i in ret:
            records.append(i)
        return records

    def count(self, collection, query, projection=None):
        """count"""
        #print(query)
        #print(projection)
        if projection:
            ret = self.__client[collection].find(query, projection=projection).count()
        else:
            ret = self.__client[collection].find(query).count()
        return ret
