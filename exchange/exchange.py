#!/usr/bin/python


class Exchange(object):
    """docstring for Exchange"""
    def __init__(self):
        super().__init__()

    def __creat_balance(self, coin, free, frozen):
        return {'coin': coin, 'free': free, 'frozen': frozen}

    def get_balance_free(self, balance):
        return balance['free']

    def get_balance_frozen(self, balance):
        return balance['frozen']

