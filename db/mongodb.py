#!/usr/bin/python
from pymongo import MongoClient


class MongoDB(object):
    """docstring for MongoDB"""
    def __init__(self, user, password, db_name, db_url):
        client = MongoClient(db_url)
        self.__client = eval('%s.%s' % (client, db_name))
        self.__client.authenticate(user, password)


    def insert_order(self, strategy_id, symbol, side, type, pirce, amount, status):
        _id = self.__client.orders.insert_one({
            'strategy_id': strategy_id,
            'symbol': symbol,
            'side': side,
            'type': type,
            'order_id': '',
            'pirce': pirce,
            'amount': amount,
            'status': xquant.ORDER_STATUS_WAIT,
            'cancle_amount': 0,
            'deal_amount': 0,
            'deal_value': 0 }).inserted_id
        return _id
        '''
    def update_order(self, id, order_id, status):
        self.__client.orders.update_one({'_id': ObjectId(id)}, {$set:{
            'order_id': order_id,
            'status': status }})
    '''
    def update_order(self, id, **datas):
        self.__client.orders.update_one({'_id': ObjectId(id)}, {'$set':{*datas}})



    #
    def get_orders(self, **querys):
        print('querys: ', querys)
        print('*querys: ', *querys)
        # print('**querys: ', **querys)
        orders = self.__client.orders.find(querys)
        return orders

    '''
    def get_order(self, strategy_id, order_id):
        order = self.__client.orders.find_one({
            'strategy_id': strategy_id,
            'order_id': order_id })
        return order
    '''
