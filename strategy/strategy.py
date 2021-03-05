"""strategy"""
from datetime import timedelta, datetime
import common.bill as bl
from engine.order import pst_is_lock

class Strategy:
    """Strategy"""

    def __init__(self, strategy_config, engine):
        self.name = ""
        self.config = strategy_config
        self.engine = engine

        self.instance_id = engine.instance_id

        md = engine.md
        self.md = md

        self.highkey     = md.kline_key_high
        self.lowkey      = md.kline_key_low
        self.openkey     = md.kline_key_open
        self.closekey    = md.kline_key_close
        self.volumekey   = md.kline_key_volume
        self.opentimekey = md.kline_key_open_time
        self.closetimekey = md.kline_key_close_time

        self.highseat     = md.get_kline_seat_high()
        self.lowseat      = md.get_kline_seat_low()
        self.openseat     = md.get_kline_seat_open()
        self.closeseat    = md.get_kline_seat_close()
        self.volumeseat   = md.get_kline_seat_volume()
        self.opentimeseat = md.get_kline_seat_open_time()
        self.closetimeseat = md.get_kline_seat_close_time()

        self.aligning_log = "\n%4s" % " "
        self.aligning_info = "\n%68s" % " "

    def log_info(self, info):
        self.engine.log_info(info)

    def log_warning(self, info):
        self.engine.log_warning(info)

    def log_error(self, info):
        self.engine.log_error(info)

    def log_critical(self, info):
        self.engine.log_critical(info)

    def log_debug(self, info):
        self.engine.log_debug(info)


class SignalStrategy(Strategy):
    def merge_infos(self, infos, aligning):
        info = ""
        for info_tmp in infos:
            info += aligning + info_tmp
        return info

    def on_tick(self, klines=None):
        """ tick处理接口 """
        symbol = self.config["symbol"]
        if not klines:
            kl_cfg = self.config["kline"]
            klines = self.md.get_klines(symbol, kl_cfg["interval"], kl_cfg["size"])
            if len(klines) <= 0:
                return
        self.kls = klines
        self.cur_price = float(klines[-1][self.closeseat])
        cur_close_time = datetime.fromtimestamp(klines[-1][self.closetimeseat]/1000)
        self.engine.handle(symbol, self, self.cur_price, cur_close_time, "")

    def check_bill(self, symbol, position_info):
        bill, info = self.check(symbol, position_info)
        self.log_info(info)
        if not bill:
            return []
        return [bill]

    def calc_ti(self):
        pass

    def check_signal(self):
        symbol = self.config["symbol"]
        signals = []

        if not self.calc_ti():
            return signals

        s, infos = self.signal_long_close()
        if s:
            signals.append(s)

        if "long_lock" in self.config:
            s, infos = self.signal_long_lock(symbol)
            if s:
                signals.append(s)

        s, infos = self.signal_long_open()
        if s:
            signals.append(s)

        s, infos = self.signal_short_close()
        if s:
            signals.append(s)

        if "short_lock" in self.config:
            s, infos = self.signal_short_lock(symbol)
            if s:
                signals.append(s)

        s, infos = self.signal_short_open()
        if s:
            signals.append(s)

        return signals


    def check(self, symbol, position_info):
        info = ""
        if not self.calc_ti():
            return None, info
        bill, infos = self.create_bill(symbol, position_info)
        return bill, self.merge_infos(infos, self.aligning_log)


    def create_bill(self, symbol, position_info):
        log_infos = []
        pst_amount = position_info["amount"]

        if pst_amount == 0 or (pst_amount > 0 and position_info["direction"] == bl.DIRECTION_LONG):
            signal, tmp_infos = self.signal_long_close()
            log_infos += tmp_infos
            if signal:
                if pst_amount > 0:
                    rmk = self.merge_infos(tmp_infos, self.aligning_info)
                    return bl.close_long_bill(0, signal["name"], rmk), log_infos
            else:
                signal, tmp_infos = self.signal_long_open()
                log_infos += tmp_infos
                if signal:
                    rmk = self.merge_infos(tmp_infos, self.aligning_info)
                    return bl.open_long_bill(1, signal["name"], rmk), log_infos

        if pst_amount == 0 or (pst_amount > 0 and position_info["direction"] == bl.DIRECTION_SHORT):
            signal, tmp_infos = self.signal_short_close()
            log_infos += tmp_infos
            if signal:
                if pst_amount > 0:
                    rmk = self.merge_infos(tmp_infos, self.aligning_info)
                    return bl.close_short_bill(0, signal["name"], rmk), log_infos
            else:
                signal, tmp_infos = self.signal_short_open()
                log_infos += tmp_infos
                if signal:
                    rmk = self.merge_infos(tmp_infos, self.aligning_info)
                    return bl.open_short_bill(1, signal["name"], rmk), log_infos

        if pst_amount <= 0:
            return None, log_infos

        if "long_lock" in self.config and position_info["direction"] == bl.DIRECTION_LONG:
            lock_signal, tmp_infos = self.signal_long_lock(symbol)
            log_infos += tmp_infos
            rmk = self.merge_infos(tmp_infos, self.aligning_info)
            if pst_is_lock(position_info):
                if not lock_signal:
                    return bl.unlock_long_bill(position_info["pst_rate"], "unlock", rmk), log_infos
            else:
                if lock_signal:
                    return bl.lock_long_bill(position_info["pst_rate"], lock_signal["name"], rmk), log_infos

        if "short_lock" in self.config and position_info["direction"] == bl.DIRECTION_SHORT:
            lock_signal, tmp_infos = self.signal_short_lock(symbol)
            log_infos += tmp_infos
            rmk = self.merge_infos(tmp_infos, self.aligning_info)
            if pst_is_lock(position_info):
                if not lock_signal:
                    return bl.unlock_short_bill(position_info["pst_rate"], "unlock", rmk), log_infos
            else:
                if lock_signal:
                    return bl.lock_short_bill(position_info["pst_rate"], lock_signal["name"], rmk), log_infos

        return None, log_infos
