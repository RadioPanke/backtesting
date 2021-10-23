from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import ema_indicator
import plotly.graph_objects as go

"""
Buys on close sells on next open
"""


class TwoBarTrails(BaseStrategy):
    def conf(self):
        self.min_bars = 50

    def calculate_indicators(self):
        self.data['atr'] = average_true_range(high=self.data.high, low=self.data.low, close=self.data.close, window=5)
        # self.data['sma5'] = ema_indicator(self.data.high, 5)
        self.data['sma20'] = ema_indicator(self.data.close, 20)
        # self.data['sma30'] = ema_indicator(self.data.high, 30)
        self.data['sma50'] = ema_indicator(self.data.close, 50)

    def plot_indicators(self):
        return go.Scatter(x=self.data.date, y=self.data.sma20), go.Scatter(x=self.data.date, y=self.data.sma50)

    def notify_order(self, order: Order):
        return
        if order.status == OrderStatus.Executed:
            if order.side == Side.Sell:
                symbol = '🟢' if self.pnl > 0 else '🔴'
                self.log(f' {symbol} Sold {int(order.size)}@{order.execprice:.2f} P/L {self.pnl:.2f}')
            else:
                self.log(f'️🔷 Long {int(order.size)}@{order.execprice:.2f}')

    def next(self, x: int, bar):
        support = round(min([self.data.low[x - 1], self.data.low[x - 2]]) - .05, 2)
        entry_threshold = round(max([self.data.low[x - 1], self.data.low[x - 2]]) + .05, 2)

        if self.order:
            # it stop is not hit, replace it with new support
            self.sell(size=self.size, exectype=OrderType.Stop, price=support)
            return

        if not self.position:
            if bar.low > entry_threshold:
            # if bar.low > entry_threshold and bar.close > bar.sma5:
                if (bar.close - support) > bar.atr:
                    support = bar.low - .15
                self.size = round(self.p['risk'] / (bar.close - support), 0)
                self.buy(size=self.size, exectype=OrderType.Limit, price=bar.close)
                self.sell(exectype=OrderType.Stop, size=self.size, price=support)
