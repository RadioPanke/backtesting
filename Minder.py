"""
Minder is the backtester

range: loc inclusive iloc exclusive
"""
__author__ = 'Diego Jimenez Casillas'
import concurrent, numpy as np, pandas as pd, math
import enum
from _datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from strategies.daily.EndOfMonthRally import EndOfMonthRally
from model.DataFeeder import DataFeeder
from model.DataFeeder import Source
from strategies.intraday.FiveMinsOpen import FiveMinsOpen
from util.conf import *


def print_global_stats(stats):
    final_pnl = sum([st.final_pnl for st in stats if not math.isnan(st.final_pnl)])
    expectancy = np.mean([st.expectancy for st in stats])
    wins = sum([len(st.wins) for st in stats])
    losses = sum([len(st.losses) for st in stats])
    win_perc = wins / (wins + losses) * 100 if wins > 0 else 0
    numberOfTrades = wins + losses
    all_wins = list()
    for st in stats:
        all_wins = all_wins + st.wins
    p20th_win = np.percentile(all_wins, 20) if len(all_wins) > 0 else 0
    p50th_win = np.percentile(all_wins, 50) if len(all_wins) > 0 else 0
    p75th_win = np.percentile(all_wins, 75) if len(all_wins) > 0 else 0
    p90th_win = np.percentile(all_wins, 90) if len(all_wins) > 0 else 0
    all_losses = list()
    for st in stats:
        all_losses = all_losses + st.losses
    avg_win = np.mean(all_wins)
    avg_loss = np.mean(all_losses)
    p20th_loss = np.percentile(all_losses, 20)
    p50th_loss = np.percentile(all_losses, 50)
    p75th_loss = np.percentile(all_losses, 75)
    avg_win_loss_ratio = np.mean([st.avg_win_loss_ratio for st in stats])
    max_win = max([st.max_win for st in stats])
    max_loss = min([st.max_loss for st in stats])
    if wins > 0 and losses > 0:
        profitability = -(avg_win / avg_loss) * (win_perc / (100 - win_perc))
    else:
        profitability = 0
    print()
    print(f'Final P/L:          {final_pnl:.2f}')
    print(f'Win %:              {win_perc:.2f}')
    print(f'Profitability:      {profitability:.2f}')
    print(f'Mean Expectancy:    {expectancy:.2f}')
    print(f'Trades:             {numberOfTrades}')
    print(f'Number of wins:     {wins}')
    print(f'Number of losses:   {losses}')
    print(f'Max win:            {max_win:.2f}')
    print(f'Max loss:           {max_loss:.2f}')
    print(f'Avg win:            {avg_win:.2f}')
    print(f'Avg loss:           {avg_loss:.2f}')
    print(f'Avg win/loss ratio: {avg_win_loss_ratio:.2f}')
    print(f'20th loss:          {p20th_loss:.2f}')
    print(f'50th loss:          {p50th_loss:.2f}')
    print(f'75th loss:          {p75th_loss:.2f}')
    print(f'20th win:           {p20th_win:.2f}')
    print(f'50th win:           {p50th_win:.2f}')
    print(f'75th win:           {p75th_win:.2f}')
    print(f'90th win:           {p90th_win:.2f}')


def pull_data(time_series, ticker):
    if time_series is TimeSeries.INTRADAY:
        time_series_path = 'data/intraday'
        ticker_file = Path(f'{time_series_path}/{ticker}.csv')
        if not ticker_file.exists():
            feeder = DataFeeder(ticker, Source.AlphaVantage)
            feeder.path = time_series_path
            feeder.pull_intraday_data()
    elif time_series is TimeSeries.DAILY:
        time_series_path = 'data/daily'
        ticker_file = Path(f'{time_series_path}/{ticker}.csv')
        if not ticker_file.exists():
            feeder = DataFeeder(ticker, Source.AlphaVantage)
            feeder.path = time_series_path
            feeder.pull_daily_data()
    elif time_series is TimeSeries.WEEKLY:
        time_series_path = 'data/weekly'
        ticker_file = Path(f'{time_series_path}/{ticker}.csv')
        if not ticker_file.exists():
            feeder = DataFeeder(ticker, Source.AlphaVantage)
            feeder.path = time_series_path
            feeder.pull_weekly_data()

    return pd.read_csv(ticker_file, parse_dates=['date'])


def replay(ticker):
    start = datetime(2022, 2, 1)
    end = datetime(2022, 3, 1)
    strategy = FiveMinsOpen(start=None, end=None)

    data = pull_data(TimeSeries.INTRADAY, ticker)

    if strategy.feed(data, ticker) is None:
        return None
    strategy.ticker = ticker
    strategy.p['risk'] = 50
    strategy.cash = 10000

    # pnl = strategy.play()
    strategy.play()
    """###PRINT RESULTS###"""
    # strategy.print_stats()
    strategy.plot_results(pnltrace=True, indicatortrace=False)
    # strategy.plot_pnls()
    # strategy.plot_equity_curve()
    return strategy.stats


def main():
    """Set the stage"""
    # tickers = stocks + etfs
    # tickers = ['AMZN', 'IBM', 'TSLA', 'ALLY', 'AMAT', 'SPY', 'QQQ']
    tickers = ['SPY']
    # tickers = etfs20
    # tickers = etfs
    print('Started')
    start = datetime.now()
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(replay, t) for t in tickers]
    stats = [fut.result() for fut in concurrent.futures.as_completed(futures) if fut.result() is not None]
    print_global_stats(stats)
    print(f'\nRan for {round((datetime.now() - start).total_seconds(), 0):.0f} seconds')


if __name__ == '__main__':
    main()


class TimeSeries(enum.Enum):
    DAILY = 1
    WEEKLY = 2
    INTRADAY = 3

# TODO get weekly strat for crossover with MAs