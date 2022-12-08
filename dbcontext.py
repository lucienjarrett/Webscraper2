import pyodbc
import pymssql
from dotenv import load_dotenv, dotenv_values

load_dotenv()
config = dotenv_values(".env")


def get_conn_string():
    database = config['DBNAME']
    user = config['DBUSER']
    server = config['DBSERVER']
    pwd = config['DBPASS']
    #  port = config['DBPORT']
    return 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + user + ';PWD=' + pwd




# def get_conn_string():
#     database = config['DBNAME']
#     user = config['DBUSER']
#     server = config['DBSERVER']
#     pwd = config['DBPASS']
#     #  port = config['DBPORT']
#     return 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + user + ';PWD=' + pwd


def get_conn_string_pymssql():
    database = config['DBNAME']
    user = config['DBUSER']
    server = config['DBSERVER']
    pwd = config['DBPASS']
    #  port = config['DBPORT']
    conn = pymssql.connect(server, user, pwd, database)
    return conn
#
# conn = get_conn_string_pymssql()
# cursor = conn.cursor()
# #
# cursor.execute('SELECT * FROM Customers')
# row = cursor.fetchall()
#
# for i in row:
#     print(i)

