"""
Author: Rosenyoung

This is a backtesting sample of moving average strategy

Version 1.0 2022-05-02

"""

import pandas as pd
import backtrader as bt
import time

from DataBaseConn import DataBaseConn


class SmaStrategy(bt.Strategy):
    # params = (('short_window',10),('long_window',60))
    params = {"short_window": 10, "long_window": 60}

    def log(self, txt, dt=None):
        # Log the backtesting information
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Calculate the indicator
        self.short_ma = bt.indicators.SMA(self.datas[0].close, period=self.p.short_window)
        self.long_ma = bt.indicators.SMA(self.datas[0].close, period=self.p.long_window)

    def next(self):
        """
        Set the main strategy here. If MA10 < MA60 at previous bar and MA10 > MA60 at current bar, close the short
        position and create a long position.
        If MA10 > MA60 at previous bar and MA10 < MA60 at current bar, close the long position and create a short
        position.
        """
        size = self.getposition(self.datas[0]).size

        if size == 0 and self.short_ma[-1] < self.long_ma[-1] and self.short_ma[0] > self.long_ma[0]:
            # Create a long positon
            self.buy(size = 50000)
        if size > 0 and self.short_ma[-1] > self.long_ma[-1] and self.short_ma[0] < self.long_ma[0]:
            # Close the long position
            self.close(self.datas[0])
            # Create a short position
            self.sell(size=50000)

        if size == 0 and self.short_ma[-1] > self.long_ma[-1] and self.short_ma[0] < self.long_ma[0]:
            # Create a short position
            self.sell(size = 50000)
        if size < 0 and self.short_ma[-1] < self.long_ma[-1] and self.short_ma[0] > self.long_ma[0]:
            # Close the short position
            self.close(self.datas[0])
            # Create a long position
            self.buy(size=50000)

    # Notify the status of orders. In backtesting generally all orders can be filled.
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Rejected:
            self.log(f"order is rejected : order_ref:{order.ref}  order_info:{order.info}")
        if order.status == order.Margin:
            self.log(f"order need more margin : order_ref:{order.ref}  order_info:{order.info}")
        if order.status == order.Cancelled:
            self.log(f"order is concelled : order_ref:{order.ref}  order_info:{order.info}")
        if order.status == order.Partial:
            self.log(f"order is partial : order_ref:{order.ref}  order_info:{order.info}")
        # Check if an order has been completed
        # Attention: broker could reject order if not enougth cash
        if order.status == order.Completed:
            if order.isbuy():
                self.log("buy result : buy_price : {} , buy_cost : {} , commission : {}".format(
                    order.executed.price, order.executed.value, order.executed.comm))

            else:  # Sell
                self.log("sell result : sell_price : {} , sell_cost : {} , commission : {}".format(
                    order.executed.price, order.executed.value, order.executed.comm))

    # Notify the information of each trade
    def notify_trade(self, trade):
        if trade.isclosed:
            self.log('closed symbol is : {} , total_profit : {} , net_profit : {}'.format(
                trade.getdataname(), trade.pnl, trade.pnlcomm))
        if trade.isopen:
            self.log('open symbol is : {} , price : {} '.format(
                trade.getdataname(), trade.price))



if __name__ == '__main__':
    # Create a cerebro object, which is the core of backtrader
    cerebro = bt.Cerebro()
    # Add the strategy
    cerebro.addstrategy(SmaStrategy)
    # Params for data feeding
    params = dict(
        # fromdate=datetime.datetime(2006, 10, 27),
        # todate=datetime.datetime(2020, 8, 14),
        timeframe=bt.TimeFrame.Seconds,
        compression=1,
        dtformat=('%Y-%m-%d'),
        tmformat=('%H:%M:%S'),
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=-1,
        openinterest=-1)

    # Transform the timestamp into datetime
    def stamp2time(timestamp):

        time_local = time.localtime(timestamp)

        dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)

        return dt
    # Acquire data from database
    data_conn = DataBaseConn()
    df = data_conn.read_historical_data(86400, 'EUR')
    data_conn.close_conn()
    # Transform the timestamp into datetime
    df['DateTime'] = df['DateTime'].apply(stamp2time)
    # Data processing
    df = df[['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Average']]
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest']
    df = df.sort_values("datetime")
    df.index = pd.to_datetime(df['datetime'])
    df = df[['open', 'high', 'low', 'close', 'volume', 'openinterest']]
    # Feed the data
    feed = bt.feeds.PandasDirectData(dataname=df, **params)
    cerebro.adddata(feed, name="EUR")
    # Set commission.
    cerebro.broker.setcommission(commission=0.00002)
    # Set the fund size
    cerebro.broker.setcash(100000.0)

    cerebro.run()

    # Plot the results
    cerebro.plot(volume = False)