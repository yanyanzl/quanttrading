
# this is the module for all database operation realted functions and features.

import psycopg2
from db_settings import DATABASES as dbs
from db_settings import DEBUG, ASSETDATA_TABLE_NAME, ASSETLIST_TABLE_NAME
import pandas as pd

from sys import path as pt
from finlib import format_excetpion_message
from finlib import Asset

from pathlib import Path  # if you haven't already done so
file = Path(__file__).resolve()
pt.append(str(file.parents[2]))


from utility import encrypt, decrypt


DEFAULT_DATABASE = dbs['NAME']
DEFAULT_USER = dbs['USER']
DEFAULT_HOST = dbs['HOST']

# DEFAULT_PASSWORD = os.environ.get("DB_PASS")
DEFAULT_PASSWORD = decrypt(b"080802", dbs['PASSWORD']).decode()
# password = encrypt(b"080802", b"080802")
print(f"pass is {DEFAULT_PASSWORD}")

print("DB_PASS is  ", DEFAULT_PASSWORD)
DEFAULT_PORT = dbs['PORT']

######### to be added: encryption function (for password related content)


# get a connection to database. inner function. 
# Open a cursor to perform database operations
def _get_conn(db=DEFAULT_DATABASE, dbhost=DEFAULT_HOST, dbport=DEFAULT_PORT, dbuser=DEFAULT_USER, dbpass=DEFAULT_PASSWORD):

        try:
            # build the connection to the database by psycopg2
            print(f"default db is {DEFAULT_DATABASE}")
            print(f"DEFAULT_HOST is {DEFAULT_HOST}")
            print(f"DEFAULT_PORT is {DEFAULT_PORT}")
            print(f"DEFAULT_USER is {DEFAULT_USER}")
            print(f"DEFAULT_PASSWORD is {DEFAULT_PASSWORD}")
            conn = psycopg2.connect(database=db, 
                    user=dbuser, host=dbhost, password=dbpass,port=dbport)
            return conn
        except Exception as ex:
            format_excetpion_message(ex)

# public function: to get a specific asset's history price data
# firstly get it from the database. if the database does not have the asset's data or all of it's data.
# then build it's data in the database.
def get_asset_price_data(asset_name=""):
     
     pass


# private function: to get data for an condition in a table.
# columns are the names for the columns of the data to get. if empty, return all columns in the table.
# condition is a dictionary. example: {'asset_name': TSLA, 'Date': '2023-12-18 00:00:00'}. if empty. 
# no condition

def _get_data_from_db(table_name="", columns = [], condition_dict={}):
        try:
            conn = None
            cur = None
            if not table_name:
                 raise ValueError(f"_get_data_from_da: parameter table_name is empty {table_name}")
            data = pd.DataFrame()

            # construct SQL 
            query = "SELECT"
            # if columns is empty. select all
            if not columns:
                 query = query + " * "
            else:
                for _ in columns:
                     query = query + _ + " , "
                query = query.rstrip().rstrip(",") 

            query = query + " FROM " + table_name

            # if no condition, query is completed.
            if not condition_dict:
                 query = query + ";"
            # add all conditions to the query
            else:
                query = query + " WHERE "
                for _ in condition_dict:
                     query = query + _ + " = " + condition_dict[_] + " AND "
                query = query.rstrip().rstrip("AND") + ";"

            conn = _get_conn()
            cur = conn.cursor()

            rows = cur.execute(query)

            conn.commit()
            cur.close()
            conn.close()

            return rows

        except (Exception, psycopg2.DatabaseError) as ex:
             format_excetpion_message(ex)
        finally:
            if cur is not None:
                 cur.close()
            if conn is not None:
                conn.close()

_get_data_from_db(table_name="aiinvest_assetlist")


# public function
# get the asset id by asset name. 
# if can't find the id. check it online, 
# if the asset is an valid ticker, insert it into the table
# otherwise raise valueerror.
def get_asset_id(asset_name=""):
        asset_id = -1
        try:
            # construct SQL 
            query = "SELECT id from aiinvest_assetlist where asset_name=\'" + asset_name +"\'"
            conn = _get_conn()
            cur = conn.cursor()

            is_finish = False
            while not is_finish:
                 
                cur.execute(query)
                rows = cur.fetchall()

                if DEBUG:
                    print(rows)
                
                # get asset_id in the database
                if len(rows) == 1:
                    asset_id = rows[0][0]
                    # break the loop
                    is_finish = True
                # if the asset doesn't exist in the database. insert it into it
                elif len(rows) == 0 and Asset(asset_name).is_valid():
                    _add_asset_to_list(asset_name, ASSETLIST_TABLE_NAME)
                    # then continue the loop to get the ID
                else:
                    raise ValueError(f"there is {len(rows)} asset in the db for asset_name: {asset_name}. or the asset_name may be an invalid ticker")
            
            conn.commit()
            return asset_id
        except (Exception, psycopg2.DatabaseError) as ex:
             format_excetpion_message(ex)
        finally:
            if cur is not None:
                 cur.close()
            if conn is not None:
                conn.close()

# add the asset_name to the asset list table. return the id for the asset.
def _add_asset_to_list(asset_name="", table_name=""):
        try:
            # check the args are correct type
            if  isinstance(asset_name, str):
                # check the list is not empty
                asset_name = pd.DataFrame({'asset_name':[asset_name]})
                
                # provide information for debug
                if DEBUG:
                    print(f" asset_name is {asset_name} and table name is {table_name} in _add_asset_to_list",  )
                
                _add_data_to_db(asset_name, table_name)

            # type of the args data inputs are not correct, 
            else:
                raise TypeError(
                    f"string expected for asset name, got'{type(asset_name).__name__}'"
                )
        except Exception as ex:
            format_excetpion_message(ex)


######### to be improved : years to more flexialbe xD, xM, xY, Max
# get data online and save to database. 
# years is number of yesrs to build the data. default is the current year till now
def _build_asset_data(asset_name="", years=0, table_name=ASSETDATA_TABLE_NAME):
        asset = Asset(asset_name)
        try:

            if not asset.is_valid():
                raise ValueError (f"Asset data is not found for Asset name : {asset_name}")
            
            asset_id = get_asset_id(asset_name)

            his_price = asset.fetch_his_price(period=years)

            his_price['asset_name'] = asset_name
            
            his_price['asset_id'] = asset_id

            his_price.pop('Adj Close')
            # his_price = his_price.rename(columns={'Date': 'asset_data_date', 
            #                           'Open': 'asset_open_price', 
            #                           'High': 'asset_high_price',
            #                           'Low': 'asset_low_price',
            #                           'Close': 'asset_close_price',
            #                           'Volume': 'asset_volume'
            #                           })
            his_price = his_price.set_index(['asset_name'],append=True)
            his_price.columns = map(str.lower, his_price.columns)

            if DEBUG:
                print(len(his_price))
                print("asset_id is ", asset_id)
                # print(his_price)
            
            # add the history price information for the asset to the database.
            _add_data_to_db(his_price,table_name)

            # this will print all the name for the columns
            # for price in his_price:
            #     print("price ------ ",price)

        except Exception as ex:
            format_excetpion_message(ex)



# add data to the specified table in the current connected database
# the column names in data_list should be the same as the table's column names
# to avoid duplicate data to be added to the database. 
# it is important to set the unique identifiers to be the index of the data_list.
# example : data_list.set_index(['asset_name', 'date'])
# if index is not assigned to the unique identifier. set the second column (column[1]) as the identifier
def _add_data_to_db(data_list=pd.DataFrame(), table_name=""):
    
    try:
        # check the args are correct type
        if  isinstance(data_list, pd.DataFrame) :
            # check the list is not empty
            if len(data_list) != 0:
                conn = _get_conn()

                cur = conn.cursor()

                # provide information for debug
                if DEBUG:
                    # print("data_list is\n", data_list)
                    print("_add_data_to_db: data_list.columns are ",data_list.columns)
                    print("_add_data_to_db: data_list.index.names are ", data_list.index.names)

                data_list = data_list.convert_dtypes()
                # print("data_list.values[1]", data_list.values[1])
                #  construct the query for add rows to the table
                query = "INSERT INTO "+ table_name + " ("
                
                is_index_none = False
                if data_list.index.names[0] is None:
                    is_index_none = True

                # all the columns names include indexes.
                all_columns = list(filter(None, data_list.index.names + data_list.columns.to_list()))
                print("all_columns", all_columns)

                for _ in all_columns:
                        query = query + f"{_} ,"

                query = query.rstrip(query[-1])+") SELECT "

                # each row of the Data_list is a row to be inserted.
                i = 0
                while i < len(data_list.index):

                    queryi = query

                    # if index.name == None. the index has no name and was added by dataframe. 
                    # it will not be added to the database.
                    # otherwise, add index values to the query. 
                    if not is_index_none:
                        for _ in data_list.index[i]:
                            # print(f"index {i} values are ", data_list.index[i])
                            queryi = queryi + f"'{_}',"
                    
                    # add non-index values to the query. 
                    k = 0
                    while k < len(data_list.columns):
                        # print(f"{_} is  ", data_list.iloc[i][_])
                        queryi = queryi + f"'{data_list.values[i][k]}'," 
                        k += 1
                    # print("data_list.iloc[i] is ",data_list.iloc[i])
                        
                    # avoid insert repeatidly
                    # construct the unique identifiers of the data_list and avoid duplicate data to be added
                    # if index is not assigned to the unique identifier. set the second column (column[1]) as the identifier
                    # any data has the same identifier in the database will not be added.
                    # remove the last comma and add conditions : the data does not exist in the database.
                    queryi = queryi.rstrip(queryi[-1]) + " WHERE NOT EXISTS (SELECT * FROM " + table_name + " WHERE "
                    
                    # if index is not assigned to the unique identifier. set the first column (column[0]) as the identifier
                    if data_list.index.names[0] == None:
                        queryi = queryi + data_list.columns[0] + f" = '{data_list.iloc[i][data_list.columns[0]]}' and "
                    # if the index is provided . use all the indexes as the unique identifier.
                    else:
                            j = 0
                            for _ in data_list.index.names:
                                # data_list.index[i] is the row i indexes. 
                                # data_list.index[i][j] is the jth index value in row i
                                # print(f"data_list.index[{i}][{j}] name is {_} and the value is ", data_list.index[i][j])
                                queryi = queryi + _ + " = '" + str(data_list.index[i][j]) + "' and "
                                j =+ 1
                        
                    queryi = queryi.rstrip().rstrip("and") + ");"
                    i += 1
                    # print(queryi)
                    cur.execute(queryi)


                conn.commit()

            # input list is empty
            else:
                raise Exception("The input data list is empty for _add_data_to_db or tablename")

        # type of the args data inputs are not correct, 
        else:
            raise TypeError(
                "DataFrame expected for data_list, "+
                f"got'{type(data_list).__name__}'"
            )

    except (Exception, psycopg2.DatabaseError) as ex:
            format_excetpion_message(ex)

    finally:
        if cur is not None:
                cur.close()
        if conn is not None:
            conn.close()

# check if the table exist in the current database. 
def is_table_valid(conn, table_name=""):
        exist = False
        try:
             
            query1 = "SELECT EXISTS (SELECT FROM information_schema.tables" + " WHERE table_name = '" + table_name + "');"

            cur = conn.cursor()

            cur.execute("SELECT * from aiinvest_assetlist")

            exist = cur.fetchone()[0]
            conn.commit()
            if DEBUG:
                print("table", table_name, exist)
            return exist
        
        except (Exception, psycopg2.DatabaseError) as ex:
             format_excetpion_message(ex)
        finally:
            if cur is not None:
                 cur.close()


# _build_asset_data("NFLX", 5)



# ##################
# development test. should be deleted when deploy.
def test_tmp():
        table_name = ASSETDATA_TABLE_NAME
        asset_name="AAPL"

        data_list = pd.DataFrame({'asset_name':[asset_name], 'asset_id':[1], 'date':['2023-12-12']})
        print(data_list)
        # asset_name = asset_name.set_index(['asset_name', 'date'])
        print(data_list.index)
        if data_list.index.names[0] == None:
             print("datalist with no index")
        
        print("@@@@@@@@@@@@@@data.columns", data_list.columns)

        data_list = data_list.set_index(['asset_name','date'])
        for _ in data_list.index.names:
            print(f"Asset index are:" , _)

        query = "INSERT INTO "+ table_name + " ("
        
        start_column = 0
        if data_list.index.names[0] == None:
            start_column = 1

        
        all_columns = list(filter(None, data_list.index.names + data_list.columns.to_list()))
        print("all_columns", all_columns)
        for _ in all_columns:
                query = query + f"{_} ,"

        query = query.rstrip(query[-1])+") SELECT "

        # each row of the Data_list is a row to be inserted.
        i = 0
        while i < len(data_list.index):

            queryi = query
            # add index values to the query. 
            for _ in data_list.index[i]:
                print("index i values are ", data_list.index[i])
                queryi = queryi + f"'{_}',"
            
            # add non-index values to the query. 
            for _ in data_list.columns[start_column:]:
                print(" $$$$$$$$$$$ _ is \n  ", _)
                
                queryi = queryi + f"'{data_list.iloc[i][_]}'," 
            
            # remove the last comma and add conditions : the data does not exist in the database.
            queryi = queryi.rstrip(queryi[-1]) + " WHERE NOT EXISTS (SELECT * FROM " + table_name + " WHERE "
            
            # if index is not assigned to the unique identifier. set the second column (column[1]) as the identifier
            if data_list.index.names[0] == None:
                queryi = queryi + data_list.columns[1] + f" = '{data_list.iloc[i][data_list.columns[1]]}' and "
            # if the index is provided . use all the indexes as the unique identifier.
            else:
                    j = 0
                    for _ in data_list.index.names:
                        print("********** _ is ", _)
                        print("data_list.index[i][j] is ", data_list.index[i][j])
                        queryi = queryi + _ + " = '" + data_list.index[i][j] + "' and "
                        j =+ 1
                
            queryi = queryi.rstrip().rstrip("and") + ");"
            i += 1
            print(queryi)
   
        # _add_data_to_db(asset_name, ASSETLIST_TABLE_NAME)

''' 
conn = _get_conn()
cur = conn.cursor()

cur.execute("SELECT * from aiinvest_assetlist")

rows = cur.fetchall()

for row in rows:
    print(row)
# cur.execute("SELECT * from aiinvest_assetdata")
# rows = cur.fetchall()

# for row in rows:
#     print(row)


# this will get all the table's information .
# cur.execute("""SELECT *
# FROM INFORMATION_SCHEMA.TABLES
# WHERE TABLE_TYPE = 'BASE TABLE' and TABLE_SCHEMA = 'public'""")
# rows = cur.fetchall()

# for row in rows:
#     print(row)


# this will get all the table's columns' information .
# cur.execute("""SELECT * FROM information_schema.columns
# WHERE table_name = 'aiinvest_assetdata'""")

table_name = "aiinvest_assetdata"
query = "SELECT column_name FROM information_schema.columns WHERE table_name ='"+table_name+"'"

query1 = "SELECT EXISTS (SELECT FROM information_schema.tables" + " WHERE table_name = '" + table_name + "');"

# this will get all the column_name from the table .
cur.execute(query1)
rows = cur.fetchall()

for row in rows:
    print(row)

print(rows)
# Make the changes to the database persistent
conn.commit()


cur.close()

conn.close()
'''

# test_tmp()