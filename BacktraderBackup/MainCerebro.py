import datetime, quantstats
import backtrader as bt
import yfinance as yf
from pathlib import Path
from strategies import VXXScalper

"""
Set the stage and pull the data
"""
ticker = 'VXX'
strategy = VXXScalper.VXXScalper
start = [2018, 10, 1]
end = [2019, 12, 1]
cerebro = bt.Cerebro(cheat_on_open=True)

ticker_file = Path(f'resources/{ticker}.csv')
if not ticker_file.exists():
    print(f'Pulling {ticker} data')
    # history = spy.history(interval='1d', start='2000-01-01', end='2020-12-15')
    history = yf.download(period="max", tickers=ticker, interval="1d")
    history.to_csv(f'resources/{ticker}.csv')

# Create the Data Feed
data = bt.feeds.YahooFinanceCSVData(
    dataname=f'resources/{ticker}.csv',
    # Do not pass values before this date
    fromdate=datetime.datetime(start[0], start[1], start[2]),
    # Do not pass values after this date
    todate=datetime.datetime(end[0], end[1], end[2]),
    reverse=False)

cerebro.adddata(data)
cerebro.addstrategy(strategy)
cerebro.broker.set_cash(30000)
# Set the commission - 0.1% (0.001)... divide by 100 to remove the %
cerebro.broker.setcommission(commission=0)
# Add a FixedSize sizer according to the stake
# cerebro.addsizer(bt.sizers.FixedSize, stake=10)
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='PyFolio')

print(f'Starting equity {cerebro.broker.get_value():.2f}')
results = cerebro.run()
print(f'Ending equity {cerebro.broker.get_value():.2f}')
# generate stats
strat = results[0]
portfolio_stats = strat.analyzers.getbyname('PyFolio')
returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
returns.index = returns.index.tz_convert(None)
quantstats.reports.html(returns, output=f'stats/{strategy.__name__}_{ticker}Stats.html',
                        title=f'{strategy.__name__} on {ticker}')

# 'bar' / 'candle' / 'line'
cerebro.plot(style='candle')
cerebro.plot()
