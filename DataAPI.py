"""

Author: Ruosen Yang
This API class inherit the Wrapper and Client class, and overrides the methods of EWrapper. This API overrides
the function of EWrapper, translate the data requested into dataframe and store the data into mysql database.

Version 1.0 2022-03-17
This API is designed for 5 seconds bar data only.

"""

from ibapi import wrapper
from ibapi.client import EClient

import pandas as pd
import numpy as np

from ibapi.common import BarData
from ibapi.contract import Contract

import threading
import time
import datetime
from sqlalchemy import create_engine
import pymysql
import pytz


# Acquire different types of data and save data to database
class DataAPI(wrapper.EWrapper, EClient):

    def __init__(self, symbol, contract_type):
        """
        symbol: str - The contract symbol, such as 'EUR', 'AAPL'
        contrancttype: str - 'FX' or 'STK'
        duration: int - the period of historical data. If the duration is 3600 seconds, then when requesting
        historical data, the data of the last 1 hour will be acquired.Normally, duration should be the time
        interval between the last time of data in database and
        current time.
        """
        wrapper.EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.reqID = None

        self.data = []  # store data temporary
        self.symbol = symbol
        self.contract_type = contract_type

        self.max_duration = 86400  # historical data before 24 hours is not available
        self.__duration = 5

        # use latest time of already stored data to avoid data overlapping
        self.latest_time = int(time.time()) - self.max_duration

        # Check contract type
        if self.contract_type == 'STK':
            self.contract = self.stock_contract(symbol)
        elif self.contract_type == 'FX':
            self.contract = self.fx_contract(symbol)
        else:
            print(" Not a supported symbol")

        # Create a list to store data temporary
        self.data = []

        # Create a dataframe to append realtime value.
        self.dataframe = pd.DataFrame(['Contract', 'DateTime', 'Open', 'High', 'Low',
                                       'Close', 'Volume', 'Average', 'Count'])

        # Database connection setting
        self.__database_username = 'root'
        self.__database_password = 'yang930805'
        self.__database_ip = 'localhost'
        self.__database_port = 3306
        self.__database_name = 'ibapi'
        self.engine = create_engine('mysql+pymysql://{0}:{1}@{2}/{3}'.
                                    format(self.__database_username, self.__database_password,
                                           self.__database_ip, self.__database_name))

        # Check whetehr historical data has been saved
        self.__historical_flag = False

        # Creating  a random number as clientId
        CId = np.random.randint(100)

        print('DataAPI Connecintg...')
        # connect to the IB TWS
        self.connect('127.0.0.1', 7497, clientId=CId)

        """
        Request frozen market data in case live is not available.
        Different market data subscriptions give you access to different information
        https://interactivebrokers.github.io/tws-api/market_data_type.html#gsc.tab=0
        Type of data, type 2 returns the last snapshot if market is not open
        """
        self.reqMarketDataType(4)

        # Threading control
        self.thread = threading.Thread(target=self.run)
        self.control = threading.Event()
        self.thread.start()  # start the thread

    def increment_id(self):
        # Increase self.reqID, should be used after each request.
        self.reqID += 1

    def nextValidId(self, orderId: int):
        """ Receives next valid order id. Catch valid ID after connection"""
        self.reqID = orderId

        self.control.set()

    def connectAck(self):
        """ callback signifying completion of successful connection """
        print('DataAPI Connected.')

    # Define foreign exchange contract
    def fx_contract(self, symbol: str):
        """create fx_contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = 'CASH'
        contract.currency = "USD"
        contract.exchange = 'IDEALPRO'
        return contract

    # Define stock contract
    def stock_contract(self, symbol: str):
        """
        For more contract type and details
        See ...IB_API\samples\Python\Testbed\ContractSamples.py
        """
        contract = Contract()
        contract.symbol = symbol
        contract.secType = 'STK'
        contract.currency = "USD"
        contract.exchange = 'ISLAND'
        return contract

    # override this function in EWrapper, store historical data to a list
    def historicalData(self, reqId, bar: BarData):
        self.data.append(
            [self.symbol, bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume, bar.average, bar.barCount])

    def historical_to_csv(self):
        """
        Save historical_data to csv.
        If you want to use this function, do not forget to set the self.__duration
        when requesting historical data, or the interval of data will be decided automatically.

        """
        while True:
            time.sleep(1)
            if len(self.data) > 0:
                break
        df = pd.DataFrame(self.data,
                          columns=['Contract', 'DateTime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Average',
                                   'Count'])
        df.to_csv('..\data\historicaldata.csv')
        print(df.head(10))
        print("Historical data saved to csv")

    def historical_to_database(self):
        """
        Save historical data into the database
        """
        while True:
            time.sleep(1)
            if len(self.data) > 0:
                break

        df = pd.DataFrame(self.data,
                          columns=['Contract', 'DateTime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Average',
                                   'Count'])

        """
        Use dataframe slice to avoid data overlapping 
        df['DateTime'].iloc[0:1] - the earlist time of data requested
        self.latest_time - the time of last data in the database
        Use slice to ensure that the data to be saved do not overlap the existing data in database
        """
        df['DateTime'] = df['DateTime'].astype(int)
        if (df['DateTime'].iloc[0:1] <= self.latest_time).bool():
            df = df[(df['DateTime'] > self.latest_time)]
            print(df.head(5))
        try:
            df.to_sql(name='fivesecondbar', con=self.engine, if_exists='append', index=False, chunksize=2000,
                      method='multi')
            self.__historical_flag = True
        except (ValueError, pymysql.exc.OperationalError, pymysql.exc.IntegrityError) as err:
            print("Error {} occured when storing historical data to database!".format(err))
            self.__historical_flag = False

    # clear the data list
    def clear_data(self):
        self.data.clear()

    def realtimeBar(self, reqId, time, open, high, low, close,
                    volume, wap, count):

        """
        This function get one row of real-time data every 5 seconds, and store the data to database immediately
        return a dataframe for further operation
        """
        df = pd.DataFrame([[self.symbol, time, open, high, low, close, volume, wap, count]],
                          columns=['Contract', 'DateTime', 'Open', 'High', 'Low',
                                   'Close', 'Volume', 'Average', 'Count'])
        try:
            df.to_sql(name='fivesecondbar', con=self.engine, if_exists='append', index=False, chunksize=2000,
                      method='multi')
            print("Saving real-time bar...")
        except (ValueError, pymysql.exc.OperationalError, pymysql.exc.IntegrityError) as err:
            print("Error {} occured when storing real_time data to database!".format(err))
            # Normally, the first real-time data will concur an IntegrityError, but it does not matter.


        # return the real-time data for further use
        self.dataframe = df

    def request_historical_bar(self):
        """
        This function will request the historical data whose timestamp locate beteewn
        the latest timestamp in database and current timestamp。
        So duplicated data will not be stored.
        The dataframe.to_sql can only insert data without overlapping.
        """
        time.sleep(1)
        self.cal_duration()
        # 可能在5点和6点之间
        self.reqHistoricalData(self.reqID, contract=self.contract, endDateTime='',
                               durationStr=str(self.__duration) + ' ' + 'S',
                               barSizeSetting='5 secs', whatToShow='midpoint', useRTH=1, formatDate=2,
                               keepUpToDate=False, chartOptions=[])
        self.increment_id()

    def request_realtime_bar(self):
        """
        This function will only works after the historical data been updated.
        The order to use this function is:

        # First update historical data in database
        dataapi = DataAPI('EUR', 'FX')
        dataapi.request_historical_bar()
        dataapi.historical_to_database()

        # After historical data has been updated to database
        dataapi.request_realtime_bar()

        """
        count = 1
        while True:
            print("Historical data have not been updated!")
            time.sleep(1)
            count += 1
            if self.__historical_flag:
                print("Historical data updated!")
                break
            if count > 60:
                print("Waiting too long...")
                break
        if self.__historical_flag:
            self.reqRealTimeBars(self.reqID, dataapi.contract, 5, 'MIDPOINT', 1, [])
            self.increment_id()

    def cal_duration(self):
        """
        This method calculate the time interval between current time and the lasted time of the data stored in database.
        Then pass the self。duration to the reqHistoricalData method to avoid duplicated data.
        """
        sql_conn = pymysql.connect(host=self.__database_ip,
                                   user=self.__database_username,
                                   password=self.__database_password,
                                   database=self.__database_name,
                                   port=self.__database_port,
                                   )
        cur = sql_conn.cursor()
        sql = """
                SELECT
                    MAX( DateTime ) 
                FROM
                    fivesecondbar 
                WHERE
                    Contract = '{}'
               """.format(self.symbol)
        cur.execute(sql)
        last_time = cur.fetchone()[0]

        current_time = int(time.time())

        if last_time is None:
            self.__duration = self.max_duration
        else:
            last_time = int(last_time)
            self.__duration = current_time - last_time - 5
            self.latest_time = last_time
            if self.__duration >= self.max_duration:
                self.__duration = self.max_duration
        print("duration", self.__duration)


if __name__ == '__main__':
    dataapi = DataAPI('EUR', 'FX')
    dataapi.request_historical_bar()
    dataapi.historical_to_database()
    dataapi.request_realtime_bar()
