# IBAPI_Trading_Modules
These modules are a simple trading system based on Interactive Brokers API. The system can save trading data, the orders placed and their status, and account information into database on a real-time basis. These data can be used for backtesting and performance valuation afterwards. Now the design of this system mainly focus on foreign exchanges. I will compelete the system gradually.

Please see the DDL.sql as reference to construct your mysql database. Do not forget to change the database connection parameters before connecting.

DataAPI can acquire historical and real-time 5 second bar data and save the data into mysql database. You should have set a mysql database before using this API. Data will be stored to a schema called FiveSecondBar.

Orders.py is used for placing orders. Except placing orders it can also be used to update position and account summary information. Currently only market order, limit order and marketiftouched order is supported. An OrderStatus schema is used to save the order information including orderID, order status. The Position schema is used to store position information, including contract symbol, amount of position. The AccountSummary schema is used to save account information like current netliquidity, cash available and so on.

DataBaseConn is used for connecting the database, and acquire historical data from database. Modify your database connection parameters in this module.

MASampleStrategy is a sample strategy.(Do not expect that this strategy could earn a profit). Use it as a reference and construct your own strategy.
