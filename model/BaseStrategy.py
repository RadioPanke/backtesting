from _datetime import datetime
from util import Utils
import plotly.graph_objects as go
import pandas as pd
import sys
import numpy as np

from model.order import OrderType, Order, OrderStatus, Side, TimeInForce

# remove pandas warnings
pd.options.mode.chained_assignment = None


class BaseStrategy:
    p = {'risk': 30}

    def __init__(self, start=None, end=None):
        self.data = None
        self.min_bars = 1
        self.start = start
        self.end = end
        self.bar = None
        self.index = None
        self.ticker = None
        self.next_price = False

        self.position = None
        self.size = None
        self.order = None

        self.cash = 0
        self.pnl = 0

        # plot variables
        self.traces = []
        self.traces_pnl = []
        self.traces_pnl_curve = []
        # stats
        self.stats = None

    def next(self, x: int, bar):
        """
        Will call this for every bar in the data
        :param x: index of current bar starting at 0
        :param bar: bar object with high, low etc...
        :return: None
        """
        pass

    def conf(self):
        """
        Pre conf before getting the data series, mainly for indicators setups
        :return: None
        """
        pass

    def calculate_indicators(self):
        pass

    def notify_order(self, order):
        pass

    def log(self, txt):
        print(f'{self.bar.date:%Y-%m-%d} --- {txt}')

    def feed(self, data: pd.DataFrame, ticker) -> None:
        """
        Dataframe columns [date, open, high, low, close]
        :param data: dataframe containing ticker info
        :return: None
        """
        # apply custom configs
        self.conf()

        if self.start and self.end:
            mask = (data['date'] >= self.start) & (data['date'] <= self.end)
            self.data = data.loc[mask]
        elif self.start:
            mask = data['date'] >= self.start
            self.data = data.loc[mask]
        elif self.end:
            mask = data['date'] <= self.end
            self.data = data.loc[mask]
        else:
            self.data = data
        if self.data.empty:
            print(f'############# Empty feed for {ticker} #############')
            return
        self.calculate_indicators()
        return 0

    def play(self):
        """
        Starts strategy execution
        :return: None
        """
        self.stats = Stats(type(self).__name__, self.ticker, self.cash, self.data)
        initial_index = None
        for index, bar in self.data.iterrows():
            if initial_index is None:
                initial_index = index
            if index >= initial_index + self.min_bars:
                self.bar = bar
                self.index = index
                self._evaluate()
                self.next(index, bar)
        self.stats.calculate_stats()
        return float(f'{self.stats.final_pnl:.2f}')

    def _evaluate(self):
        """
        Manages active orders and positions before updating to next bar
        :return: None
        """
        if self.order:
            if self.order.size <= 0:
                self.log(f'Wrong size {self.order.size} in {self.ticker}')
                sys.exit(1)
            if self.order.exectype == OrderType.Market:
                self._evaluate_market()
            elif self.order.exectype == OrderType.Limit:
                self._evaluate_limit()
            elif self.order.exectype == OrderType.Stop:
                self._evaluate_stop()

    def _evaluate_limit(self):
        # todo code when price is not within limits at the same day of execution and next days
        if self.bar.high >= self.order.price >= self.bar.low:
            self.order.status = OrderStatus.Executed
            self.order.execprice = self.order.price
            if not self.position:
                self.position = Position(size=self.order.size, avgprice=self.order.execprice, side=self.order.side)
                self._plot_tracer(self.order.side, size=self.order.size)
                self._add_stats(self.order.side)
            else:
                if self.position.side == self.order.side:
                    self.position.size = self.position.size + self.order.size
                    self.position.avgprice = np.mean([self.position.avgprice, self.order.execprice])
                    self._plot_tracer(self.order.side, size=self.order.size)
                    self._add_stats(self.order.side)
                elif self.order.size > self.position.size:
                    self.log(f'Order size {self.order.size} cannot be higher than positions size {self.position.size}')
                    sys.exit(1)
                else:
                    size = self.position.size - self.order.size
                    if size == 0:
                        self.pnl = (self.order.execprice - self.position.avgprice) \
                                   * self.position.size * self.position.side.value
                        self.cash = self.cash + self.pnl
                        self.position = None
                    else:
                        # todo calculate partial profits when position is not closed
                        self.position.size = size
                    self._plot_tracer(self.order.side, self.order.size, self.pnl)
                    self._add_stats(self.order.side, self.pnl, self.cash)
            self.notify_order(self.order)
            if self.order.oso is not None:
                order = self.order.oso
                self.send_order(order.exectype, order.size, order.side, order.price, nextbar=order.nextbar)
            else:
                self.order = None

    def _evaluate_market(self):
        self.order.status = OrderStatus.Executed
        self.order.execprice = self.bar.open
        if not self.position:
            self.position = Position(size=self.order.size, avgprice=self.order.execprice, side=self.order.side)
            self._plot_tracer(self.order.side, size=self.order.size)
            self._add_stats(self.order.side)
        else:
            if self.position.side == self.order.side:
                # todo calculate avg price after adding shares
                self.position.size = self.position.size + self.order.size
            elif self.position.size < self.order.size:
                self.log(f'Order size {self.order.size} cannot be higher than positions size {self.position.size}')
                sys.exit(1)
            else:
                size = self.position.size - self.order.size
                if size == 0:
                    self.pnl = (self.order.execprice - self.position.avgprice) \
                               * self.position.size * self.position.side.value
                    self.cash = self.cash + self.pnl
                    self.position = None
                else:
                    # todo calculate partial profits when position is not closed
                    self.position.size = size
                self._plot_tracer(self.order.side, self.order.size, self.pnl)
                self._add_stats(self.order.side, self.pnl, self.cash)
        self.notify_order(self.order)
        self.order = None

    def _evaluate_stop(self):
        if self.next_price:
            self.next_price = False
            return
        if self.order.side == Side.Buy:
            if self.bar.high >= self.order.price:
                if self.bar.open > self.order.price:
                    self.order.execprice = self.bar.open
                else:
                    self.order.execprice = self.order.price
                self.order.status = OrderStatus.Executed
                if not self.position:
                    self.position = Position(size=self.order.size, avgprice=self.order.execprice, side=self.order.side)
                    self._plot_tracer(self.order.side, self.order.size)
                    self._add_stats(self.order.side)
                else:
                    if self.position.side == self.order.side:
                        # todo calculate avg price after adding shares
                        self.position.size = self.position.size + self.order.size
                    elif self.order.size > self.position.size:
                        self.log(f'Order size {self.order.size} cannot be higher than positions size {self.position.size}')
                        sys.exit(1)
                    else:
                        size = self.position.size - self.order.size
                        if size == 0:
                            self.pnl = (self.order.execprice - self.position.avgprice) \
                                       * self.position.size * self.position.side.value
                            self.cash = self.cash + self.pnl
                            self.position = None
                        else:
                            # todo calculate partial profits when position is not closed
                            self.position.size = size
                        self._plot_tracer(self.order.side, self.order.size, self.pnl)
                        self._add_stats(self.order.side, self.pnl, self.cash)
                self.notify_order(self.order)
                if self.order.oso is not None:
                    order = self.order.oso
                    self.send_order(order.exectype, order.size, order.side, order.price)
                else:
                    self.order = None
        else:
            # sell branch
            if self.bar.low <= self.order.price:
                if self.bar.open < self.order.price:
                    self.order.execprice = self.bar.open
                else:
                    self.order.execprice = self.order.price
                self.order.status = OrderStatus.Executed
                if not self.position:
                    self.position = Position(size=self.order.size, avgprice=self.order.execprice, side=self.order.side)
                else:
                    if self.position.side == self.order.side:
                        # todo calculate avg price after adding shares
                        self.position.size = self.position.size + self.order.size
                    elif self.order.size > self.position.size:
                        self.log(f'Order size {self.order.size} cannot be higher than positions size {self.position.size}')
                        sys.exit(1)
                    else:
                        size = self.position.size - self.order.size
                        if size == 0:
                            self.pnl = (self.order.execprice - self.position.avgprice) \
                                       * self.position.size * self.position.side.value
                            self.cash = self.cash + self.pnl
                            self.position = None
                        else:
                            # todo calculate partial profits when position is not closed
                            self.position.size = size
                        self._plot_tracer(self.order.side, self.order.size, self.pnl)
                        self._add_stats(self.order.side, self.pnl, self.cash)
                self.notify_order(self.order)
                if self.order.oso is not None:
                    order = self.order.oso
                    self.send_order(order.exectype, order.size, order.side, order.price)
                else:
                    self.order = None

    def _add_stats(self, side, pnl=None, cash=None):
        self.stats.trade_sides.append(side)
        if pnl:
            self.stats.pnls.append(self.pnl)
        if cash:
            if cash > self.stats.max_equity:
                self.stats.max_equity = cash
            elif cash < self.stats.max_drawdown:
                self.stats.max_drawdown = cash

    def send_order(self, exectype=OrderType.Market, size=1, side=Side.Buy, price=None, tif=TimeInForce.GTC,  oso=None, nextbar=False):
        """
        Long / short
        :param side: buy / sell
        :param oso: order sends order
        :param exectype: Order [Market, Limit, Stop, StopLimit]
        :param size: number of shares
        :param tif: time in force
        :param price: stop or limit price
        :param nextbar: True = skip current bar
        :return: order
        """
        self.order = Order(exectype=exectype, size=size, tif=tif, side=side, price=price, oso=oso)
        self.notify_order(self.order)
        if nextbar:
            self.next_price = True
        self._evaluate()
        return self.order

    def print_stats(self):
        """
        Prints stats to console and to the stats folder
        """
        self.stats.to_string()
        # self.stats.calculate_stats()

    def _plot_tracer(self, side, size, realized=None):
        color = 'RoyalBlue' if side == Side.Buy else 'DarkOrchid'
        symbol = 'star-triangle-up' if side == Side.Buy else 'star-triangle-down'
        text = int(size)

        self.traces.append(dict(x0=self.bar.date, y=(self.data.high[self.index] + 5,), marker_symbol=symbol,
                                marker=dict(color=color, size=8.5), hoverinfo="text", mode="markers",
                                text=text,))
        if realized:
            pnl_color = 'green' if realized > 0 else 'crimson'
            self.traces.append(go.Scatter(x0=self.bar.date, y=(self.data.high[self.index] + 10,),
                                          marker=dict(color=pnl_color, size=8), hoverinfo="text", mode="markers",
                                          text=f'{realized:.2f}',))
            self.traces_pnl.append(go.Scatter(x0=self.bar.date, y=(realized,), marker=dict(color=pnl_color, size=15),
                                              hoverinfo="text", mode="markers", text=f'{realized:.2f}',))
            self.traces_pnl_curve.append(self.cash)

    def plot_results(self, pnltrace=True, indicatortrace=False):
        """
        Plots chart with trades made

        :param pnltrace: dots with P/L numbers
        :param indicatortrace: up and down arrows where trades were executed
        """
        candlestick = go.Candlestick(x=self.data.date, open=self.data.open, high=self.data.high,
                                     low=self.data.low, close=self.data.close)
        fig_chart = go.Figure(data=[candlestick])

        fig_chart.layout.xaxis.rangeslider.visible = False
        fig_chart.layout.xaxis.type = 'category'
        fig_chart.layout.xaxis.tickformat = '%Y - %m - %d'
        fig_chart.update_layout(title=f'{type(self).__name__} on {self.ticker}')

        if pnltrace:
            fig_chart.add_traces(self.traces)
        if indicatortrace:
            fig_chart.add_traces(self.plot_indicators())

        fig_chart.show()

    def plot_indicators(self):
        pass

    def plot_pnls(self):
        """
        External P/L green/red dot plot
        """
        fig_pnls = go.Figure(data=self.traces_pnl)
        fig_pnls.layout.xaxis.type = 'category'
        fig_pnls.update_layout(title=f'P/L {type(self).__name__} on {self.ticker}')

        fig_pnls.show()

    def plot_equity_curve(self):
        """
        Extra equity line chart
        """
        fig_curve = go.Figure()
        fig_curve.update_layout(title=f'Equity curve {type(self).__name__} on {self.ticker}')
        fig_curve.add_trace(go.Scatter(y=self.traces_pnl_curve, line=dict(color='DarkCyan', width=2.2),
                                       mode='lines+markers'))
        fig_curve.show()


class Position:
    def __init__(self, size, avgprice, side):
        self.size = size
        self.avgprice = avgprice
        self.side = side


class Stats:
    def __init__(self, strategy, ticker, cash, data):
        # filled
        self.strategy = strategy
        self.ticker = ticker
        self.data = data
        self.trade_sides = []
        self.pnls = []
        self.max_drawdown = cash
        self.max_equity = cash
        self.starting_equity = cash
        # empty
        self.final_pnl = 0
        self.max_loss = 0
        self.max_win = 0
        self.sell_trades = 0
        self.buy_trades = 0
        self.avg_win = 0
        self.avg_loss = 0
        self.median_win = 0
        self.median_loss = 0
        self.avg_win_loss_ratio = 0
        self.losses = []
        self.wins = []
        self.losing_streak = 0
        self.winning_streak = 0
        self.trading_days = 0
        self.trading_years = 0
        self.ending_equity = 0
        self.win_percentage = 0
        self.total_transactions = 0
        self.expectancy = 0
        self.profitability = 0

    def calculate_stats(self):
        self.max_loss = min(self.pnls) if len(self.pnls) > 0 else 0
        self.max_win = max(self.pnls) if len(self.pnls) > 0 else 0
        for side in self.trade_sides:
            if side == Side.Buy:
                self.buy_trades = self.buy_trades + 1
            elif side == Side.Sell:
                self.sell_trades = self.sell_trades + 1
        # losing and winning streaks
        win_streak = 0
        loss_streak = 0
        for pnl in self.pnls:
            if pnl > 0:
                win_streak = win_streak + 1
                if self.winning_streak < win_streak:
                    self.winning_streak = win_streak
                loss_streak = 0
            elif pnl < 0:
                loss_streak = loss_streak + 1
                if self.losing_streak < loss_streak:
                    self.losing_streak = loss_streak
                win_streak = 0
        self.wins = [win for win in self.pnls if win > 0]
        if len(self.wins) > 0:
            self.median_win = np.percentile(self.wins, 50)
        self.avg_win = np.mean(self.wins) if len(self.wins) > 0 else 0
        self.losses = [loss for loss in self.pnls if loss < 0]
        if len(self.losses) > 0:
            self.median_loss = np.percentile(self.losses, 50)
        self.avg_loss = np.mean(self.losses) if len(self.losses) > 0 else 0
        self.avg_win_loss_ratio = abs(round(self.avg_win / self.avg_loss, 1)) if self.avg_loss < 0 else 2
        self.win_percentage = len(self.wins) / (len(self.wins) + len(self.losses)) * 100 if len(self.wins) > 0 else 0
        self.expectancy = (self.avg_win * self.win_percentage / 100) - \
                            (- self.avg_loss * ((100 - self.win_percentage) / 100))
        self.expectancy = self.expectancy if not Utils.isBad(self.expectancy) else 0
        if len(self.wins) > 0 and len(self.losses) > 0:
            self.profitability = -(self.avg_win / self.avg_loss) * (self.win_percentage / (100 - self.win_percentage))
        days_number = self.data.close.size
        self.trading_days = days_number
        # trading_days = days - weekends  - holidays
        self.trading_years = f'{days_number / (365 - 104 - 10):.1f}'
        self.ending_equity = self.starting_equity + (sum(self.pnls))
        self.final_pnl = self.ending_equity - self.starting_equity
        self.total_transactions = self.sell_trades + self.buy_trades

    def to_string(self):
        """
        Prints stats to console and to the stats folder
        """
        print('''
        --- ‼️ Stats ‼️ ---
        ''')
        print(f'{self.ticker}')
        print(f'P/L:                {self.final_pnl:.2f}')
        print(f'Starting equity:    {self.starting_equity:.2f}')
        print(f'Ending equity:      {self.ending_equity:.2f}')
        print(f'Highest equity:     {self.max_equity:.2f}')
        print(f'Highest drawdown:   {self.max_drawdown:.2f}')
        print()
        print(f'Win %:              {self.win_percentage:.2f}')
        print(f'Profitability:      {self.profitability:.2f}')
        print(f'Expectancy:         {self.expectancy:.2f}')
        print(f'Number of wins:     {len(self.wins)}')
        print(f'Number of losses:   {len(self.losses)}')
        print(f'Max winning streak: {self.winning_streak}')
        print(f'Max losing streak:  {self.losing_streak}')
        print(f'Max win:            {self.max_win:.2f}')
        print(f'Max loss:           {self.max_loss:.2f}')
        print(f'Median win:         {self.median_win:.2f}')
        print(f'Median loss:        {self.median_loss:.2f}')
        print(f'Avg win:            {self.avg_win:.2f}')
        print(f'Avg loss:           {self.avg_loss:.2f}')
        print(f'Avg win/loss ratio: {self.avg_win_loss_ratio}')
        print()
        print(f'Trading days:       {self.trading_days}')
        print(f'Trading years:      {self.trading_years}')
        print(f'Total transactions: {self.total_transactions}')
        print(f'Number of Buys:     {self.buy_trades}')
        print(f'Number of Sells:    {self.sell_trades}')
        with open(f'stats/{self.strategy}__{self.ticker}', 'a+') as file:
            print('''
                    --- ‼️ Stats ‼️ ---
                    ''', file=file)
            print(f'{datetime.now().strftime("%H:%M:%S")} {self.ticker}', file=file)
            print(f'P/L:                {self.final_pnl:.2f}', file=file)
            print(f'Starting equity:    {self.starting_equity:.2f}', file=file)
            print(f'Ending equity:      {self.ending_equity:.2f}', file=file)
            print(f'Highest equity:     {self.max_equity:.2f}', file=file)
            print(f'Highest drawdown:   {self.max_drawdown:.2f}', file=file)
            print(file=file)

            print(f'Win %:              {self.win_percentage:.2f}', file=file)
            print(f'Profitability:      {self.profitability:.2f}', file=file)
            print(f'Expectancy:         {self.expectancy:.2f}', file=file)
            print(f'Number of wins:     {len(self.wins)}', file=file)
            print(f'Number of losses:   {len(self.losses)}', file=file)
            print(f'Max winning streak: {self.winning_streak}', file=file)
            print(f'Max losing streak:  {self.losing_streak}', file=file)
            print(f'Max win:            {self.max_win:.2f}', file=file)
            print(f'Max loss:           {self.max_loss:.2f}', file=file)
            print(f'Median win:         {self.median_win:.2f}', file=file)
            print(f'Median loss:        {self.median_loss:.2f}', file=file)
            print(f'Avg win:            {self.avg_win:.2f}', file=file)
            print(f'Avg loss:           {self.avg_loss:.2f}', file=file)
            print(f'Avg win/loss ratio: {self.avg_win_loss_ratio}', file=file)
            print(file=file)
            print(f'Trading days:       {self.trading_days}', file=file)
            print(f'Trading years:      {self.trading_years}', file=file)
            print(f'Total transactions: {self.total_transactions}', file=file)
            print(f'Number of Buys:     {self.buy_trades}', file=file)
            print(f'Number of Sells:    {self.sell_trades}', file=file)
            print('====================================================', file=file)
