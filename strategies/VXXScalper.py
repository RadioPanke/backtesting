from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range

"""
()
"""
class VXXScalper(BaseStrategy):
    def conf(self):
        self.min_bars = 5

    def calculate_indicators(self):
        # Initialize ATR
        self.data['atr'] = average_true_range(high=self.data.high, low=self.data.low, close=self.data.close, window=5)

    def notify_order(self, order: Order):
        return
        if order.status == OrderStatus.Pending and order.exectype == OrderType.Stop:
            self.log(f'Stop buy @{order.price}')
        elif order.status == OrderStatus.Executed:
            if order.side == Side.Sell:
                self.log(f'🔷 Short {int(order.size)}@{order.execprice:.2f}')
            else:
                symbol = '🟢' if self.pnl > 0 else '🔴'
                self.log(f'️{symbol} Cover {int(order.size)}@{order.execprice:.2f} P/L {self.pnl:.2f}')

    def next(self, x: int, bar):
        # 2 days high +- .45%
        # 1.0045
        resistance = round(max([self.data.high[x - 1], self.data.high[x - 2]]) * 1.0045, 2)
        entry_threshold = round(min([self.data.high[x - 1], self.data.high[x - 2]]) * .9955, 2)

        if self.order:
            # it stop is not hit, replace it with new resistance
            self.send_order(size=self.size, exectype=OrderType.Stop, side=Side.Buy, price=resistance)
        elif not self.position:
            if entry_threshold > bar.high > (bar.close * 1.0045):
                # size based on fixed risk amount
                if (resistance - bar.close) > bar.atr:
                    resistance = bar.high * 1.01
                # fixed risk
                self.size = round(self.p['risk'] / (resistance - bar.close), 0)
                # % risk
                # self.size = round(self.cash * .01 / (resistance - bar.close), 0)
                self.size = self.size if self.size > 0 else 1
                self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=bar.close)
                # buy to cover stop
                self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Stop, price=resistance)
