from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import sma_indicator
import plotly.graph_objects as go

"""
On the 20th days of every month, stocks/ETFs tend to rally, specially if they went down a couple of days down in a row,
it will raise over the next 5~ days

//Variations//
Entry:
    - asd <-- Best
Exit
    - asd <-- Best
"""


class EndOfMonthRally(BaseStrategy):
    def conf(self):
        self.min_bars = 200
        self.flattened = False
        self.p['high_d'] = 26
        self.p['low_d'] = 21
        self.bar_high = 0

    def calculate_indicators(self):
        self.data['day'] = self.data.date.dt.day
        self.data['ma200'] = sma_indicator(self.data.close, 200)
        self.data['atr'] = average_true_range(high=self.data.high, low=self.data.low, close=self.data.close, window=7)

    def plot_indicators(self):
        return go.Scatter(x=self.data.date, y=self.data.ma200, name='ma200', line=dict(color='gold'))

    def notify_order(self, order: Order):
        # return
        if order.status == OrderStatus.Executed:
            if order.side == Side.Sell:
                symbol = '🟢' if self.pnl > 0 else '🔴'
                # self.log(f' {symbol} Sold {int(order.size)}@{order.execprice:.2f} P/L {self.pnl:.2f}')
                if order.exectype == OrderType.Stop:
                    self.flattened = True
            else:
                # self.log(f'️🔷 Long {int(order.size)}@{order.execprice:.2f}')
                pass
        elif order.exectype == OrderType.Stop and order.status == OrderStatus.Pending:
            # self.log(f'️🔶 Stop {int(order.size)}@{order.price:.2f}')
            pass

    def next(self, x: int, bar):
        if not self.position:
            if self.flattened:
                self.flattened = False
                return
            if bar.open > bar.ma200:
                if self.p['high_d'] > bar.day > self.p['low_d']:
                    # if self.down_2_days(x):
                    if self.down_1_day(x):
                        stop_loss = self.stop_atr(bar, .5)
                        entry_price = bar.close
                        # entry_price = self.data.high[x-1]
                        self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=entry_price,
                                        oso=stop_loss)
                        self.bar_high = self.data.high[x-2]
        elif self.position:
            # if self.exit_atr(bar, 1):
            # if self.exit_bar_high(bar):
            if self.exit_by_risk(bar, 1):
                self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=bar.close)

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

    def down_1_day(self, x):
        return self.data.open[x-1] > self.data.close[x-1]

    def down_2_days(self, x):
        return self.data.open[x-2] > self.data.close[x-2] > self.data.open[x-1] > self.data.close[x-1]

    def stop_atr(self, bar, atrs):
        """
        atrs: number of ATRs to set the stop at
        """
        self.size = round(self.p['risk'] / (bar.atr * atrs), 0)
        s_price = bar.close - (bar.atr * atrs)
        self.size = self.size if self.size > 0 else 1
        return Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell, price=s_price, nextbar=True)
