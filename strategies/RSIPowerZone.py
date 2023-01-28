from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import ema_indicator
from ta.momentum import rsi
import plotly.graph_objects as go

"""
Buys on close sells on next open
"""


class RSIPowerZone(BaseStrategy):
    def conf(self):
        self.min_bars = 200

    def calculate_indicators(self):
        self.data['sma'] = ema_indicator(self.data.close, 200)
        self.data['rsi'] = rsi(close=self.data.close, window=4)
        self.data['atr'] = average_true_range(high=self.data.high, low=self.data.low,
                                              close=self.data.close, window=7)

    def plot_indicators(self):
        return go.Scatter(x=self.data.date, y=self.data.sma)

    def notify_order(self, order: Order):
        return
        if order.status == OrderStatus.Executed:
            if order.side == Side.Sell:
                symbol = '🟢' if self.pnl > 0 else '🔴'
                self.log(f' {symbol} Sold {int(order.size)}@{order.execprice:.2f} P/L {self.pnl:.2f}')
            else:
                self.log(f'️🔷 Long {int(order.size)}@{order.execprice:.2f} rsi {self.bar.rsi:.2f}')

    def next(self, x: int, bar):
        if not self.position:
            if bar.close > bar.sma and bar.rsi < 30:
                    support = bar.close - bar.atr
                    self.level = support
                    self.size = round(self.p['risk'] / (bar.close - support), 0)
                    self.buy(size=self.size, exectype=OrderType.Limit, price=bar.close)
            self.added = False
        elif bar.rsi >= 55:
            self.sell(size=self.size, exectype=OrderType.Limit, price=bar.close)
            self.added = False
        elif bar.close < self.level and not self.added:
            self.buy(size=self.size, exectype=OrderType.Limit, price=bar.close)
            self.size = self.size * 2
            self.sell(size=self.size, exectype=OrderType.Stop, price=(bar.close - bar.atr))
            self.added = True

