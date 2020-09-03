
import common.bill as bl
from pprint import pprint


ORDER_ACTION_KEY       = "action"
ORDER_DIRECTION_KEY    = "direction"
ORDER_DEAL_AMOUNT_KEY  = "deal_amount"
ORDER_DEAL_VALUE_KEY   = "deal_value"
ORDER_COMMISSION_KEY   = "commission"
ORDER_SLP_KEY          = "stop_loss_price"

POSITON_KEY = "pst"

POSITON_PREFIX = POSITON_KEY
POSITON_DIRECTION_KEY  = ORDER_DIRECTION_KEY
POSITON_COMMISSION_KEY = ORDER_COMMISSION_KEY
POSITON_AMOUNT_KEY     = "amount"
POSITON_VALUE_KEY      = "value"
POSITON_PRICE_KEY      = "price"
POSITON_SLP_KEY        = ORDER_SLP_KEY
POSITON_HIGH_KEY       = "high"
POSITON_HIGH_TIME_KEY  = "high_time"
POSITON_LOW_KEY        = "low"
POSITON_LOW_TIME_KEY   = "low_time"

HISTORY_PREFIX = "history"
HISTORY_COMMISSION_KEY = HISTORY_PREFIX + "_" + ORDER_COMMISSION_KEY
HISTORY_PROFIT_KEY     = HISTORY_PREFIX + "_profit"


def get_order_value(order):
    if ((order[ORDER_ACTION_KEY] == bl.OPEN_POSITION and order[ORDER_DIRECTION_KEY] == bl.DIRECTION_LONG) or
        (order[ORDER_ACTION_KEY] == bl.CLOSE_POSITION and order[ORDER_DIRECTION_KEY] == bl.DIRECTION_SHORT)):
        return - order[ORDER_DEAL_VALUE_KEY]
    else:
        return order[ORDER_DEAL_VALUE_KEY]

def get_floating_profit(pst, cur_price):
    tmp_value = cur_price * pst[POSITON_AMOUNT_KEY]
    if pst[POSITON_DIRECTION_KEY] == bl.DIRECTION_LONG:
        pst_profit = tmp_value + pst[POSITON_VALUE_KEY]
    else:
        pst_profit = pst[POSITON_VALUE_KEY] - tmp_value
    pst_profit -= pst[POSITON_COMMISSION_KEY]
    return pst_profit

def init_history(pst):
    pst[HISTORY_COMMISSION_KEY] = 0
    pst[HISTORY_PROFIT_KEY] = 0

def get_first_pst(order, commission_rate):
    return {
        POSITON_DIRECTION_KEY  : order[ORDER_DIRECTION_KEY],
        POSITON_AMOUNT_KEY     : order[ORDER_DEAL_AMOUNT_KEY],
        POSITON_COMMISSION_KEY : order[ORDER_DEAL_VALUE_KEY] * commission_rate,
        POSITON_VALUE_KEY      : get_order_value(order),
        POSITON_PRICE_KEY      : order[ORDER_DEAL_VALUE_KEY] / order[ORDER_DEAL_AMOUNT_KEY],
        POSITON_SLP_KEY        : order[ORDER_SLP_KEY],
    }

def calc_pst_by_order(pre_order, cur_order, commission_rate):
    pre_pst = pre_order[POSITON_KEY]
    if pre_pst[POSITON_AMOUNT_KEY] == 0:
        cur_pst = get_first_pst(cur_order, commission_rate)
    else:
        if cur_order[ORDER_DIRECTION_KEY] != pre_order[ORDER_DIRECTION_KEY]:
            return

        cur_pst = { POSITON_DIRECTION_KEY : cur_order[ORDER_DIRECTION_KEY] }

        if cur_order[ORDER_ACTION_KEY] == bl.OPEN_POSITION:
            cur_pst[POSITON_AMOUNT_KEY] = pre_order[ORDER_DEAL_AMOUNT_KEY] + cur_order[ORDER_DEAL_AMOUNT_KEY]
        else:
            cur_pst[POSITON_AMOUNT_KEY] = pre_order[ORDER_DEAL_AMOUNT_KEY] - cur_order[ORDER_DEAL_AMOUNT_KEY]

        cur_pst[POSITON_COMMISSION_KEY] = pre_pst[POSITON_COMMISSION_KEY] + cur_order[ORDER_DEAL_VALUE_KEY] * commission_rate
        cur_pst[POSITON_VALUE_KEY]      = pre_pst[POSITON_VALUE_KEY] + get_order_value(cur_order)

    cur_pst[HISTORY_PROFIT_KEY]     = pre_pst[HISTORY_PROFIT_KEY]
    cur_pst[HISTORY_COMMISSION_KEY] = pre_pst[HISTORY_COMMISSION_KEY]
    if cur_pst[POSITON_AMOUNT_KEY] == 0:
        pst_profit = cur_pst[POSITON_VALUE_KEY] - cur_pst[POSITON_COMMISSION_KEY]
        cur_pst[HISTORY_PROFIT_KEY]     += pst_profit
        cur_pst[HISTORY_COMMISSION_KEY] += cur_pst[POSITON_COMMISSION_KEY]

    cur_order[POSITON_KEY] = cur_pst
    #pprint(cur_order)


def get_pst_by_orders(orders, commission_rate):
    if len(orders) == 0:
        return {
            POSITON_AMOUNT_KEY: 0,
            POSITON_VALUE_KEY: 0,
            POSITON_COMMISSION_KEY: 0,
            HISTORY_PROFIT_KEY: 0,
            HISTORY_COMMISSION_KEY: 0,
        }

    cur_order = orders[-1]
    if POSITON_KEY in cur_order:
        return cur_order[POSITON_KEY]

    if len(orders) == 1:
        first_pst = get_first_pst(cur_order, commission_rate)
        init_history(first_pst)
        cur_order[POSITON_KEY] = first_pst
        return first_pst

    pre_order = orders[-2]
    if POSITON_KEY in pre_order:
        calc_pst_by_order(pre_order, cur_order, commission_rate)
        return cur_order[POSITON_KEY]

    first_pst = get_first_pst(orders[0], commission_rate)
    init_history(first_pst)
    orders[0][POSITON_KEY] = first_pst
    for idx in range(1, len(orders)):
        calc_pst_by_order(orders[idx-1], orders[idx])
    return orders[idx][POSITON_KEY]
