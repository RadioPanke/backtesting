import enum
import yfinance as yf
from util.conf import *
from io import StringIO
import requests
import pandas as pd
import numpy as np


class DataFeeder:
    path = 'data'

    def __init__(self, ticker, source):
        self.ticker = ticker
        self.source = source

    def pull_data(self):
        print(f'Pulling {self.ticker} data from {self.source.name}')
        if self.source is Source.AlphaVantage:
            self._pull_AlphaVantage()
        if self.source is Source.YFinance:
            self._pull_yfinance()

    def _pull_yfinance(self):
        data = yf.download(period="max", tickers=self.ticker, interval="1d")
        data.columns = map(str.lower, data.columns)
        data.to_csv(f'{self.path}/{self.ticker}.csv')

    def _pull_AlphaVantage(self):
        params = dict(
            function='TIME_SERIES_DAILY_ADJUSTED',
            symbol=self.ticker,
            apikey={ALPHA_VANTAGE_API_KEY},
            outputsize='full',
            datatype='csv'
        )
        res = requests.get(f'https://www.alphavantage.co/query', params=params)
        data = pd.read_csv(StringIO(res.text), parse_dates=['timestamp'])
        data = data.rename(columns={'timestamp': 'date'})

        multiplier = 1
        for index, bar in data.iterrows():
            if bar.split_coefficient != 1:
                data.loc[index, 'open'] = bar.open * (1 / multiplier)
                data.loc[index, 'high'] = bar.high * (1 / multiplier)
                data.loc[index, 'low'] = bar.low * (1 / multiplier)
                data.loc[index, 'close'] = bar.close * (1 / multiplier)
                multiplier = multiplier * bar.split_coefficient
                continue
            data.loc[index, 'open'] = bar.open * (1 / multiplier)
            data.loc[index, 'high'] = bar.high * (1 / multiplier)
            data.loc[index, 'low'] = bar.low * (1 / multiplier)
            data.loc[index, 'close'] = bar.close * (1 / multiplier)

        data.sort_values(by=['date'], inplace=True, ascending=True)
        data.to_csv(f'{self.path}/{self.ticker}.csv', index=None)


class Source(enum.Enum):
    YFinance = 0
    AlphaVantage = 1
