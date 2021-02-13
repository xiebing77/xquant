#!/usr/bin/python
"""bill"""

DIRECTION_LONG = "LONG"   # 做多
DIRECTION_SHORT = "SHORT"  # 做空

OPEN_POSITION = "OPEN"    # 开仓
CLOSE_POSITION = "CLOSE"   # 平仓
LOCK_POSITION = "LOCK"       # 锁仓
UNLOCK_POSITION = "UNLOCK"   # 解锁仓位


def create_bill(direction, action, pst_rate, describe, rmk, can_open_time=None, stop_loss_price=None):
    """创建单据"""
    return {"direction": direction, "action": action, "pst_rate": pst_rate, "describe": describe, "rmk": rmk, "can_open_time": can_open_time,
        "stop_loss_price": stop_loss_price
    }

def open_long_bill(pst_rate, describe, rmk, can_open_time=None, stop_loss_price=None):
    """创建买单"""
    return create_bill(DIRECTION_LONG, OPEN_POSITION, pst_rate, describe, rmk, can_open_time, stop_loss_price)

def close_long_bill(pst_rate, describe, rmk, can_open_time=None, stop_loss_price=None):
    """创建卖单"""
    return create_bill(DIRECTION_LONG, CLOSE_POSITION, pst_rate, describe, rmk, can_open_time, stop_loss_price)

def open_short_bill(pst_rate, describe, rmk, can_open_time=None, stop_loss_price=None):
    """创建买信号"""
    return create_bill(DIRECTION_SHORT, OPEN_POSITION, pst_rate, describe, rmk, can_open_time, stop_loss_price)

def close_short_bill(pst_rate, describe, rmk, can_open_time=None, stop_loss_price=None):
    """创建卖信号"""
    return create_bill(DIRECTION_SHORT, CLOSE_POSITION, pst_rate, describe, rmk, can_open_time, stop_loss_price)

def is_open_bill(bill):
    return bill["action"] == OPEN_POSITION

def is_close_bill(bill):
    return bill["action"] == CLOSE_POSITION

def is_long_bill(bill):
    return bill["direction"] == DIRECTION_LONG

def is_short_bill(bill):
    return bill["direction"] == DIRECTION_SHORT

def lock_long_bill(pst_rate, describe, rmk):
    return create_bill(DIRECTION_LONG, LOCK_POSITION, pst_rate, describe, rmk, None, None)

def unlock_long_bill(pst_rate, describe, rmk):
    return create_bill(DIRECTION_LONG, UNLOCK_POSITION, pst_rate, describe, rmk, None, None)

def lock_short_bill(pst_rate, describe, rmk):
    return create_bill(DIRECTION_SHORT, LOCK_POSITION, pst_rate, describe, rmk, None, None)

def unlock_short_bill(pst_rate, describe, rmk):
    return create_bill(DIRECTION_SHORT, UNLOCK_POSITION, pst_rate, describe, rmk, None, None)

def decision_bills(bills):
    """决策交易信号"""
    if not bills:
        return None

    ds_bill = bills[0]

    for bill in bills[1:]:
        # 暂时不支持同时做多、做空
        if ds_bill["direction"] != bill["direction"]:
            return None

        if ds_bill["action"] == bill["action"]:
            # 持仓率低的信号优先
            if ds_bill["pst_rate"] > bill["pst_rate"]:
                ds_bill = bill
            elif ds_bill["pst_rate"] == bill["pst_rate"]:
                # 合并信号
                ds_bill["describe"] += ", " + bill["describe"]
                ds_bill["rmk"] += ", " + bill["rmk"]
                # 限制开仓时间长的优先
                if bill["can_open_time"]:
                    if (not ds_bill["can_open_time"]) or (ds_bill["can_open_time"] < bill["can_open_time"]):
                        ds_bill["can_open_time"] = bill["can_open_time"]
        else:
            # 平仓信号优先于开仓信号
            if ds_bill["action"] == OPEN_POSITION:
                ds_bill = bill

    return ds_bill

