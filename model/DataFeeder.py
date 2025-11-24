import enum
import time

import sys

import yfinance as yf
from io import StringIO
import requests
import pandas as pd
import numpy as np
from util.conf import *


class DataFeeder:
    path = 'data'

    def __init__(self, ticker, source):
        self.ticker = ticker
        self.source = source

    def pull_daily_data(self):
        print(f'Pulling daily {self.ticker} data from {self.source.name}')
        if self.source is Source.AlphaVantage:
            self._pull_AlphaVantage()
        if self.source is Source.YFinance:
            self._pull_yfinance()

    def pull_intraday_data(self, timeframe):
        print(f'Pulling {timeframe} intraday {self.ticker} data from {self.source.name}')
        if self.source is Source.AlphaVantage:
            self._pull_intraday_AlphaVantage(timeframe)

    def pull_weekly_data(self):
        print(f'Pulling weekly {self.ticker} data from {self.source.name}')
        if self.source is Source.AlphaVantage:
            self._pull_weekly_AlphaVantage()

    def _pull_yfinance(self):
        data = yf.download(period="max", tickers=self.ticker, interval="1d")
        data.columns = map(str.lower, data.columns)
        data.to_csv(f'{self.path}/{self.ticker}.csv')

    def _pull_AlphaVantage(self):
        params = dict(
            function='TIME_SERIES_DAILY_ADJUSTED',
            symbol=self.ticker,
            apikey=ALPHA_VANTAGE_API_KEY,
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

    def _pull_intraday_AlphaVantage(self, timeframe):
        data = None
        today = pd.to_datetime("today")
        if timeframe == "3min":
            timeframe = "1min"
        for i in range(1,5):
            target_date = today - pd.DateOffset(months=i)
            month_str = target_date.strftime('%Y-%m')
            params = dict(
                function="TIME_SERIES_INTRADAY",
                extended_hours="false",
                symbol=self.ticker,
                apikey=ALPHA_VANTAGE_API_KEY,
                adjusted="true",
                interval=timeframe,
                outputsize="full",
                month=month_str,
                datatype="csv"
            )
            res = None
            try:
                res = requests.get(f'https://www.alphavantage.co/query', params=params)
                if res.status_code != 200:
                    print(f'Bad status code: {res.status_code}\n {res.text}')
                    sys.exit()
                temp = pd.read_csv(StringIO(res.text), parse_dates=['timestamp'])
                temp = temp.rename(columns={'timestamp': 'date'})
            except Exception as e:
                print(f"ERROR: {e}")
                print(f'There was a problem with the REST call \n{res.text}')
            if data is None:
                data = temp
            else:
                data = pd.concat([data, temp], ignore_index=True)
            time.sleep(1)
        data.sort_values(by=['date'], inplace=True, ascending=True)
        # data = data.iloc[::-1]
        if timeframe == "1min":
            # save for later 3min
            data1min = data.copy()
        data.reset_index(inplace=True, drop=True)
        data.to_csv(f'{self.path}/{self.ticker}.csv', index=None)

        if timeframe == "1min":
            print("Transforming to 3 min bars")
            time_series_path = "data/intraday3min"
            data1min["date"] = pd.to_datetime(
                data1min["date"],
                errors="coerce",
                utc=False
            )
            data1min = data1min.set_index("date")
            data3min = data1min.resample("3Min").agg(
                {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
            )
            data3min = data3min.dropna()
            data3min = data3min.reset_index()
            data3min.to_csv(f'{time_series_path}/{self.ticker}.csv', index=False)

    def _pull_weekly_AlphaVantage(self):
        params = dict(
            function='TIME_SERIES_WEEKLY_ADJUSTED',
            symbol=self.ticker,
            apikey=ALPHA_VANTAGE_API_KEY,
            datatype='csv'
        )
        try:
            res = requests.get(f'https://www.alphavantage.co/query', params=params)
            if res.status_code != 200:
                print(f'Bad status code: {res.status_code}\n {res.text}')
                sys.exit()
            data = pd.read_csv(StringIO(res.text), parse_dates=['timestamp'])
            data = data.rename(columns={'timestamp': 'date'})
        except Exception as ex:
            print(f'There was a problem with the REST call\n {ex}\n response: {res.text}')

        data.sort_values(by=['date'], inplace=True, ascending=True)
        data.to_csv(f'{self.path}/{self.ticker}.csv', index=None)


class Source(enum.Enum):
    YFinance = 0
    AlphaVantage = 1
