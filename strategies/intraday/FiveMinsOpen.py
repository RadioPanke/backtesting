import pandas as pd

from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import sma_indicator
import plotly.graph_objects as go

"""
TODO

//Variations//
Entry:
    - asd <-- Best
Exit
    - asd <-- Best
"""


# TODO this whole thing is not done
class FiveMinsOpen(BaseStrategy):
    def conf(self):
        self.marketOpenTime = pd.Timestamp(2022, 1, 1, 9, 35, 0).time()
        self.marketOpen = None
        self.openBar = None

    def calculate_indicators(self):
        self.data['marketOpen'] = self.data.date.dt.time == self.marketOpenTime

    def notify_order(self, order: Order):
        return
        if order.status == OrderStatus.Executed:
            if order.side == Side.Sell:
                symbol = '🟢' if self.pnl > 0 else '🔴'
                self.log(f' {symbol} Sold {int(order.size)}@{order.execprice:.2f} P/L {self.pnl:.2f}')
            else:
                self.log(f'️🔷 Long {int(order.size)}@{order.execprice:.2f}')
        elif order.exectype == OrderType.Stop and order.status == OrderStatus.Pending:
            self.log(f'️🔶 Stop {int(order.size)}@{order.price:.2f}')

    def next(self, x: int, bar):
        if bar.marketOpen:
            self.marketOpen = True
            self.openBar = bar
            self.openIndex = x
        elif self.marketOpen and x == (self.openIndex + 2):
            low = min(self.data.low[x - 2], self.data.low[x - 1], bar.low)
            if self.openBar.low == low:
                high = max(self.data.high[x - 2], self.data.high[x - 1], bar.high)
                self.size = round(self.p['risk'] / (high - low), 0)
                s_price = low - .01
                self.size = self.size if self.size > 0 else 1
                stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell, price=s_price)
                entry_price = bar.close
                self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=entry_price,
                                oso=stop_loss)
        if self.position:
            self.marketOpen = False

    def exit_atr(self, bar, atrs):
        """
        exit when price is N ATRs above the entry
        """
        return abs(bar.close - self.position.avgprice) > (bar.atr * atrs)

    def exit_bar_high(self, bar):
        """
        exit when price is above the initial 2 down days
        """
        return bar.close > self.bar_high

    def exit_by_risk(self, bar, risk_multiplier):
        """
        exit when P/L is higher than the risk multiplier
        """
        return ((bar.high - self.position.avgprice) * self.size) >= (self.p['risk'] * risk_multiplier)


