from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.trend import sma_indicator

"""
Buys on close sells on next open
"""


class BuyCloseSellOpenETF(BaseStrategy):
    def conf(self):
        self.min_bars = 200

    def calculate_indicators(self):
        # Initialize ATR
        self.data['atr'] = average_true_range(high=self.data.high, low=self.data.low, close=self.data.close, window=14)
        self.data['sma'] = sma_indicator(close=self.data.close, window=200)

    def notify_order(self, order: Order):
        if order.status == OrderStatus.Executed:
            if order.side == Side.Sell:
                symbol = '🟢' if self.pnl > 0 else '🔴'
                # self.log(f' {symbol} Sold {int(order.size)}@{order.execprice:.2f} P/L {self.pnl:.2f}')
            else:
                # self.log(f'️🔷 Long {int(order.size)}@{order.execprice:.2f}')
                pass

    def next(self, x: int, bar):
        if not self.position:
            self.size = round(self.p['risk'] / bar.atr, 0)
            self.buy(exectype=OrderType.Limit, size=self.size, price=bar.close)
        else:
            self.sell(exectype=OrderType.Market, size=self.size)
