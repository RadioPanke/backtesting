import yfinance as yf
import matplotlib.pyplot as plt

spy = yf.Ticker("VXX")


# history = spy.history(period="max")
history = yf.download(period="max", tickers="VXX")

print(history.to_csv())
print('plotting')
history['Close'].plot(title="VXX's stock close")
plt.show()
