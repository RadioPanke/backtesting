import pandas as pd

from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import sma_indicator
import plotly.graph_objects as go

"""
Not fully implemented, just testing out the code

10/20/50 SMA from Qullamaggie

Nope:
Entry
- fast > slow
- bar.atr > bar.atr_sma12 * 1.1
Exit
- close < slow

//Variations//
Entry:
    - close > slow
    - close > previous 2 highs
Exit:
    - End of day
    - fast cross slow
Results:
- Final P/L:          1544.96
- Profitability:      1.10
- Win %:              50.40
- Trades:             625
// - - - - - //
Entry:
    - close > slow
    - close > previous 2 highs
    - no trade after 3pm NY
Exit:
    - End of day
    - fast cross slow
Results:
- Final P/L:          615.45
- Win %:              48.88
- Profitability:      1.05
- Trades:             536
// - - - - - //
Entry:
    - close > slow
    - close > previous 2 highs
    - Trades after 11:00 NY
Exit:
    - End of day
    - fast cross slow
Results:
- Final P/L:          1544.39
- Win %:              49.23
- Profitability:      1.13
- Trades:             522
// - - - - - //
Entry:
    - fast > slow
    - close > previous 2 highs
    - Trades after 11:00 NY
Exit:
    - End of day
    - fast cross slow
Results:

// - - - - - //
"""


class QullamaggieSMAs(BaseStrategy):
    def conf(self):
        self.min_bars = 20

    def calculate_indicators(self):
        self.data['fast'] = sma_indicator(self.data.close, 10)
        self.data['slow'] = sma_indicator(self.data.close, 20)
        self.data['atr'] = average_true_range(high=self.data.high, low=self.data.low, close=self.data.close, window=5)
        # shift(1) to avoid lookahead
        self.data['atr_sma12'] = self.data.atr.rolling(12).mean().shift(1)

    def plot_indicators(self):
        return go.Scatter(x=self.data.index, y=self.data.fast, name='fast', line=dict(color='red')), \
               go.Scatter(x=self.data.index, y=self.data.slow, name='slow', line=dict(color='steelblue'))

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
            # account for volume?
            
            # if bar.close > bar.slow and bar.close > self.data.high[x - 1] and bar.close > self.data.high[x - 2] and bar.fast > bar.slow:
            isBefore15hrs = bar.date.time() < pd.Timestamp("15:00").time()
            isAfter11hrs = bar.date.time() >= pd.Timestamp("11:00").time()
            isCloseHTSlow = bar.close > bar.slow
            isFastHTSlow = bar.fast > bar.slow
            isAtrLTAtrSMA = bar.atr < bar.atr_sma12 
            isRangeHTAtr = bar.high - bar.low > bar.atr * .8
            if isCloseHTSlow and bar.close > self.data.high[x - 1] and bar.close > self.data.high[x - 2] and isAfter11hrs and isAtrLTAtrSMA:
                self.set_size_long(bar)
                self.send_long(bar)
            # if self.cross == 1:
            #     self.set_size_long(bar)
            #     self.send_long(bar)
            # elif self.cross == -1:
            #     self.set_size_short(bar)
            #     self.send_short(bar)
        elif self.position:
            """EXIT"""
            isEndOfDay = bar.date.time() == pd.Timestamp(year=2025, month=6, day=3, hour=15, minute=55).time()
            ifCross = self.cross == -1
            ifCloseLessThanSlow = bar.close < bar.slow
            if (ifCross and self.position.side == Side.Buy) or isEndOfDay:
                """liquidate"""
                self.send_order(size=self.size, side=Side.Sell, exectype=OrderType.Limit, price=bar.close)
            # elif self.cross == 1 and self.position.side == Side.Sell:
            #     """liquidate"""
            #     self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=bar.close)
            #     # flat and go long
            #     self.set_size_long(bar)
            #     self.send_long(bar)

    def ma_cross(self, x, bar):
        # if bar.date.time() == pd.Timestamp(year=2025, month=6, day=3, hour=14, minute=0).time():
        #     pass  # Debug breakpoint
        #     a = self.data.fast[x - 1]
        #     b = self.data.slow[x - 1]
        #     c = bar.fast
        #     d = bar.slow
        #     e = bar.open
        #     f = bar.high
        #     g = bar.low
        #     h = bar.close
        if self.data.fast[x - 1] > self.data.slow[x - 1] and bar.fast < bar.slow:
            # short
            self.cross = -1
        elif self.data.fast[x - 1] < self.data.slow[x - 1] and bar.fast > bar.slow:
            # long
            self.cross = 1
        else:
            self.cross = 0

    def send_long(self, bar):
        stop_price = bar.low - bar.atr
        # stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell, price=stop_price)   
        # self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=bar.close, oso=stop_loss)
        self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=bar.close)

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