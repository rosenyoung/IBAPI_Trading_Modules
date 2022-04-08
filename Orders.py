"""
Author: Rosenyoung
This module is designed for placing orders and save the order status and position status into database
Position information will be updated after an order is submitted.
This module is also used for clear the position of one asset
This module can update account summary information if you want.

Version 1.0 2022-04-03
Support 3 kinds of order: Market, Limit, Market if touched

"""

from ibapi import wrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order
from decimal import Decimal

import pandas as pd
import numpy as np

import threading
import time

from DataBaseConn import DataBaseConn

from loguru import logger
logger.add("..\logs\\Orders_{time}.log", rotation="00:00")


class Orders(wrapper.EWrapper, EClient):

    def __init__(self, contract_type):
        """
        contract_type:str - 'FX' or 'STK'
        You must create different order object for different contract type
        """
        wrapper.EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.reqID = None

        self.contract_type = contract_type

        # Check contract type
        if self.contract_type not in ['STK', 'FX']:
            raise Exception(" Not a supported symbol")

        # Define the tags of account_summary
        self.account_summary_tag = 'NetLiquidation, TotalCashValue, AvailableFunds, GrossPositionValue'

        database_conn = DataBaseConn()
        self.data_conn = database_conn.conn
        self.cur = database_conn.cur

        # Creating  a random number between 100-149 as clientId
        CId = np.random.randint(100, 150)

        logger.info('Orders API Connecintg...')
        # connect to the IB TWS
        self.connect('127.0.0.1', 7497, clientId=CId)

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
        logger.info('Orders API Connected.')

    # Define foreign exchange contract
    @staticmethod
    def fx_contract(symbol: str):
        """create fx_contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = 'CASH'
        contract.currency = "USD"
        contract.exchange = 'IDEALPRO'
        return contract

    # Define stock contract
    @staticmethod
    def stock_contract(symbol: str):
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

    # Define the market order.
    @staticmethod
    def MarketOrder(action: str, quantity: Decimal):

        # ! [market]
        order = Order()
        order.action = action
        order.orderType = "MKT"
        order.totalQuantity = quantity
        # ! [market]
        return order

    # Define the market order which will be excuted if a target price is touched
    @staticmethod
    def MarketIfTouched(action: str, quantity: Decimal, price: float):

        # ! [market_if_touched]
        order = Order()
        order.action = action
        order.orderType = "MIT"
        order.totalQuantity = quantity
        order.auxPrice = price
        # ! [market_if_touched]
        return order

    # Define a limit order
    @staticmethod
    def LimitOrder(action: str, quantity: Decimal, limitPrice: float):

        # ! [limitorder]
        order = Order()
        order.action = action
        order.orderType = "LMT"
        order.totalQuantity = quantity
        order.lmtPrice = limitPrice
        # ! [limitorder]
        return order

    # Close the database connection
    def close_conn(self):
        self.data_conn.close()

    def place_orders(self, symbol, order_type, action, amount, price=1.10000):
        """
        symbol:str - symbol of the underlying,e.g. 'EUR', 'GBP', 'AAPL'
        order_type:str - 'MKT', 'LMT', or 'MKTIFTCH'
        action:str - 'buy' or 'sell'
        amount: Decimal
        price: float

        """
        if self.contract_type == 'STK':
            self.contract = self.stock_contract(symbol)
        elif self.contract_type == 'FX':
            self.contract = self.fx_contract(symbol)

        order = Order()
        timestamp = int(time.time())
        if order_type == 'MKT':
            order = self.MarketOrder(action, amount)
        elif order_type == 'LMT':
            order = self.LimitOrder(action, amount, price)
        elif order_type == 'MKTIFTCH':
            order = self.MarketIfTouched(action, amount, price)
        else:
            raise Exception("Unsupported order type!")

        # Place the order
        self.placeOrder(timestamp, self.contract, order)
        logger.info(f"Placed an order: OrderId : {timestamp}, Contract : {symbol}, Type : {order_type}, "
                    f"Action: {action}, Amount: {amount} ")

        # Save the order submitted immediately, waiting for
        initial_order_sql = f"""
                INSERT INTO orderstatus ( OrderID, Contract, Action, `Status`, AmountFilled, Remaining, AvgFillPrice, ClientID )
                VALUES
        	    ('{timestamp}', '{symbol}', '{action}', 'Submitted', 0.0, 0.0, 0.0, '{self.clientId}')
                """
        print("Saving the order: " + initial_order_sql)

        try:
            self.cur.execute(initial_order_sql)
            self.data_conn.commit()
        except Exception as err:
            self.data_conn.rollback()
            logger.warning("Error {} happened when initially saving order status!".format(err))

        # Sleep 1 second to avoid duplicated orderID
        time.sleep(1)

    def orderStatus(self, orderId, status, filled,
                    remaining, avgFillPrice, permId,
                    parentId, lastFillPrice, clientId,
                    whyHeld, mktCapPrice):
        """
        Save order status into database.
        Once order status is updated, call the reqPositions function and update position information.
        """
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        order_status_sql = f"""
        UPDATE orderstatus
        SET
	    `Status` = '{status}', 
	    AmountFilled = {filled}, 
	    Remaining = {remaining}, 
	    AvgFillPrice = {avgFillPrice}, 
	    ClientID = '{clientId}', 
	    LastUpdTime = '{current_time}'
	    WHERE
	    OrderID = {orderId}
        """
        print("Updating order status: " + order_status_sql)
        logger.info(f"Order status: Orderid : {orderId}, Status : {status}, AvgPrice : {avgFillPrice}")

        try:
            self.cur.execute(order_status_sql)
            self.data_conn.commit()
        except Exception as err:
            self.data_conn.rollback()
            logger.warning("Error {} happened when updating order status!".format(err))

        # Update position data after an order is placed
        self.reqPositions()

    def accountSummary(self, reqId: int, account: str, tag: str, value: str,
                       currency: str):
        # Saving account summary to database
        current_timestamp = int(time.time())
        upd_account_summary_sql = f"""
        INSERT INTO accountsummary (Account, `TimeStamp`,  {tag})
        VALUES
	    ('{account}', '{current_timestamp}', '{value}')
	    ON DUPLICATE KEY UPDATE
		{tag} = '{value}'
        """
        logger.info(f"Account summary: {tag} : {value}")
        print('Account summary sql: ' + upd_account_summary_sql)
        try:
            self.cur.execute(upd_account_summary_sql)
            self.data_conn.commit()
        except Exception as err:
            self.data_conn.rollback()
            logger.warning("Error {} happened when updating order status!".format(err))

    def accountSummaryEnd(self, reqId: int):
        # Notify an account summary request has ended.
        self.cancelAccountSummary(reqId)
        logger.info(f"Account summary request {reqId} ends!")

    def position(self, account, contract, position,
                 avgCost):

        # Saving current positions to database
        current_timestamp = int(time.time())
        upd_position_sql = f"""
                INSERT INTO position (Account, `TimeStamp`,  Contract, Position, AvgCost)
                VALUES
        	    ('{account}', '{current_timestamp}', '{contract.symbol}', '{position}', '{avgCost}')
        	    ON DUPLICATE KEY UPDATE
        		Position = '{position}',
        		AvgCost = '{avgCost}'
                """
        print('Position sql: ' + upd_position_sql)
        logger.info(f"Current Position: Contract : {contract.symbol}, Position ; {position}, AvgCost : {avgCost}")

        try:
            self.cur.execute(upd_position_sql)
            self.data_conn.commit()
        except Exception as err:
            self.data_conn.rollback()
            logger.warning("Error {} happened when updating position information!".format(err))

    def clear_position(self, symbol):
        # Clear current position of an asset
        current_postion_sql = f""" SELECT
                                        position 
                                    FROM
                                        position 
                                    WHERE
                                        contract = '{symbol}' 
                                        AND `timestamp` = (
                                            SELECT
                                                MAX( `timestamp` ) 
                                            FROM
                                                position 
                                            WHERE
                                            contract = '{symbol}')
        """
        self.cur.execute(current_postion_sql)
        current_position = self.cur.fetchone()[0]
        print("Current position: " + str(current_position))
        logger.info(f"Start to clear {symbol} current position")

        if current_position is not None:
            if current_position > 0:
                self.place_orders(symbol, 'MKT', 'sell', current_position)
            elif current_position < 0:
                self.place_orders(symbol, 'MKT', 'buy', abs(current_position))

        logger.info("Position Cleared")

    def positionEnd(self):
        # Notify an position information request has ended.
        self.cancelPositions()
        logger.info("Request position end!")


if __name__ == '__main__':
    orders_api = Orders('FX')
    time.sleep(5)
    orders_api.place_orders('EUR', 'MKT', 'buy', 110000)
    orders_api.place_orders('GBP', 'MKT', 'buy', 100000)
    orders_api.place_orders('EUR', 'LMT', 'sell', 100000, 1.30)
    time.sleep(5)
    orders_api.place_orders('EUR', 'MKT', 'sell', 100000)
    orders_api.place_orders('GBP', 'MKT', 'sell', 100000)
    get_orderid_sql = "Select orderid FROM orderstatus WHERE status != 'filled' order by orderid desc"
    orders_api.cur.execute(get_orderid_sql)
    orderid = orders_api.cur.fetchone()[0]
    print("OrderID:" + str(orderid))
    orders_api.cancelOrder(orderid)
    time.sleep(5)
    orders_api.clear_position('EUR')
    time.sleep(5)

    orders_api.reqAccountSummary(orders_api.reqID, 'All', orders_api.account_summary_tag)
    orders_api.increment_id()
