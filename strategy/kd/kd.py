import common.bill as bl
import utils.indicator as ic
import utils.ti as ti
from strategy.strategy import Strategy


class KDStrategy(Strategy):
    """ simple KD stragegy"""

    def __init__(self, strategy_config, engine):
        super().__init__(strategy_config, engine)
        self.kline = strategy_config["kline"]
        self.offset = strategy_config["kdj_offset"]


    def check(self, symbol, klines):
        """ kdj指标，金叉全买入，下降趋势部分卖出，死叉全卖出 """
        '''
        kdj_arr = ic.py_kdj(klines, self.highseat, self.lowseat, self.closeseat)
        cur_k = kdj_arr[-1][1]
        cur_d = kdj_arr[-1][2]
        '''
        kkey, dkey = ti.KD(klines, self.closekey, self.highkey, self.lowkey)
        cur_k = klines[-1][kkey]
        cur_d = klines[-1][dkey]

        signal_info = (
            "(%6.2f) k(%6.2f) d(%6.2f)"
            % (
                cur_k - cur_d,
                cur_k,
                cur_d,
            )
        )

        offset = self.offset[0]
        if cur_k > cur_d + offset:
            # 金叉
            return bl.open_long_bill(1, "买：", signal_info)

        elif cur_k < cur_d - offset:
            # 死叉
            return bl.close_long_bill(0, "卖：", signal_info)


        return None


    def on_tick(self, klines=None):
        """ tick处理接口 """
        symbol = self.config["symbol"]
        # 之前的挂单全撤掉
        self.engine.cancle_orders(symbol)

        if not klines:
            klines = self.engine.md.get_klines(symbol, self.kline["interval"], self.kline["size"])
        self.cur_price = float(klines[-1][self.closeseat])

        check_signals = []
        signal = self.check(symbol, klines)
        if signal:
            check_signals.append(signal)
        position_info = self.engine.get_position(symbol, self.cur_price)
        self.engine.handle_order(symbol, position_info, self.cur_price, check_signals)
