#!/usr/bin/python
"""strategy"""

class Strategy:
    """Strategy"""

    def __init__(self, strategy_config, engine):
        self.config = strategy_config
        self.engine = engine

        for index, value in enumerate(self.engine.get_kline_column_names()):
            if value == "high":
                self.highindex = index
            if value == "low":
                self.lowindex = index
            if value == "open":
                self.openindex = index
            if value == "close":
                self.closeindex = index
            if value == "volume":
                self.volumeindex = index
            if value == "open_time":
                self.opentimeindex = index

        self.aligning_log = "\n%4s" % " "
        self.aligning_info = "\n%68s" % " "
