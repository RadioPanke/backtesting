from model.BaseStrategy import BaseStrategy
from model.order import OrderType, Order, OrderStatus, Side
from ta.volatility import average_true_range
from ta.momentum import rsi
from ta.trend import sma_indicator

"""
"""


class TwoDayReversal(BaseStrategy):
    def conf(self):
        self.min_bars = 5

    def calculate_indicators(self):
        # Initialize ATR
        self.data['atr'] = average_true_range(high=self.data.high, low=self.data.low, close=self.data.close, window=5)
        self.data['rsi'] = rsi(close=self.data.close, window=2)
        self.data['sma'] = sma_indicator(close=self.data.close, window=200)

    def notify_order(self, order: Order):
        return
        if order.status == OrderStatus.Pending and order.exectype == OrderType.Stop:
            self.log(f'Stop buy @{order.price}')
        elif order.status == OrderStatus.Executed:
            if order.side == Side.Sell:
                self.log(f'🔷 Short {int(order.size)}@{order.execprice:.2f}')
            else:
                symbol = '🟢' if self.pnl > 0 else '🔴'
                self.log(f'️{symbol} Cover {int(order.size)}@{order.execprice:.2f} P/L {self.pnl:.2f}')

    def next(self, x: int, bar):
        # entry condition
        # trade_condition = self.twoDayRsiUnder10(x, bar)
        trade_condition = self.rsiUnder10(x, bar)
        if self.order:
            # it stop is not hit, replace it with new resistance
            self.send_order(size=self.size, exectype=OrderType.Limit, side=Side.Sell, price=bar.close)
        elif not self.position and trade_condition:
            self.size = round(self.p['risk'] / bar.atr, 0)
            # % risk
            self.size = self.size if self.size > 0 else 1
            s_price = bar.close - bar.atr
            stop_loss = Order(exectype=OrderType.Stop, size=self.size, side=Side.Sell, price=s_price)
            self.send_order(size=self.size, side=Side.Buy, exectype=OrderType.Limit, price=bar.close,
                            oso=stop_loss)

    def rsiUnder10(self, x, bar):
        if bar.close > bar.sma:
            return True if bar.rsi < 10 else False
        else:
            return False

    def twoDayRsiUnder10(self, x, bar):
        if bar.close > bar.sma:
            return True if self.data.rsi[x-1] < 10 and bar.rsi < 10 else False
        else:
            return False
