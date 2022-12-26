"""
HolyGrail

-14 ADX to define a trend
-20 EMA for entries

When price touches EMA set a buy stop at the high of previous bar
Once filled set a stop loss at the new low
Trail the stop of get out at the next swing high

NOTE: better for intraday???
"""
from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.trend import ema_indicator
from ta.trend import adx
import plotly.graph_objects as go


class HolyGrail(BaseStrategy):
    def conf(self):
        self.min_bars = 25
        self.trigger = None

    def calculate_indicators(self):
        self.data['ema'] = ema_indicator(self.data.close, 20)
        self.data['adx'] = adx(self.data.high, self.data.low, self.data.close, 14)

    def plot_indicators(self):
        return go.Scatter(x=self.data.date, y=self.data.ema), go.Scatter(x=self.data.date, y=self.data.adx)

    def notify_order(self, order: Order):
        if order.status == OrderStatus.Executed:
            if order.side == Side.Sell:
                symbol = '🟢' if self.pnl > 0 else '🔴'
                # self.log(f' {symbol} Sold {int(order.size)}@{order.execprice:.2f} P/L {self.pnl:.2f}')
            else:
                # self.log(f'️🔷 Long {int(order.size)}@{order.execprice:.2f}')
                self.trigger = None
        elif self.order.exectype is OrderType.Stop and self.order.side is Side.Sell:
            # self.log(f'Stop at {self.order.price:.2f}')
            pass
        elif self.trigger is not None:
            pass
            # self.log(f'Trigger XXX {self.trigger}')

    def next(self, x: int, bar):
        if not self.position and bar.adx >= 30 and self.trigger is None:
            self.price_cross_on_previous(x)
            if self.cross == -1:
                if bar.ema > self.data.ema[x - 15]:
                    high = bar.open if bar.open > self.data.high[x-1] else self.data.high[x-1]
                    self.size = round(self.p['risk'] / (high - self.data.low[x-1]), 0)
                    self.trigger = x - 1
                    stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell, price=self.data.low[x-1] - .01)
                    self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Stop, price=self.data.high[x-1] + .01, oso=stop_loss)
        elif not self.position and self.trigger is not None:
            # move entry
            high = bar.open if bar.open > self.data.high[x - 1] else self.data.high[x - 1]
            low = self.data.loc[self.trigger:x].low.min()
            self.size = round(self.p['risk'] / (high - low), 0)
            stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell, price=low - .01)
            self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Stop, price=self.data.high[x-1] + .01, oso=stop_loss)
        elif self.position:
            # PROFITS // exit at trend 5 or at previous swing high????
            prev_high = self.data.loc[x-10:x].high.max()
            trend = self.trend(x, 5)
            if bar.high >= prev_high:
            # if trend > 2 or bar.high >= prev_high:
                # take profits
                self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=bar.close)

    def trend(self, x, length):
        last_price = self.data.close[x - length - 1]
        local_trend = 0
        for bar in self.data.close.loc[x-length:x-1]:
            if bar > last_price:
                local_trend += 1
            elif bar < last_price:
                local_trend -= 1
            last_price = bar
        return local_trend

    def price_cross_on_previous(self, x):
        # calculate 'touch' vs 'close' below EMA
        """
        Calculates price cross on previous bar
        low = touch
        close = cross close
        """
        if self.data.low[x - 2] > self.data.ema[x - 2] and self.data.low[x - 1] < self.data.ema[x - 1]:
            self.cross = -1
        elif self.data.low[x - 2] < self.data.ema[x - 2] and self.data.low[x - 1] > self.data.ema[x - 1]:
            self.cross = 1
        else:
            self.cross = 0