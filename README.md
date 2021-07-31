# Algorithm Trading In Examples

Repository include simple examples of algorithm trading in python.

## Base
Simple all kind of examples

- base/fetching_historical_tickers_data.py - get stock historic data.

## Backtest
Backtest - is general method for seeing how well a strategy or model would have done ex-post.

- backtest/backtest-gc-spy.py - strategy based on: [The Golden Cross (50 SMA crossing 200 SMA)](https://www.investopedia.com/terms/g/goldencross.asp)
- backtest/backtest-ema_sma-spy.py - strategy based on: 20 EMA crossing 50 SMA
- backtest/backtest-ma-spy.py - strategy based on: [Moving Average Trading Strategy That Crushes Buy and Hold](https://www.newtraderu.com/2019/10/05/moving-average-trading-strategy-that-crushes-buy-and-hold/)

### How to run?
Before start, you should install python and [python package manager](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/). The Best way to run examples is to using [python virtual environment](https://docs.python.org/3/library/venv.html)
```py
# create venv. if virtualenv not install then install it using: pip install
python3 -m venv env
# activate you env session
source env/bin/activate
# go to folder with include requirements.txt
cd backtest
# install dependencies
pip install -r requirements.txt
```