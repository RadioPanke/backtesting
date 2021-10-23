from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import ema_indicator
from ta.momentum import rsi
import plotly.graph_objects as go


class EngulfingBars(BaseStrategy):
    def conf(self):
        self.min_bars = 7

    def calculate_indicators(self):
        self.data['atr'] = average_true_range(high=self.data.high, low=self.data.low,
                                              close=self.data.close, window=7)

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
            self.i = 0
            # if prev is red and curr is green
            if self.data.open[x-1] > self.data.close[x-1] and bar.close > bar.open:
                # if engulfing
                if bar.close > self.data.open[x-1] and bar.open < self.data.close[x-1]:
                    prev_number = self.data.open[x-1] - self.data.close[x-1]
                    current_number = bar.close - bar.open
                    if current_number > (prev_number * 1.4):
                        self.size = round(self.p['risk'] / (bar.close - self.data.close[x-1]), 0)
                        self.buy(size=self.size, exectype=OrderType.Limit, price=bar.close)
                        self.next_price = True
                        self.sell(size=self.size, exectype=OrderType.Stop, price=self.data.close[x-1])
                        self.i = x
        elif x == self.i + 2:
            self.sell(size=self.size, exectype=OrderType.Limit, price=bar.close)
