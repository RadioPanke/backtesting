import pandas as pd

from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import sma_indicator
from ta.volatility import BollingerBands
import plotly.graph_objects as go

"""
YoYo

move with volume more than sma volume and it retraces less them mid of the bars move, go long in tha direction of the first bar and sell at the next 2 bars???

Test for 1/5 mins

//VariationA//
Entry:
    - Vol 30% > prev bar
    - Next bar retraces to mid or more
Exit:
    - 2 bars
//VariationA//
Entry:
    - 
Exit:
    - 
"""


class YoYo(BaseStrategy):
    def conf(self):
        self.vol_increase = 1.3
        self.min_bars = 20

    def calculate_indicators(self):
        pass

    # def plot_indicators(self):
    #     return go.Scatter(x=self.data.index, y=self.data.sma, name='sma', line=dict(color='blue')), \
    #            go.Scatter(x=self.data.index, y=self.data.high_band, name='high_band', line=dict(color='red')), \
    #            go.Scatter(x=self.data.index, y=self.data.low_band, name='low_band', line=dict(color='red'))

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
        if not self.position:
            """ENTRY"""
            volIncrease = self.data.volume[x - 1] > self.data.volume[x - 2] * self.vol_increase
            middle2 = ((self.data.high[x - 2] - self.data.low[x - 2]) / 2) + self.data.low[x - 2]
            impulseBar = self.data.low[x - 1] < middle2 and self.data.high[x - 1] > self.data.high[x - 2]
            self.middle1 = ((self.data.high[x - 1] - self.data.low[x - 1]) / 2) + self.data.low[x - 1]
            retrace = bar.low < self.middle1

            if volIncrease and impulseBar and retrace:
                self.set_size_long(x, bar)
                self.send_long(x, bar)
                self.position_start = x

        elif self.position:
            """EXIT"""
            if x == self.position_start + 2:
                self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=bar.close)

    def send_long(self, x, bar):
        stop_price = self.bar_low_stop
        stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell, price=stop_price)   
        self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=self.middle1, oso=stop_loss, nextbar=True)

    def set_size_long(self, x, bar):
        self.bar_low_stop = self.data.low[x - 1]
        self.long_points_risk = self.data.high[x - 1] - self.bar_low_stop
        self.size = round(self.p['risk'] / self.long_points_risk, 0)
        self.size = self.size if self.size > 0 else 1