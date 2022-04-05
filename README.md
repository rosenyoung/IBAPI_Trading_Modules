# IBAPI_Trading_Modules
This modules are a simple trading system based on Interactive Brokers API. I will compelete it gradually.

Please see the DDL.sql as reference to construct your mysql database.

DataAPI can acquire historical and real-time 5 second bar data and save the data into mysql database. You should have set a mysql database before using this API. Data will be stored to a schema called FiveSecondBar. Do not forget to change the database connection parameters before connecting.

Orders.py is used for placing orders. Except placing orders it can also be used to update position and account summary information. Currently only marker order, limit order and marketiftouched order is supported. An OrderStatus schema is used to save the order information. The position schema is used to store position information. The AccountSummary schema is used to save account information like current netliquidity, cash available and so on.

