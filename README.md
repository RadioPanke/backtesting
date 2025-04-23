# backtesting

- pulls data based on weekly/daily/intraday
- Easy plug and play strategies to test ideas
- Compares PnL to a buy andhold approach to SPY for the same period
- Saves outpouts for each ticker or only the aggregate of a particular strategy with all the tickers included
- It can plot chart with trades and PnL / equity curve trade by trade / point chart to visualize PnL of all trades and find outliers
- Many stats like profitability, expectancy, win/loss ratio, median win/loss and more


Main class is Minder.py

It can save outputs for specific tickers or global, plot trades in the ticker chart etc...
Strategies are easily pluged in

Eaxmple output
```
Started

Final P/L:          19796.83
SPY comparison      148.04
Win %:              27.91
Profitability:      1.42
Mean Expectancy:    15.82
Trades:             1419
Number of wins:     396
Number of losses:   1023
Max win:            1260.93
Max loss:           -293.00
Avg win:            168.13
Avg loss:           -45.73
Avg win/loss ratio: 4.00
20th loss:          -51.30
50th loss:          -49.93
75th loss:          -40.68
20th win:           33.84
50th win:           88.13
75th win:           223.36
90th win:           413.83

Ran for 1 seconds
```