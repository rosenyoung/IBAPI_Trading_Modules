"""
Author: Rosenyoung
This is a sample strategy

Version 1.0 2022-04-07
This is a sample strategy
Version 1.1 2022-04-09
Add a loguru module to create log files
"""

import time

from DataAPI import DataAPI
from Orders import Orders

import pandas as pd

from DataBaseConn import DataBaseConn

from loguru import logger
logger.add("..\logs\\MASampleStrategy_{time}.log", rotation="00:00")


class MovingAverageStrategy:
    def __init__(self, symbol: str, contract_type: str, short_period: int, long_period: int):
        """
        symbol - Code of contract, e.g. 'EUR', 'AAPL'
        contract_type - 'FX' or 'STK'
        short_period - The shorter period for calculating moving average
        long_period - The longer period for calculating moving average

        """
        self.contract_type = contract_type
        self.symbol = symbol
        self.short_period = short_period
        self.long_period = long_period

        self.data_api = DataAPI(self.symbol, self.contract_type)
        self.order_api = Orders(self.contract_type)
        self.database_conn = DataBaseConn()

        time.sleep(5)
        # Update historical data
        self.data_api.request_historical_bar()
        self.data_api.historical_to_database()
        # Update real-time data
        self.data_api.request_realtime_bar()

    def run(self):
        time.sleep(5)
        # Read historical data from database
        historical_df = self.database_conn.read_historical_data(symbol=self.symbol)
        # updating_df is a dataframe refreshing every 5 seconds
        updating_df = historical_df.tail(100)

        # Check contract type
        contract = self.order_api.fx_contract(self.symbol)
        if self.contract_type == 'STK':
            contract = self.order_api.stock_contract(self.symbol)

        # Define position status, 1 for long, -1 for short and 0 for empty
        position_status = 0

        # Define the timecount, stop the process and clear position after 4 hours
        timecount = 0

        while True:
            # Get real-time bar data
            realtime_df = self.data_api.dataframe
            # concat the real-time data to updating_df
            updating_df = pd.concat([updating_df, realtime_df]).tail(100)
            print(updating_df.tail(5))

            # Create order ID
            orderId = int(time.time())

            # Calculate the current moving average
            ma_s = updating_df['Close'][-self.short_period:].mean()
            ma_l = updating_df['Close'][-self.long_period:].mean()

            # Calculate the moving average of previous tick
            s_previous = self.short_period + 1
            l_previous = self.long_period + 1
            ma_s_previous = updating_df['Close'][-s_previous:-1].mean()
            ma_l_previous = updating_df['Close'][-l_previous:-1].mean()

            # Get current position status
            current_postion_sql = f""" SELECT
                                                            position 
                                                        FROM
                                                            position 
                                                        WHERE
                                                            contract = '{self.symbol}' 
                                                            AND `timestamp` = (
                                                                SELECT
                                                                    MAX( `timestamp` ) 
                                                                FROM
                                                                    position 
                                                                WHERE
                                                                contract = '{self.symbol}')
                                """
            self.database_conn.cur.execute(current_postion_sql)
            self.database_conn.conn.commit()
            current_position = self.database_conn.cur.fetchone()[0]
            print("Current position: " + str(current_position))
            if current_position > 0:
                position_status = 1
            elif current_position < 0:
                position_status = -1
            else:
                position_status = 0
            print("position status:" + str(position_status))

            # The main strategy
            if (ma_s > ma_l) & (ma_s_previous < ma_l_previous):
                 if position_status != 1:
                    order = self.order_api.MarketOrder('buy', 100000+abs(current_position))
                    self.order_api.placeOrder(orderId, contract, order)
                    logger.info(f"Create a long order: OrderID : {orderId}")

            elif (ma_s < ma_l) & (ma_s_previous > ma_l_previous):
                 if position_status != -1:
                    order = self.order_api.MarketOrder('sell', 100000+abs(current_position))
                    self.order_api.placeOrder(orderId, contract, order)
                    logger.info(f"Create a short order: OrderID : {orderId}")

            time.sleep(5)
            timecount +=5

            # Stop after 4 hours and clear the position
            if timecount > 14400:
                self.order_api.clear_position(self.symbol)
                logger.info("Stop the strategy")
                time.sleep(5)
                break



if __name__ == "__main__":
    ma_strategy = MovingAverageStrategy('EUR', 'FX', 5, 20)
    ma_strategy.run()
