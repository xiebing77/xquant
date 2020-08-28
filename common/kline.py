#!/usr/bin/python

from datetime import datetime, timedelta, time


KLINE_DATA_TYPE_LIST = 0
KLINE_DATA_TYPE_JSON = 1

KLINE_KEY_OPEN_TIME  = "open_time"
KLINE_KEY_CLOSE_TIME = "close_time"
KLINE_KEY_OPEN       = "open"
KLINE_KEY_CLOSE      = "close"
KLINE_KEY_HIGH       = "high"
KLINE_KEY_LOW        = "low"
KLINE_KEY_VOLUME     = "volume"

KLINE_INTERVAL_1MINUTE = '1m'
KLINE_INTERVAL_3MINUTE = '3m'
KLINE_INTERVAL_5MINUTE = '5m'
KLINE_INTERVAL_15MINUTE = '15m'
KLINE_INTERVAL_30MINUTE = '30m'
KLINE_INTERVAL_1HOUR = '1h'
KLINE_INTERVAL_2HOUR = '2h'
KLINE_INTERVAL_4HOUR = '4h'
KLINE_INTERVAL_6HOUR = '6h'
KLINE_INTERVAL_8HOUR = '8h'
KLINE_INTERVAL_12HOUR = '12h'
KLINE_INTERVAL_1DAY = '1d'
KLINE_INTERVAL_3DAY = '3d'
KLINE_INTERVAL_1WEEK = '1w'
KLINE_INTERVAL_1MONTH = '1M'

SECONDS_MINUTE = 60
SECONDS_HOUR = 60 * SECONDS_MINUTE
SECONDS_DAY = 24 * SECONDS_HOUR

def get_kline_collection(symbol, interval):
    return "kline_%s_%s" % (symbol, interval)

def get_open_time(interval, dt):
    if interval == KLINE_INTERVAL_1MINUTE:
        return datetime.combine(dt.date(), time(dt.hour, dt.minute, 0))
    elif interval == KLINE_INTERVAL_3MINUTE:
        open_minute = (dt.minute // 3) * 3
        return datetime.combine(dt.date(), time(dt.hour, open_minute, 0))
    elif interval == KLINE_INTERVAL_5MINUTE:
        open_minute = (dt.minute // 5) * 5
        return datetime.combine(dt.date(), time(dt.hour, open_minute, 0))
    elif interval == KLINE_INTERVAL_15MINUTE:
        open_minute = (dt.minute // 15) * 15
        return datetime.combine(dt.date(), time(dt.hour, open_minute, 0))
    elif interval == KLINE_INTERVAL_30MINUTE:
        if dt.minute < 30:
            open_minute = 0
        else:
            open_minute = 30
        return datetime.combine(dt.date(), time(dt.hour, open_minute, 0))

    elif interval == KLINE_INTERVAL_1HOUR:
        open_hour = dt.hour
        return datetime.combine(dt.date(), time(open_hour, 0, 0))
    elif interval == KLINE_INTERVAL_2HOUR:
        open_hour = (dt.hour // 2) * 2
        return datetime.combine(dt.date(), time(open_hour, 0, 0))
    elif interval == KLINE_INTERVAL_4HOUR:
        open_hour = (dt.hour // 4) * 4
        return datetime.combine(dt.date(), time(open_hour, 0, 0))

    elif interval == KLINE_INTERVAL_6HOUR:
        if dt.hour < 2:
            return datetime.combine(dt.date() - timedelta(days=1), time(20, 0, 0))
        elif dt.hour < 8:
            return datetime.combine(dt.date(), time(2, 0, 0))
        elif dt.hour < 14:
            return datetime.combine(dt.date(), time(8, 0, 0))
        elif dt.hour < 20:
            return datetime.combine(dt.date(), time(14, 0, 0))
        else:
            return datetime.combine(dt.date(), time(20, 0, 0))

    elif interval == KLINE_INTERVAL_8HOUR:
        open_hour = (dt.hour // 8) * 8
        return datetime.combine(dt.date(), time(open_hour, 0, 0))

    elif interval == KLINE_INTERVAL_12HOUR:
        if dt.hour < 8:
            return datetime.combine(dt.date() - timedelta(days=1), time(20, 0, 0))
        elif dt.hour >= 20:
            return datetime.combine(dt.date(), time(20, 0, 0))
        else:
            return datetime.combine(dt.date(), time(8, 0, 0))

    elif interval == KLINE_INTERVAL_1DAY:
        if dt.hour < 8:
            return datetime.combine(dt.date() - timedelta(days=1), time(8, 0, 0))
        else:
            return datetime.combine(dt.date(), time(8, 0, 0))
    else:
        return None

def get_timedelta(interval, size):
    if interval == KLINE_INTERVAL_1MINUTE:
        return timedelta(minutes=size-1)
    elif interval == KLINE_INTERVAL_3MINUTE:
        return timedelta(minutes=3*size-1)
    elif interval == KLINE_INTERVAL_5MINUTE:
        return timedelta(minutes=5*size-1)
    elif interval == KLINE_INTERVAL_15MINUTE:
        return timedelta(minutes=15*size-1)
    elif interval == KLINE_INTERVAL_30MINUTE:
        return timedelta(minutes=30*size-1)

    elif interval == KLINE_INTERVAL_1HOUR:
        return timedelta(hours=1*size-1)
    elif interval == KLINE_INTERVAL_2HOUR:
        return timedelta(hours=2*size-1)
    elif interval == KLINE_INTERVAL_4HOUR:
        return timedelta(hours=4*size-1)
    elif interval == KLINE_INTERVAL_6HOUR:
        return timedelta(hours=6*size-1)
    elif interval == KLINE_INTERVAL_8HOUR:
        return timedelta(hours=8*size-1)
    elif interval == KLINE_INTERVAL_12HOUR:
        return timedelta(hours=12*size-1)

    elif interval == KLINE_INTERVAL_1DAY:
        return timedelta(days=size-1)

    else:
        return None

def get_interval_timedelta(interval):
    if interval == KLINE_INTERVAL_1MINUTE:
        return timedelta(minutes=1)
    elif interval == KLINE_INTERVAL_3MINUTE:
        return timedelta(minutes=3)
    elif interval == KLINE_INTERVAL_5MINUTE:
        return timedelta(minutes=5)
    elif interval == KLINE_INTERVAL_15MINUTE:
        return timedelta(minutes=15)
    elif interval == KLINE_INTERVAL_30MINUTE:
        return timedelta(minutes=30)

    elif interval == KLINE_INTERVAL_1HOUR:
        return timedelta(hours=1)
    elif interval == KLINE_INTERVAL_2HOUR:
        return timedelta(hours=2)
    elif interval == KLINE_INTERVAL_4HOUR:
        return timedelta(hours=4)
    elif interval == KLINE_INTERVAL_6HOUR:
        return timedelta(hours=6)
    elif interval == KLINE_INTERVAL_8HOUR:
        return timedelta(hours=8)
    elif interval == KLINE_INTERVAL_12HOUR:
        return timedelta(hours=12)

    elif interval == KLINE_INTERVAL_1DAY:
        return timedelta(days=1)

    else:
        return None

def get_interval_seconds(interval):
    if interval == KLINE_INTERVAL_1MINUTE:
        return 1 * SECONDS_MINUTE
    elif interval == KLINE_INTERVAL_3MINUTE:
        return 3 * SECONDS_MINUTE
    elif interval == KLINE_INTERVAL_5MINUTE:
        return 5 * SECONDS_MINUTE
    elif interval == KLINE_INTERVAL_15MINUTE:
        return 15 * SECONDS_MINUTE
    elif interval == KLINE_INTERVAL_30MINUTE:
        return 30 * SECONDS_MINUTE

    elif interval == KLINE_INTERVAL_1HOUR:
        return 1 * SECONDS_HOUR
    elif interval == KLINE_INTERVAL_2HOUR:
        return 2 * SECONDS_HOUR
    elif interval == KLINE_INTERVAL_4HOUR:
        return 4 * SECONDS_HOUR
    elif interval == KLINE_INTERVAL_6HOUR:
        return 6 * SECONDS_HOUR
    elif interval == KLINE_INTERVAL_8HOUR:
        return 8 * SECONDS_HOUR
    elif interval == KLINE_INTERVAL_12HOUR:
        return 12 * SECONDS_HOUR

    elif interval == KLINE_INTERVAL_1DAY:
        return SECONDS_DAY

    else:
        return None

def get_next_open_time(interval, dt):
    return get_open_time(interval, dt) + get_interval_timedelta(interval)

def get_next_open_timedelta(interval, dt):
    return get_next_open_time(interval, dt) - dt

def get_kline_index(key, kline_column_names):
    for index, value in enumerate(kline_column_names):
        if value == key:
            return index

def trans_from_json_to_list(kls, kline_column_names):
    return [[(kline[column_name] if (column_name in kline) else "0") for column_name in kline_column_names] for kline in kls]

def trans_from_list_to_json(kls_list, kline_column_names):
    kls_json = []
    for kl_list in kls_list:
        kl_json = {}
        for idx, v in enumerate(kl_list):
            kl_json[kline_column_names[idx]] = v
        kls_json.append(kl_json)
    return kls_json
