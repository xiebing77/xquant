"""strategy"""

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

