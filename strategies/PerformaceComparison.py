import pandas as pd

from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import ema_indicator
import plotly.graph_objects as go

"""
Used to compare the performace of any given strategy to the overall market in a buy and hold situation
"""


class PerformanceComparison(BaseStrategy):
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
            self.set_size(bar)
            self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=bar.open)
        elif self.position:
            if x == self.data.index[-1]:
                self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=bar.close)

    def set_size(self, bar):
        self.size = round(self.p['risk'] / 20, 0)
        self.size = self.size if self.size > 0 else 1