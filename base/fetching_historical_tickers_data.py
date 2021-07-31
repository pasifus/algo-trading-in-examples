import yfinance as yf

# fetching data for ticker: SPY
data = yf.download("SPY", interval = "1d", start="2000-01-01", end="2021-01-01")
# save to csvx
data.to_csv("spy.csv")
# print
print(data)

# fetching data for multiple tickers: AAPL, GOOG, MSFT
data = yf.download("AAPL, GOOG, MSFT", interval = "1d", start="2000-01-01", end="2021-01-01")
# save to csv
data.to_csv("aapl_goog_msft.csv")
# print
print(data)
