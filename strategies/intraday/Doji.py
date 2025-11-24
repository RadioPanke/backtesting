import pandas as pd

from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import sma_indicator
from ta.volatility import BollingerBands
import plotly.graph_objects as go

"""
Doji

Doji with volume ready to bounce at low of day or close?

Test for 1/5 mins

//VariationA//
Entry:
- Vol 1.3 > sma6
- .2 or .0006 close to LOD, or at LOD
- Low of bar -1 > middle of bar
- After 9am
Exit:
- 1x
//VariationA//
Entry:
- 
Exit:
- 
"""


class Doji(BaseStrategy):
    def conf(self):
        # from BaseStrat, how many to let go before calculating indicators
        self.min_bars = 20
        self.volume_increase = 1
        self.atr_increase = 1.1
        self.rr_factor = 2

    def calculate_indicators(self):
        self.data["vol_sma"] = self.data["volume"].rolling(6).mean().shift(1)
        self.data["atr"] = average_true_range(
            high=self.data.high, low=self.data.low, close=self.data.close, window=14
        ).shift(1)
        self.data["atr_ma"] = self.data["atr"].rolling(14).mean().shift(1)
        self.lod = self.data.low[1]

    def plot_indicators(self):
        pass
        # go.Scatter(x=self.data.index, y=self.data.fast, name='fast', line=dict(color='red'))

    def notify_order(self, order: Order):
        return
        if order.status == OrderStatus.Executed:
            if order.side == Side.Sell:
                symbol = "🟢" if self.pnl > 0 else "🔴"
                self.log(
                    f" {symbol} Sold {int(order.size)}@{order.execprice:.2f} atr {self.bar.atr:.2f} P/L {self.pnl:.2f}"
                )
            else:
                self.log(
                    f"️🔷 Bought {int(order.size)}@{order.execprice:.2f} atr {self.bar.atr:.2f} P/L {self.pnl:.2f}"
                )
        elif order.exectype == OrderType.Stop and order.status == OrderStatus.Pending:
            self.log(
                f"️🔶 Stop {int(order.size)}@{order.price:.2f} atr {self.bar.atr:.2f} P/L {self.pnl:.2f}"
            )

    def next(self, x: int, bar):
        self.setLOD(bar)
        if not self.position:
            if self.order:
                # cancel order if not filled on next bar
                self.order = None

            """ENTRY"""
            isTime = bar.date.time() > pd.Timestamp("09:55").time()

            volumeUp = bar.volume > bar.vol_sma * self.volume_increase

            threshold = min(0.2, bar.low * 0.0005)
            isLOD = bar.low == self.lod or bar.low < self.lod + threshold

            middle = (bar.high - bar.low) / 2
            isDoji = bar.open > bar.low + middle and bar.close > bar.low + middle
            dojiPlacement = self.data.low[x - 1] > bar.low + middle

            highAtr = bar.atr > bar.atr_ma * self.atr_increase
            highAtr
            volumeUp
            if isTime and isLOD and isDoji and dojiPlacement:
                self.set_size_long(x, bar)
                self.send_long(x, bar)
                self.position_start = x
        elif self.position:
            """EXIT"""
            marketClose = bar.date.time() > pd.Timestamp("15:50").time()
            target2x = (
                bar.high - self.position.avgprice
            ) > self.long_points_risk * self.rr_factor
            if target2x:
                exit_price = self.position.avgprice + (
                    self.long_points_risk * self.rr_factor
                )
                self.send_order(
                    size=self.size,
                    side=Side.Sell,
                    exectype=OrderType.Limit,
                    price=exit_price,
                )
            elif marketClose:
                self.send_order(
                    size=self.size,
                    side=Side.Sell,
                    exectype=OrderType.Limit,
                    price=bar.close,
                )

    def send_long(self, x, bar):
        stop_price = self.bar_low_stop
        stop_loss = Order(
            exectype=OrderType.Stop, size=self.size, side=Side.Sell, price=stop_price
        )
        self.send_order(
            size=self.size,
            side=Side.Buy,
            exectype=OrderType.Stop,
            price=bar.high,
            oso=stop_loss,
            nextbar=True,
        )

    def setLOD(self, bar):
        if bar.date.time() == pd.Timestamp("09:30").time():
            self.lod = bar.low
        self.lod = min(bar.low, self.lod)

    def set_size_long(self, x, bar):
        self.bar_low_stop = bar.low
        self.long_points_risk = bar.high - self.bar_low_stop
        self.size = round(self.p["risk"] / self.long_points_risk, 0)
        self.size = self.size if self.size > 0 else 1
