import backtrader as bt
from backtrader import Order


class VXXScalperStr(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.order = None
        self.size = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'Cover EXECUTED {order.executed.price:.2f} / qty {int(self.order.size)}')
            elif order.issell():
                self.log(f'Short EXECUTED {order.executed.price:.2f} / qty {int(self.order.size)}')
        self.order = None

    def next(self):
        self.log(f'Open {self.data.open[0]:.2f} / High {self.data.high[0]:.2f}')

        # 2 days high + .45%
        resistance = max([self.data.high[-1], self.data.high[-2]]) * 1.0045
        entry_threshold = min([self.data.high[-1], self.data.high[-2]]) * .9955
        self.log(f'Threshold {entry_threshold:.2f} / Resistance {resistance:.2f}')

        if self.order:
            self.cancel(self.order)
            return

        if not self.position:
            # current close less than 2 days high
            if self.data.open[0] < entry_threshold:
                self.size = round(50 / (resistance - self.data.open[0]), 0)
                price = self.data.open[0] - .03
                self.log(f'Sell order sent at {price:.2f}')
                self.order = self.sell(size=self.size, exectype=Order.Limit,
                                       price=price, valid=0)
        else:
            if self.data.high[0] >= resistance:
                self.order = self.buy(size=self.size)
