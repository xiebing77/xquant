

class SignalEngine:
    """引擎"""

    def __init__(self, instance_id, config, log_switch):
        self.instance_id = instance_id
        self.log_switch = log_switch


    def log_info(self, info):
        if self.log_switch:
            log.info(info)

    def log_warning(self, info):
        if self.log_switch:
            log.warngin(info)

    def log_error(self, info):
        if self.log_switch:
            log.error(info)

    def log_critical(self, info):
        if self.log_switch:
            log.critical(info)

    def log_debug(self, info):
        if self.log_switch:
            log.debug(info)


class TestSignal(SignalEngine):
    def __init__(self, md, instance_id, config, log_switch=False):
        super().__init__(instance_id, config, log_switch)
        self.md = md
        self.signals = []

    def handle_signal(self, symbol, signals, price, create_time):
        for s in signals:
            s["price"] = price
            s["create_time"] = create_time
        self.signals += signals

    def get_signalsets(self):
        signalsets = {}
        for s in self.signals:
            s_name = s["name"]
            if s_name not in signalsets:
                signalsets[s_name] = [s]
            else:
                signalsets[s_name].append(s)
        return signalsets

    def handle(self, symbol, strategy, price, create_time, info):
        signals = strategy.check_signal_single()
        self.handle_signal(symbol, signals, price, create_time)
        return

