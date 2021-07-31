import yfinance as yf

from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import ma

from pyalgotrade import plotter

from pyalgotrade.stratanalyzer import returns, sharpe, drawdown, trades

stock = "NYSE"
ticker = "SPY"
start_date = "2000-01-01"
end_date = "2021-01-01"
my_balance = 1000


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


class MovingAverageCrossStrategy(strategy.BacktestingStrategy):
    """Strategy: 20 EMA crossing 50 SMA
    buy: SimpleMovingAverage(20) cross over ExponentialMovingAverage(50).
    sell: ExponentialMovingAverage(50) cross over SimpleMovingAverage(20).
    """
    def __init__(self, feed, instrument):
        super(MovingAverageCrossStrategy, self).__init__(feed)
        self.position = None
        self.instrument = instrument
        self.sma20 = ma.SMA(feed[instrument].getAdjCloseDataSeries(), 20)
        self.ema50 = ma.EMA(feed[instrument].getAdjCloseDataSeries(), 50)
        self.setUseAdjustedValues(True)  # https://www.investopedia.com/terms/a/adjusted_closing_price.asp
        self.getBroker().setCash(my_balance)  # set balance cash

    def onEnterOk(self, position):
        exec_info = position.getEntryOrder().getExecutionInfo()
        self.info(f"===> BUY AT {exec_info.getPrice()} <===")

    def onExitOk(self, position):
        exec_info = position.getEntryOrder().getExecutionInfo()
        self.info(f"===> SELL AT {exec_info.getPrice()} <===")

    def onBars(self, bars):
        # waiting for value
        if self.sma20[-1] is None or self.ema50[-1] is None:
            return

        bar = bars[self.instrument]

        if self.position is None:
            if self.sma20[-1] > self.ema50[-1]:
                broker = self.getBroker()
                cash = broker.getCash() * .95  # price in next day can be different
                close = bar.getAdjClose()
                quantity = cash / close
                self.info(f"buying witch is sma20({self.sma20[-1]}) cross over ema50({self.ema50[-1]})")
                self.position = self.enterLong(self.instrument, quantity)
        elif self.ema50[-1] > self.sma20[-1]:
            self.info(f"selling witch is ema50({self.ema50[-1]}) cross over sma20({self.sma20[-1]})")
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
    strategy = MovingAverageCrossStrategy(feed, ticker)

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
    plt.getInstrumentSubplot(ticker).addDataSeries("SMA(20)", strategy.sma20)
    plt.getInstrumentSubplot(ticker).addDataSeries("EMA(50)", strategy.ema50)

    # run strategy
    strategy.run()

    # show strategy statistics
    print_analyzers_stats(strategy, returnsAnalyzer, sharpeRatioAnalyzer, drawDownAnalyzer, tradesAnalyzer)

    # show graph
    plt.plot()