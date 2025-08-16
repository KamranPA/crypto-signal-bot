# strategies/FibBOSFVGStrategy.py
import backtrader as bt
from utils.fib_levels import calculate_fib_levels
from utils.detect_fvg import detect_fvg
from utils.detect_bos import detect_bos
from utils.logger import setup_logger
from utils.telegram_bot import send_telegram_signal

class FibBOSFVGStrategy(bt.Strategy):
    params = (
        ('fib_entry', 0.71),
        ('fib_tp', 0.0),
        ('fib_sl', 1.0),
        ('lookback', 100),
    )

    def __init__(self):
        self.data_close = self.datas[0].close
        self.data_high = self.datas[0].high
        self.data_low = self.datas[0].low
        self.order = None
        self.log = setup_logger('strategy', f'logs/{self.datas[0]._name}.log')

    def next(self):
        if self.order:
            return

        if len(self) < self.p.lookback:
            return

        # آخرین HH و LL
        recent_highs = self.data_high.get(ago=0, size=self.p.lookback)
        recent_lows = self.data_low.get(ago=0, size=self.p.lookback)

        hh = max(recent_highs)
        ll = min(recent_lows)

        # تشخیص روند: اگر HH بعد از LL → نزولی
        idx_hh = list(recent_highs).index(hh)
        idx_ll = list(recent_lows).index(ll)

        if idx_hh < idx_ll:  # HH قبل از LL → روند نزولی
            fib_levels = calculate_fib_levels(hh, ll)
            entry_price = fib_levels[self.p.fib_entry]
            tp_price = fib_levels[self.p.fib_tp]
            sl_price = fib_levels[self.p.fib_sl]

            current_price = self.data_close[0]

            # تشخیص FVG
            fvg = detect_fvg(self.data_high, self.data_low, self.data_close)
            bos = detect_bos(self.data_high, self.data_low, self.p.lookback)

            # ورود شورت
            if (abs(current_price - entry_price) / entry_price < 0.001
                    and bos == 'bearish'
                    and fvg and fvg['type'] == 'bearish'):

                self.log.info(f"SHORT ENTRY at {current_price}")
                self.order = self.sell()

                if self.p.get('enable_telegram', True):
                    send_telegram_signal(
                        symbol=self.datas[0]._name,
                        signal="SELL (SHORT)",
                        entry=current_price,
                        tp=tp_price,
                        sl=sl_price,
                        reason="Fib 71% + BOS + FVG"
                    )

                # تنظیم SL و TP
                self.buy(exectype=bt.Order.Stop, price=sl_price, size=1)
                self.sell(exectype=bt.Order.Limit, price=tp_price, size=1)
