# strategies/FibBOSFVGStrategy.py
"""
استراتژی معاملاتی: Fib 71% + BOS + FVG
با پشتیبانی از ارسال سیگنال به تلگرام
"""

import backtrader as bt
from utils.fib_levels import calculate_fib_levels
from utils.detect_fvg import detect_fvg
from utils.detect_bos import detect_bos
from utils.telegram_bot import send_telegram_signal
from utils.logger import setup_logger

class FibBOSFVGStrategy(bt.Strategy):
    params = (
        ('fib_entry', 0.71),           # سطح ورود فیبوناچی
        ('fib_tp', 0.0),               # سطح هدف (0.0 = LL)
        ('fib_sl', 1.0),               # سطح حد ضرر (1.0 = HH)
        ('lookback', 100),             # تعداد کندل برای محاسبه
        ('enable_telegram', True),     # فعال‌سازی ارسال سیگنال به تلگرام
        ('debug', True),               # فعال‌سازی لاگ‌گیری
    )

    def __init__(self):
        self.data_close = self.datas[0].close
        self.data_high = self.datas[0].high
        self.data_low = self.datas[0].low
        self.order = None
        self.fvg_list = []
        self.bos_list = []

        # راه‌اندازی لاگ
        if self.p.debug:
            self.log = setup_logger(
                name=f'strategy_{self.datas[0]._name}',
                log_file=f'logs/{self.datas[0]._name}.log'
            )
        else:
            self.log = None

    def log(self, txt, debug=True):
        if debug and self.p.debug and self.log:
            self.log.info(txt)

    def next(self):
        if self.order:
            return

        if len(self) < self.p.lookback:
            return

        # تشخیص روند: آخرین HH و LL
        recent_highs = self.data_high.get(ago=0, size=self.p.lookback)
        recent_lows = self.data_low.get(ago=0, size=self.p.lookback)

        if len(recent_highs) == 0 or len(recent_lows) == 0:
            return

        hh = max(recent_highs)
        ll = min(recent_lows)

        # شاخص‌های موقعیت HH و LL
        idx_hh = list(recent_highs).index(hh)
        idx_ll = list(recent_lows).index(ll)

        # فقط اگر HH قبل از LL باشد (روند نزولی)
        if idx_hh < idx_ll:
            fib_levels = calculate_fib_levels(hh, ll)
            entry_price = fib_levels[self.p.fib_entry]
            tp_price = fib_levels[self.p.fib_tp]
            sl_price = fib_levels[self.p.fib_sl]

            current_price = self.data_close[0]

            # تشخیص FVG
            fvg = detect_fvg(self.data_high, self.data_low, self.data_close)
            if fvg:
                self.fvg_list.append(fvg)

            # تشخیص BOS
            bos = detect_bos(self.data_high, self.data_low, self.p.lookback)
            if bos:
                self.bos_list.append(bos)

            # ورود شورت: قیمت در 71%، BOS نزولی، FVG نزولی
            if (abs(current_price - entry_price) / entry_price < 0.001
                    and bos == 'bearish'
                    and fvg and fvg['type'] == 'bearish'):

                self.log(f"SHORT ENTRY at {current_price}")
                self.order = self.sell()

                # ارسال سیگنال به تلگرام (اختیاری)
                if self.p.enable_telegram:
                    try:
                        send_telegram_signal(
                            symbol=self.datas[0]._name,
                            signal="SELL (SHORT)",
                            entry=current_price,
                            tp=tp_price,
                            sl=sl_price,
                            reason="Fib 71% + BOS + FVG"
                        )
                    except Exception as e:
                        if self.p.debug:
                            print(f"[TELEGRAM ERROR] {e}")

                # تنظیم حد ضرر و هدف
                self.buy(exectype=bt.Order.Stop, price=sl_price, size=1)
                self.sell(exectype=bt.Order.Limit, price=tp_price, size=1)

            # ورود لانگ: (اختیاری - در صورت تمایل می‌توانید اضافه کنید)
            # elif (abs(current_price - entry_price) / entry_price < 0.001
            #         and bos == 'bullish'
            #         and fvg and fvg['type'] == 'bullish'):
            #     self.log(f"LONG ENTRY at {current_price}")
            #     self.order = self.buy()
            #     if self.p.enable_telegram:
            #         send_telegram_signal(...)
