import yfinance as yf

from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import ma

from pyalgotrade import plotter

from pyalgotrade.stratanalyzer import returns, sharpe, drawdown, trades

import pandas
import pandas_market_calendars as market_calendars

stock = "NYSE"
ticker = "SPY"
start_date = "2000-01-01"
end_date = "2021-01-01"
my_balance = 1000


def get_last_days_of_month(start_date, end_date):
    df = market_calendars.get_calendar(stock).schedule(start_date=start_date, end_date=end_date)
    df = df.groupby(df.index.strftime('%Y-%m')).tail(1)
    df['date'] = pandas.to_datetime(df["market_open"]).dt.date
    return [date.isoformat() for date in df['date'].tolist()]


def print_analyzers_stats(strategy, retAnalyzer, sharpeRatioAnalyzer, drawDownAnalyzer, tradesAnalyzer):
    print("Final portfolio value: $%.2f" % strategy.getResult())
    print("Cumulative returns: %.2f %%" % (retAnalyzer.getCumulativeReturns()[-1] * 100))
    print("Sharpe ratio: %.2f" % (sharpeRatioAnalyzer.getSharpeRatio(0.05)))
    print("Max. drawdown: %.2f %%" % (drawDownAnalyzer.getMaxDrawDown() * 100))
    print("Longest drawdown duration: %s" % (drawDownAnalyzer.getLongestDrawDownDuration()))

    print("")
    print("Total trades: %d" % (tradesAnalyzer.getCount()))
    if tradesAnalyzer.getCount() > 0:
        profits = tradesAnalyzer.getAll()
        print("Avg. profit: $%2.f" % (profits.mean()))
        print("Profits std. dev.: $%2.f" % (profits.std()))
        print("Max. profit: $%2.f" % (profits.max()))
        print("Min. profit: $%2.f" % (profits.min()))
        returns = tradesAnalyzer.getAllReturns()
        print("Avg. return: %2.f %%" % (returns.mean() * 100))
        print("Returns std. dev.: %2.f %%" % (returns.std() * 100))
        print("Max. return: %2.f %%" % (returns.max() * 100))
        print("Min. return: %2.f %%" % (returns.min() * 100))

    print("")
    print("Profitable trades: %d" % (tradesAnalyzer.getProfitableCount()))
    if tradesAnalyzer.getProfitableCount() > 0:
        profits = tradesAnalyzer.getProfits()
        print("Avg. profit: $%2.f" % (profits.mean()))
        print("Profits std. dev.: $%2.f" % (profits.std()))
        print("Max. profit: $%2.f" % (profits.max()))
        print("Min. profit: $%2.f" % (profits.min()))
        returns = tradesAnalyzer.getPositiveReturns()
        print("Avg. return: %2.f %%" % (returns.mean() * 100))
        print("Returns std. dev.: %2.f %%" % (returns.std() * 100))
        print("Max. return: %2.f %%" % (returns.max() * 100))
        print("Min. return: %2.f %%" % (returns.min() * 100))

    print("")
    print("Unprofitable trades: %d" % (tradesAnalyzer.getUnprofitableCount()))
    if tradesAnalyzer.getUnprofitableCount() > 0:
        losses = tradesAnalyzer.getLosses()
        print("Avg. loss: $%2.f" % (losses.mean()))
        print("Losses std. dev.: $%2.f" % (losses.std()))
        print("Max. loss: $%2.f" % (losses.min()))
        print("Min. loss: $%2.f" % (losses.max()))
        returns = tradesAnalyzer.getNegativeReturns()
        print("Avg. return: %2.f %%" % (returns.mean() * 100))
        print("Returns std. dev.: %2.f %%" % (returns.std() * 100))
        print("Max. return: %2.f %%" % (returns.max() * 100))
        print("Min. return: %2.f %%" % (returns.min() * 100))


class MovingAverageStrategy(strategy.BacktestingStrategy):
    """Strategy: https://www.newtraderu.com/2019/10/05/moving-average-trading-strategy-that-crushes-buy-and-hold/
    buy: closing price at the end ot the month less then MovingAverage(200).
    sell: closing price cross more then MovingAverage(200).
    """
    def __init__(self, feed, instrument):
        super(MovingAverageStrategy, self).__init__(feed)
        self.position = None
        self.instrument = instrument
        self.sma200 = ma.SMA(feed[instrument].getAdjCloseDataSeries(), 200)
        self.setUseAdjustedValues(True)  # https://www.investopedia.com/terms/a/adjusted_closing_price.asp
        self.getBroker().setCash(1000)  # set balance cash
        self.last_days_of_month = get_last_days_of_month(start_date, end_date)

    def onEnterOk(self, position):
        exec_info = position.getEntryOrder().getExecutionInfo()
        self.info(f"======== BUY AT {exec_info.getPrice()}")

    def onExitOk(self, position):
        exec_info = position.getEntryOrder().getExecutionInfo()
        self.info(f"======== SELL AT {exec_info.getPrice()}")

    def onBars(self, bars):
        # waiting for value
        if self.sma200[-1] is None:
            return

        bar = bars[self.instrument]
        date = bar.getDateTime().date().isoformat()
        close = bar.getAdjClose()
        if date in self.last_days_of_month:
            if self.position is None:
                broker = self.getBroker()
                cash = broker.getCash() * .95  # price in next day can be different
                if close > self.sma200[-1]:
                    quantity = cash / close
                    self.info(f"buying witch is sma200({self.sma200[-1]}) above close price {close}")
                    self.position = self.enterLong(self.instrument, quantity)
            elif close < self.sma200[-1]:
                self.info(f"selling witch is {close} above close price sma200({self.sma200[-1]})")
                self.position.exitMarket()
                self.position = None


if __name__ == '__main__':
    file_name = ticker + "_" + start_date + "-" + end_date + ".csv"

    # save file_name to csv
    data = yf.download(ticker, start=start_date, end=end_date)
    data.to_csv(file_name)

    # load file_name to feed
    feed = yahoofeed.Feed()
    feed.addBarsFromCSV(ticker, file_name)

    # create strategy
    strategy = MovingAverageStrategy(feed, ticker)

    # create analyzers
    returnsAnalyzer = returns.Returns()
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    drawDownAnalyzer = drawdown.DrawDown()
    tradesAnalyzer = trades.Trades()

    # add analyzers to strategy
    strategy.attachAnalyzer(returnsAnalyzer)
    strategy.attachAnalyzer(sharpeRatioAnalyzer)
    strategy.attachAnalyzer(drawDownAnalyzer)
    strategy.attachAnalyzer(tradesAnalyzer)

    # add plots
    plt = plotter.StrategyPlotter(strategy)
    plt.getInstrumentSubplot(ticker).addDataSeries("SMA(200)", strategy.sma200)

    # run strategy
    strategy.run()

    # show strategy statistics
    print_analyzers_stats(strategy, returnsAnalyzer, sharpeRatioAnalyzer, drawDownAnalyzer, tradesAnalyzer)

    # show graph
    plt.plot()