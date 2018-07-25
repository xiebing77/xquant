#!/usr/bin/python




SIDE_BUY = 'BUY'
SIDE_SELL = 'SELL'

ORDER_TYPE_LIMIT = 'LIMIT'
ORDER_TYPE_MARKET = 'MARKET'

ORDER_STATUS_WAIT = 'wait'
ORDER_STATUS_OPEN = 'open'
ORDER_STATUS_CLOSE = 'close'
ORDER_STATUS_CANCELLING = 'cancelling'
ORDER_STATUS_CANCELLED = 'cancelled'


def creat_symbol(target_coin, base_coin):
    return '%s_%s' % (target_coin.lower(), base_coin.lower())

def get_symbol_coins(symbol):
    coins = symbol.split('_')
    return tuple(coins)
