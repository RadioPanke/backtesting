import backtrader as bt
import math


class FillStr(bt.Strategy):
    params = dict(
        periods=[10, 30],
        matype=bt.ind.SMA,
    )

    def __init__(self):
        self.cheating = self.cerebro.p.cheat_on_open
        mas = [self.p.matype(period=x) for x in self.p.periods]
        self.signal = bt.ind.CrossOver(*mas)
        self.order = None

    def notify_order(self, order):
        if order.status != order.Completed:
            return

        self.order = None
        print(f'{bt.num2date(order.executed.dt).date()} {"Buy" * order.isbuy() or "Sell"} / '
              f'Executed at price {order.executed.price}')

    def next(self):
        # print(f'{self.data.datetime.date()} next / open {self.data.open[0]} /'
        #       f' close {self.data.close[0]} / cross {self.signal[0]}')

        if self.cheating:
            return
        print(f'{self.data.datetime.date()} next / open {self.data.open[0]} / high {self.data.high[0]} / cross {self.signal[0]}')
        self.operate(fromopen=False)

    def next_open(self):
        if not self.cheating:
            return
        print(f'{self.data.datetime.date()} next_open / open {self.data.open[0]} / high {self.data.high[0]} / cross {self.signal[0]}')
        self.operate(fromopen=True)

    def operate(self, fromopen):
        if self.order is not None:
            return
        if self.position:
            if self.signal < 0:
                self.order = self.close()
        elif self.signal > 0:
            print(f'{self.data.datetime.date()} Send Buy, fromopen {fromopen}, close {self.data.close[0]}')
            self.order = self.buy()