
import common.bill as bl
from pprint import pprint


ORDER_ACTION_KEY       = "action"
ORDER_DIRECTION_KEY    = "direction"
ORDER_DEAL_AMOUNT_KEY  = "deal_amount"
ORDER_DEAL_VALUE_KEY   = "deal_value"
ORDER_COMMISSION_KEY   = "commission"
ORDER_SLP_KEY          = "stop_loss_price"
ORDER_REMARK_KEY       = "rmk"

RATE_SUFFIX = "_rate"

POSITON_KEY = "pst"

POSITON_PREFIX = POSITON_KEY + "_"
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

POSITON_PROFIT_KEY = POSITON_PREFIX + "profit"
POSITON_PROFIT_RATE_KEY = POSITON_PROFIT_KEY + RATE_SUFFIX

HISTORY_PREFIX = "history"
HISTORY_COMMISSION_KEY = HISTORY_PREFIX + "_" + ORDER_COMMISSION_KEY
HISTORY_PROFIT_KEY     = HISTORY_PREFIX + "_profit"

LOCK_POSITON_PREFIX = "lock_"
LOCK_POSITON_AMOUNT_KEY = LOCK_POSITON_PREFIX + POSITON_AMOUNT_KEY
LOCK_POSITON_VALUE_KEY = LOCK_POSITON_PREFIX + POSITON_VALUE_KEY
LOCK_POSITON_COMMISSION_KEY = LOCK_POSITON_PREFIX + POSITON_COMMISSION_KEY

TOTAL_PREFIX = "total_"
TOTAL_COMMISSION_KEY = TOTAL_PREFIX + POSITON_COMMISSION_KEY
TOTAL_PROFIX_KEY = TOTAL_PREFIX + "profit"
TOTAL_PROFIX_RATE_KEY = TOTAL_PROFIX_KEY + RATE_SUFFIX

def get_order_value(order):
    if ((order[ORDER_ACTION_KEY] in [bl.OPEN_POSITION, bl.UNLOCK_POSITION] and order[ORDER_DIRECTION_KEY] == bl.DIRECTION_LONG) or
        (order[ORDER_ACTION_KEY] in [bl.CLOSE_POSITION, bl.LOCK_POSITION] and order[ORDER_DIRECTION_KEY] == bl.DIRECTION_SHORT)):
        return - order[ORDER_DEAL_VALUE_KEY]
    else:
        return order[ORDER_DEAL_VALUE_KEY]

def pst_is_lock(pst):
    if LOCK_POSITON_AMOUNT_KEY in pst and pst[LOCK_POSITON_AMOUNT_KEY] > 0:
        return True
    return False

def trans_lock_to_close(lastly_order, rmk, cur_time):
    if lastly_order[ORDER_ACTION_KEY] == bl.LOCK_POSITION:
        lastly_order[ORDER_ACTION_KEY] = bl.CLOSE_POSITION
        lastly_order["pst_rate"] = 0
        lastly_order[ORDER_REMARK_KEY] += "  close positon time: %s  " % cur_time + rmk
        del lastly_order[POSITON_KEY]

def get_pst_first_order(orders):
    for pst_first_order in reversed(orders):
        if pst_first_order[ORDER_ACTION_KEY] == bl.OPEN_POSITION:
            return pst_first_order
    return None

def init_history(pst):
    pst[HISTORY_COMMISSION_KEY] = 0
    pst[HISTORY_PROFIT_KEY] = 0

def get_first_pst(order, commission_rate):
    if ORDER_SLP_KEY in order:
        slp = order[ORDER_SLP_KEY]
    else:
        slp = None
    return {
        POSITON_DIRECTION_KEY  : order[ORDER_DIRECTION_KEY],
        POSITON_AMOUNT_KEY     : order[ORDER_DEAL_AMOUNT_KEY],
        POSITON_COMMISSION_KEY : order[ORDER_DEAL_VALUE_KEY] * commission_rate,
        POSITON_VALUE_KEY      : get_order_value(order),
        POSITON_PRICE_KEY      : order[ORDER_DEAL_VALUE_KEY] / order[ORDER_DEAL_AMOUNT_KEY],
        POSITON_SLP_KEY        : slp,
    }

def calc_pst_by_order(pre_order, cur_order, commission_rate):
    pre_pst = pre_order[POSITON_KEY]
    if pre_pst[POSITON_AMOUNT_KEY] == 0:
        cur_pst = get_first_pst(cur_order, commission_rate)
    else:
        if cur_order[ORDER_DIRECTION_KEY] != pre_order[ORDER_DIRECTION_KEY]:
            return

        cur_pst = { POSITON_DIRECTION_KEY : cur_order[ORDER_DIRECTION_KEY] }

        cur_pst[POSITON_AMOUNT_KEY]     = pre_pst[POSITON_AMOUNT_KEY]
        cur_pst[POSITON_COMMISSION_KEY] = pre_pst[POSITON_COMMISSION_KEY]
        cur_pst[POSITON_VALUE_KEY]      = pre_pst[POSITON_VALUE_KEY]
        cur_pst[POSITON_SLP_KEY]        = pre_pst[POSITON_SLP_KEY]
        if LOCK_POSITON_AMOUNT_KEY in pre_pst:
            cur_pst[LOCK_POSITON_AMOUNT_KEY]     = pre_pst[LOCK_POSITON_AMOUNT_KEY]
            cur_pst[LOCK_POSITON_COMMISSION_KEY] = pre_pst[LOCK_POSITON_COMMISSION_KEY]
            cur_pst[LOCK_POSITON_VALUE_KEY]      = pre_pst[LOCK_POSITON_VALUE_KEY]

        cur_order_action = cur_order[ORDER_ACTION_KEY]
        cur_order_amount = cur_order[ORDER_DEAL_AMOUNT_KEY]
        cur_order_commission = cur_order[ORDER_DEAL_VALUE_KEY] * commission_rate

        if cur_order_action == bl.OPEN_POSITION:
            cur_pst[POSITON_AMOUNT_KEY]     += cur_order_amount
            cur_pst[POSITON_COMMISSION_KEY] += cur_order_commission
            cur_pst[POSITON_VALUE_KEY]      += get_order_value(cur_order)
        elif cur_order_action == bl.CLOSE_POSITION:
            cur_pst[POSITON_AMOUNT_KEY]     -= cur_order_amount
            cur_pst[POSITON_COMMISSION_KEY] += cur_order_commission
            cur_pst[POSITON_VALUE_KEY]      += get_order_value(cur_order)
        elif cur_order_action == bl.LOCK_POSITION:
            if LOCK_POSITON_AMOUNT_KEY in cur_pst:
                cur_pst[LOCK_POSITON_AMOUNT_KEY]     += cur_order_amount
                cur_pst[LOCK_POSITON_COMMISSION_KEY] += cur_order_commission
                cur_pst[LOCK_POSITON_VALUE_KEY]      += get_order_value(cur_order)
            else:
                cur_pst[LOCK_POSITON_AMOUNT_KEY]     = cur_order_amount
                cur_pst[LOCK_POSITON_COMMISSION_KEY] = cur_order_commission
                cur_pst[LOCK_POSITON_VALUE_KEY]      = get_order_value(cur_order)
        elif cur_order_action == bl.UNLOCK_POSITION:
            cur_pst[LOCK_POSITON_AMOUNT_KEY]     -= cur_order_amount
            cur_pst[LOCK_POSITON_COMMISSION_KEY] += cur_order_commission
            cur_pst[LOCK_POSITON_VALUE_KEY]      += get_order_value(cur_order)

    cur_pst[HISTORY_PROFIT_KEY]     = pre_pst[HISTORY_PROFIT_KEY]
    cur_pst[HISTORY_COMMISSION_KEY] = pre_pst[HISTORY_COMMISSION_KEY]
    if cur_pst[POSITON_AMOUNT_KEY] == 0:
        pst_profit = cur_pst[POSITON_VALUE_KEY] - cur_pst[POSITON_COMMISSION_KEY]
        cur_pst[HISTORY_PROFIT_KEY]     += pst_profit
        cur_pst[HISTORY_COMMISSION_KEY] += cur_pst[POSITON_COMMISSION_KEY]
        if LOCK_POSITON_VALUE_KEY in cur_pst:
            lock_pst_profit = cur_pst[LOCK_POSITON_VALUE_KEY] - cur_pst[LOCK_POSITON_COMMISSION_KEY]
            cur_pst[HISTORY_PROFIT_KEY]     += lock_pst_profit
            cur_pst[HISTORY_COMMISSION_KEY] += cur_pst[LOCK_POSITON_COMMISSION_KEY]


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
        calc_pst_by_order(orders[idx-1], orders[idx], commission_rate)
    return orders[idx][POSITON_KEY]


def calc_pst_profit(pst, cur_price):
    total_profit = pst[HISTORY_PROFIT_KEY]
    total_commission = pst[HISTORY_COMMISSION_KEY]

    pst_profit = pst[POSITON_VALUE_KEY] - pst[POSITON_COMMISSION_KEY]
    if LOCK_POSITON_VALUE_KEY in pst:
        pst_profit += pst[LOCK_POSITON_VALUE_KEY] - pst[LOCK_POSITON_COMMISSION_KEY]
    if pst[POSITON_AMOUNT_KEY] > 0:
        if not pst_is_lock(pst):
            cur_value = cur_price * pst[POSITON_AMOUNT_KEY]
            if pst[POSITON_DIRECTION_KEY] == bl.DIRECTION_LONG:
                pst_profit += cur_value
            else:
                pst_profit -=  cur_value

        total_profit += pst_profit
        total_commission += pst[POSITON_COMMISSION_KEY]
        if LOCK_POSITON_COMMISSION_KEY in pst:
            total_commission += pst[LOCK_POSITON_COMMISSION_KEY]

    pst[TOTAL_COMMISSION_KEY] = total_commission
    return pst_profit, total_profit


def get_open_value(pst, init_value, mode):
    open_value = init_value
    if mode == 1:
        open_value += (pst[HISTORY_PROFIT_KEY])
        if pst[POSITON_AMOUNT_KEY] == 0:
            open_value -= pst[POSITON_PROFIT_KEY]
    return open_value


def analyze_profit_by_orders(orders, commission_rate, init_value, mode):
    pst_info = get_pst_by_orders(orders, commission_rate)

    for index ,order in enumerate(orders):
        pst = order[POSITON_KEY]
        deal_price = order["deal_value"] / order["deal_amount"]
        pst_profit, total_profit = calc_pst_profit(pst, deal_price)
        pst[POSITON_PROFIT_KEY] = pst_profit
        pst[TOTAL_PROFIX_KEY] = total_profit

        open_value = get_open_value(pst, init_value, mode)
        pst[POSITON_PROFIT_RATE_KEY] = pst_profit / open_value
        pst[TOTAL_PROFIX_RATE_KEY] = total_profit / init_value


def get_floating_profit(pst, init_value, mode, cur_price):
    if pst[POSITON_AMOUNT_KEY] == 0:
        return 0, 0, 0, 0
    pst_profit, total_profit = calc_pst_profit(pst, cur_price)
    pst_profit_rate = pst_profit / get_open_value(pst, init_value, mode)
    total_profit_rate = total_profit / init_value
    return pst_profit, total_profit, pst_profit_rate, total_profit_rate


def get_cost_price(pst):
    if pst[POSITON_AMOUNT_KEY] == 0:
        return 0
    if pst[POSITON_DIRECTION_KEY] == bl.DIRECTION_LONG:
        return (pst[POSITON_COMMISSION_KEY] - pst[POSITON_VALUE_KEY]) / pst[POSITON_AMOUNT_KEY]
    else:
        return (pst[POSITON_VALUE_KEY] - pst[POSITON_COMMISSION_KEY]) / pst[POSITON_AMOUNT_KEY]
