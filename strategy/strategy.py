#!/usr/bin/python
"""strategy"""

class Strategy:
    """Strategy"""

    def __init__(self, strategy_config, engine):
        self.config = strategy_config
        self.engine = engine

        self.highindex = self.engine.md.highindex
        self.lowindex = self.engine.md.lowindex
        self.openindex = self.engine.md.openindex
        self.closeindex = self.engine.md.closeindex
        self.volumeindex = self.engine.md.volumeindex
        self.opentimeindex = self.engine.md.opentimeindex

        self.aligning_log = "\n%4s" % " "
        self.aligning_info = "\n%68s" % " "
