from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import ema_indicator
from ta.trend import sma_indicator
from ta.trend import adx_neg
from ta.trend import adx_pos
import plotly.graph_objects as go

"""
Buys an uptrend

//Variations//
Entry:
    - ADX + EMA200
    - 52WHigh <-- Best
Exit
    - Trail ATR2 <-- Best
    - Trail support  
"""


class TrendSeeker(BaseStrategy):
    def conf(self):
        self.min_bars = 251

    def calculate_indicators(self):
        self.data['ma200'] = ema_indicator(self.data.close, 200)
        self.data['atr'] = average_true_range(high=self.data.high, low=self.data.low, close=self.data.close, window=5)
        adx_period = 35
        self.data['adxn'] = adx_neg(high=self.data.high, low=self.data.low, close=self.data.close, window=adx_period)
        self.data['adxp'] = adx_pos(high=self.data.high, low=self.data.low, close=self.data.close, window=adx_period)

    def plot_indicators(self):
        return go.Scatter(x=self.data.date, y=self.data.ma200, name='ma200', line=dict(color='gold')), \
               go.Scatter(x=self.data.date, y=self.data.adxn, name='adx_neg'), \
               go.Scatter(x=self.data.date, y=self.data.adxp, name='adx_pos'),

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
        if not self.position:
            self.entry_52WH(bar, x)
            # self.entry_adx(bar, x, 3.5)
        elif self.position:
            if bar.close > self.position.avgprice:
                # self.trail_support(x)
                self.trail_atr_risk(bar)

    def trail_atr_risk(self, bar):
        """trail stop risk multiplier"""
        pnl = self.size * (bar.close - self.position.avgprice)
        if pnl > self.p['risk'] * 3:
            stop_p = bar.close - (bar.atr * 2)
            if stop_p > self.order.price:
                self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Stop, price=stop_p, nextbar=True)

    def trail_support(self, x):
        """trail stop last support"""
        low = self.data.loc[x - 50:x].low.min() - .01
        if low > self.order.price:
            self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Stop, price=low, nextbar=True)

    def get_stop(self, bar, x, n=5):
        """
        :param n: number of bars to calculate low for stop
        """
        """ATR"""
        # self.size = round(self.p['risk'] / bar.atr, 0)
        # return bar.close - bar.atr
        """low n"""
        low = self.data.loc[x - n:x].low.min() - .01
        self.size = round(self.p['risk'] / (bar.close - low), 0)
        counter = 0
        while (self.size * low) > (self.cash * .5):
            counter = counter + 1
            self.size = self.size - 1
        # if counter > 0:
        #     self.log(f'Cash {self.cash:.2f}')
        #     self.log(f'Size was reduce from {self.size:.0f} money {self.size * low:.1f} ///'
        #              f' to {self.size:.0f} money {self.size * low:.1f}')
        # self.log('Size was 0')
        self.size = self.size if self.size > 0 else 1
        return low

    def entry_adx(self, bar, x, delta=.01):
        if bar.close > bar.ma200:
            if bar.adxp - bar.adxn > delta:
                s_price = self.get_stop(bar, x, n=35)
                stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell, price=s_price)
                self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=bar.close, oso=stop_loss)

    def entry_52WH(self, bar, x):
        high250 = self.data.loc[x - 250:x-5].high.max()
        if bar.close > high250:
            s_price = self.get_stop(bar, x, n=35)
            stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell, price=s_price)
            self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=bar.close, oso=stop_loss)
