"""

Author: Rosenyoung
This module extract the database connection function
This module also contains a function to query historical data

Version 1.0 2022-04-07

"""

import pandas as pd

from sqlalchemy import create_engine
import pymysql


class DataBaseConn:
    def __init__(self):
        self.__database_username = 'username'
        self.__database_password = 'password'
        self.__database_ip = 'localhost'
        self.__database_port = 3306
        self.__database_name = 'databasename'

        self.engine = create_engine('mysql+pymysql://{0}:{1}@{2}/{3}'.
                                    format(self.__database_username, self.__database_password,
                                           self.__database_ip, self.__database_name))

        self.conn = pymysql.connect(host=self.__database_ip,
                                    user=self.__database_username,
                                    password=self.__database_password,
                                    database=self.__database_name,
                                    port=self.__database_port,
                                    )

        self.cur = self.conn.cursor()

    def read_historical_data(self, length=2880, symbol='EUR'):
        """
               Read last data from database, length defined the number of rows of data requested
               When length = 2880, it requests trading data of last 4 hours.
        """
        historical_sql = f"""
                           SELECT
                                * 
                            FROM
                                ( SELECT * FROM `fivesecondbar` 
                                            WHERE Contract = '{symbol}' 
                                            ORDER BY `DateTime` DESC LIMIT {length} ) 
                                            AS lastdata 
                            ORDER BY
                                lastdata.`DateTime`
	"""

        historical_df = pd.read_sql_query(historical_sql, self.engine)

        return historical_df

    def close_conn(self):
        self.conn.close()


if __name__ == "__main__":
    database_conn = DataBaseConn()
    df = database_conn.read_historical_data()
    print(df.head(10))
