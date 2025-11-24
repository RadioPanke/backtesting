import pandas as pd

from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import sma_indicator
from ta.volatility import BollingerBands
import plotly.graph_objects as go

"""
TODO This
- Upside up bar, reversal trade, if bar 2 is below 1st bar, and above 1st bar, trade the reversal
    This can also go somehow with umbrella trades?

Hotdogs 14:30 in video and hamburgers, similar time, both are used the same way?

By Linda Raschke
  Umbrela trade
- Trade with the trend
- Hold 2~ bars
- Wick up (doji?), next bar's body is inside the with of the 1st bar
Customizations:
- It ATR > ATR mean 10% or morewe have volatility
- Above 20 SMA for long, below SMA for short
- If it reached 1st deviation recently it could mean a bounce so long? and reversed for short?
- Even touching the SMA with good volatility good?

Test for 1/5 mins

//Variations//
Entry:
    - with moving blah blah blah
Exit:
    - 
"""


class LindaScalps(BaseStrategy):
    def conf(self):
        self.min_bars = 20
        self.atr_volatility = 1.1
        self.bbands_window = 20
        self.bbands_window_dev = 1.7

    def calculate_indicators(self):
        bb_indicator = BollingerBands(close=self.data.close, window=self.bbands_window, window_dev=self.bbands_window_dev, fillna=True)
        self.data["sma"] = bb_indicator.bollinger_mavg()
        self.data["high_band"] = bb_indicator.bollinger_hband()
        self.data["low_band"] = bb_indicator.bollinger_lband()
        self.data['atr'] = average_true_range(high=self.data.high, low=self.data.low, close=self.data.close, window=14)
        self.data['atr_ma'] = self.data['atr'].rolling(14).mean()

    def plot_indicators(self):
        # go.Scatter(x=self.data.index, y=self.data.fast, name='fast', line=dict(color='red'))
        return go.Scatter(x=self.data.index, y=self.data.sma, name='sma', line=dict(color='blue')), \
               go.Scatter(x=self.data.index, y=self.data.high_band, name='high_band', line=dict(color='red')), \
               go.Scatter(x=self.data.index, y=self.data.low_band, name='low_band', line=dict(color='red'))

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
            if self.order:
                # cancel order if not filled on next bar
                self.order = None

            """ENTRY"""
            '''LONG'''
            if bar.high > bar.sma or bar.close < bar.low_band:
            # if bar.close < bar.low_band:
                if bar.atr > (bar.atr_ma * self.atr_volatility):
                    if self.isUmbrella(x, bar):
                        self.set_size_long(x, bar)
                        self.send_long(x, bar)
                        self.position_start = x
        elif self.position:
            """EXIT"""
            # # if already 2x
            # if (bar.high - self.position.avgprice) > self.long_points_risk * 2:
            #     exit_price = self.position.avgprice + self.long_points_risk * 2
            #     self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=exit_price)
            # # after 2 bars
            # elif x == self.position_start + 2 and self.position.side == Side.Buy:
            #     self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=bar.close)
            # if already 2x
            if x == self.position_start + 2 and self.position.side == Side.Buy:
                self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=bar.close)

    def isUmbrella(self, x, bar):
        body_price = max(self.data.open[x - 1], self.data.close[x - 1])
        return self.data.high[x - 1] > bar.open and self.data.high[x - 1] > bar.close \
                    and  body_price < bar.open and body_price < bar.close

    def send_long(self, x, bar):
        stop_price = self.bar_low_stop
        stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell, price=stop_price)   
        self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Stop, price=self.data.high[x - 1], oso=stop_loss, nextbar=True)

    def send_short(self, bar):
        stop_price = bar.high + bar.atr
        stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Buy, price=stop_price)   
        self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=bar.close, oso=stop_loss)

    def set_size_long(self, x, bar):
        self.bar_low_stop = min(self.data.low[x - 1], bar.low)
        self.long_points_risk = self.data.high[x - 1] - self.bar_low_stop
        self.size = round(self.p['risk'] / self.long_points_risk, 0)
        self.size = self.size if self.size > 0 else 1

    def set_size_short(self, bar):
        self.size = round(self.p['risk'] / ((bar.high + bar.atr) - bar.close), 0)
        self.size = self.size if self.size > 0 else 1