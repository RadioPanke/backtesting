import pandas as pd

from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import ema_indicator
import plotly.graph_objects as go

"""
Based on moving averages cross 

//Variations//
Entry:
    - with moving avg 200 days for entries
    - no ma 200, only fast and slow
Exit:
    - 
"""


class CrossOver(BaseStrategy):
    def conf(self):
        self.min_bars = 30

    def calculate_indicators(self):
        # 10 is 2 weeks
        # self.data['fast'] = ema_indicator(self.data.close, 2)
        self.data['fast'] = ema_indicator(self.data.close, 10)
        # 30 is 6 weeks
        # self.data['slow'] = ema_indicator(self.data.close, 6)
        self.data['slow'] = ema_indicator(self.data.close, 30)
        self.data['atr'] = average_true_range(high=self.data.high, low=self.data.low, close=self.data.close, window=5)

    def plot_indicators(self):
        return go.Scatter(x=self.data.date, y=self.data.fast, name='fast', line=dict(color='red')), \
               go.Scatter(x=self.data.date, y=self.data.slow, name='slow', line=dict(color='steelblue'))

    def notify_order(self, order: Order):
        return
        if order.status == OrderStatus.Executed:
            if order.side == Side.Sell:
                symbol = '🟢' if self.pnl > 0 else '🔴'
                self.log(f' {symbol} Sold {int(order.size)}@{order.execprice:.2f} atr {self.bar.atr:.2f} P/L {self.pnl:.2f}')
            else:
                self.log(f'️🔷 Bought {int(order.size)}@{order.execprice:.2f} atr {self.bar.atr:.2f} P/L {self.pnl:.2f}')
        elif order.exectype == OrderType.Stop and order.status == OrderStatus.Pending:
            self.log(f'️🔶 Stop {int(order.size)}@{order.price:.2f} atr {self.bar.atr:.2f} P/L {self.pnl:.2f}')

    def next(self, x: int, bar):
        self.ma_cross(x, bar)

        if not self.position:
            """ENTRY"""
            if self.cross == 1:
                self.set_size_long(bar)
                self.send_long(bar)
            elif self.cross == -1:
                self.set_size_short(bar)
                self.send_short(bar)
        elif self.position:
            """EXIT"""
            if self.cross == -1 and self.position.side == Side.Buy:
                """liquidate"""
                self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=bar.close)
                # flat and go short
                self.set_size_short(bar)
                self.send_short(bar)
            elif self.cross == 1 and self.position.side == Side.Sell:
                """liquidate"""
                self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=bar.close)
                # flat and go long
                self.set_size_long(bar)
                self.send_long(bar)

    def ma_cross(self, x, bar):
        if self.data.fast[x - 1] > self.data.slow[x - 1] and bar.fast < bar.slow:
            self.cross = -1
        elif self.data.fast[x - 1] < self.data.slow[x - 1] and bar.fast > bar.slow:
            self.cross = 1
        else:
            self.cross = 0

    def send_long(self, bar):
        stop_price = bar.low - bar.atr
        stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell, price=stop_price)   
        self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=bar.close, oso=stop_loss)

    def send_short(self, bar):
        stop_price = bar.high + bar.atr
        stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Buy, price=stop_price)   
        self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=bar.close, oso=stop_loss)

    def set_size_long(self, bar):
        self.size = round(self.p['risk'] / (bar.close - (bar.low - bar.atr)), 0)
        self.size = self.size if self.size > 0 else 1

    def set_size_short(self, bar):
        self.size = round(self.p['risk'] / ((bar.high + bar.atr) - bar.close), 0)
        self.size = self.size if self.size > 0 else 1