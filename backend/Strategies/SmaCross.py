import backtrader as bt


class SmaCross(bt.Strategy):
    params = (
        ('fast', 10),
        ('slow', 25),
    )

    def __init__ (self):
        #crossover is custom indicator
        self.crossover = bt.indicators.CrossOver(
            #from hover over the function
            # This indicator gives a signal if the provided datas (2) cross up or down.
            #     1.0 if the 1st data crosses the 2nd data upwards
            #    -1.0 if the 1st data crosses the 2nd data downwards
                   

            bt.indicators.SimpleMovingAverage(self.data.close, period = self.params.fast),
            bt.indicators.SimpleMovingAverage(self.data.close, period = self.params.slow)
        )

    def next(self):
        if (self.position == 0) and (self.crossover > 0):
            self.buy()
        elif(self.position > 0) and (self.crossover < 0):
            self.close()