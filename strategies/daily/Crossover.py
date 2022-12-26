from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import ema_indicator
from ta.momentum import rsi
from ta.volatility import bollinger_hband
from ta.volatility import bollinger_lband
from ta.trend import adx
from ta.trend import adx_neg
from ta.trend import adx_pos
import plotly.graph_objects as go

"""
Based on moving averages cross

//Variations//
Entry:
    -ADX + EMA (best)
    -EMA cross over
    -Price cross over
Exit:
    -EMA cross over
    -Move stop based on ADX
    -Trail stop based on risk multiplier (best)
    -Trail based on support
"""


class CrossOver(BaseStrategy):
    def conf(self):
        self.min_bars = 60

    def calculate_indicators(self):
        self.data['fast'] = ema_indicator(self.data.close, 10)
        self.data['ma200'] = ema_indicator(self.data.close, 200)
        self.data['slow'] = ema_indicator(self.data.close, 30)
        # self.data['ema50'] = ema_indicator(self.data.close, 50)
        self.data['atr'] = average_true_range(high=self.data.high, low=self.data.low, close=self.data.close, window=5)
        # self.data['bbh'] = bollinger_hband(close=self.data.close, window=30)
        # self.data['bbl'] = bollinger_lband(close=self.data.close, window=30)
        # self.data['rsi'] = rsi(self.data.close, window=4)
        adx_period = 35
        # self.data['adx'] = adx(high=self.data.high, low=self.data.low, close=self.data.close, window=adx_period)
        self.data['adxn'] = adx_neg(high=self.data.high, low=self.data.low, close=self.data.close, window=adx_period)
        self.data['adxp'] = adx_pos(high=self.data.high, low=self.data.low, close=self.data.close, window=adx_period)

    def plot_indicators(self):
        # return go.Scatter(x=self.data.date, y=self.data.fast), go.Scatter(x=self.data.date, y=self.data.slow)
        return go.Scatter(x=self.data.date, y=self.data.fast, name='ema10', line=dict(color='red')), \
               go.Scatter(x=self.data.date, y=self.data.slow, name='ema30', line=dict(color='steelblue')), \
               go.Scatter(x=self.data.date, y=self.data.adxn, name='adx_neg', line=dict(color='red')), \
               go.Scatter(x=self.data.date, y=self.data.adxp, name='adx_pos', line=dict(color='royalblue'))
        # go.Scatter(x=self.data.date, y=self.data.adx, name='adx', line=dict(color='black')), \
        # go.Scatter(x=self.data.date, y=self.data.ema20, name='ema20', line=dict(color='gold')), \
        # go.Scatter(x=self.data.date, y=self.data.ema50, name='ema50', line=dict(color='indigo')), \
        # go.Scatter(x=self.data.date, y=self.data.bbh), go.Scatter(x=self.data.date, y=self.data.bbl),\

    def notify_order(self, order: Order):
        return
        if order.status == OrderStatus.Executed:
            if order.side == Side.Sell:
                symbol = '🟢' if self.pnl > 0 else '🔴'
                self.log(f' {symbol} Sold {int(order.size)}@{order.execprice:.2f} P/L {self.pnl:.2f}')
            else:
                self.log(f'️🔷 Long {int(order.size)}@{order.execprice:.2f} rsi {self.bar.rsi:.2f}')
        elif order.exectype == OrderType.Stop and order.status == OrderStatus.Pending:
            self.log(f'️🔶 Stop {int(order.size)}@{order.price:.2f} atr {self.bar.atr:.2f}')

    def next(self, x: int, bar):
        self.ma_cross(x, bar)

        if not self.position:
            if self.cross == 1 and bar.close > bar.ma200:
                self.entry_adx(bar, x, 3.5)
                # self.entry_ma(bar, x)
        elif self.position:
            if self.cross == -1:
                """liquidate"""
                self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=bar.close)
            elif bar.close > self.position.avgprice:
                """trail stop risk multiplier"""
                pnl = self.size * (bar.close - self.position.avgprice)
                if pnl > self.p['risk'] * 3:
                    stop_p = bar.close - (bar.atr * 2)
                    if stop_p > self.order.price:
                        self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Stop, price=stop_p, nextbar=True)
            # elif bar.close > self.position.avgprice:
            #     """trail stop last support"""
            #     low = self.data.loc[x - 35:x].low.min() - .01
            #     if low > self.order.price:
            #         self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Stop, price=low, nextbar=True)

    def ma_cross(self, x, bar):
        if self.data.fast[x - 1] > self.data.slow[x - 1] and bar.fast < bar.slow:
            self.cross = -1
        elif self.data.fast[x - 1] < self.data.slow[x - 1] and bar.fast > bar.slow:
            self.cross = 1
        else:
            self.cross = 0

    def get_stop(self, bar, x):
        """ATR"""
        # self.size = round(self.p['risk'] / bar.atr, 0)
        # self.size = self.size if self.size > 0 else 1
        # return bar.close - bar.atr
        """low n"""
        n = 5
        # inclusive range
        low = self.data.loc[x - n:x].low.min() - .01
        self.size = round(self.p['risk'] / (bar.close - low), 0)
        # self.size = round((self.cash * .02) / (bar.close - low), 0)
        counter = 0
        while (self.size * low) > (self.cash * .5):
            counter = counter + 1
            self.size = self.size - 1
        self.size = self.size if self.size > 0 else 1
        return low

    def entry_adx(self, bar, x, delta=.01):
        if abs(bar.adxp - bar.adxn) > delta:
            s_price = self.get_stop(bar, x)
            stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell,
                              price=s_price, nextbar=True)
            self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=bar.close, oso=stop_loss)

    def entry_ma(self, bar, x):
        s_price = self.get_stop(bar, x)
        stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell,
                          price=s_price, nextbar=True)
        self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=bar.close, oso=stop_loss)
