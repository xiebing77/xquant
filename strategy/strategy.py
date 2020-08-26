#!/usr/bin/python
"""strategy"""

class Strategy:
    """Strategy"""

    def __init__(self, strategy_config, engine):
        self.config = strategy_config
        self.engine = engine

        self.highkey     = self.engine.md.kline_key_high
        self.lowkey      = self.engine.md.kline_key_low
        self.openkey     = self.engine.md.kline_key_open
        self.closekey    = self.engine.md.kline_key_close
        self.volumekey   = self.engine.md.kline_key_volume
        self.opentimekey = self.engine.md.kline_key_open_time

        self.highseat     = self.engine.md.get_kline_seat_high()
        self.lowseat      = self.engine.md.get_kline_seat_low()
        self.openseat     = self.engine.md.get_kline_seat_open()
        self.closeseat    = self.engine.md.get_kline_seat_close()
        self.volumeseat   = self.engine.md.get_kline_seat_volume()
        self.opentimeseat = self.engine.md.get_kline_seat_open_time()

        self.aligning_log = "\n%4s" % " "
        self.aligning_info = "\n%68s" % " "
