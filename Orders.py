from ibapi import wrapper
from ibapi.client import EClient

import pandas as pd
import numpy as np

from ibapi.common import BarData
from ibapi.contract import Contract

import threading
import time
from sqlalchemy import create_engine
import pymysql

class Orders(wrapper.EWrapper, EClient):

    def __init__(self, symbol, contract_type):
        """
        symbol: str - The contract symbol, such as 'EUR', 'AAPL'
        contranct_type: str - 'FX' or 'STK'
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
        self.__database_username = 'username'
        self.__database_password = 'password'
        self.__database_ip = 'localhost'
        self.__database_port = 3306
        self.__database_name = 'databasename'
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