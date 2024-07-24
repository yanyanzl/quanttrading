from pandas import DataFrame, to_datetime
import pandas as pd
from data.finlib import Asset
from datetime import datetime
import time
from datatypes import Account
from ui.chartitems import DataManager
from utility import _idGenerator, TEMP_DIR, TRADER_DIR, get_file_path
import shelve
import asyncio
import yfinance as yf

# tsla = yf.Ticker("TSLA")

# df1 = tsla.history(period="1mo")
# df1.reset_index(inplace=True)
# print(f"{df1=}")

# df2 = tsla.history(period="1d")
# df2.reset_index(inplace=True)
# df2.loc[0,'Open'] = 666
# df2.loc[0,'Date'] = '2024-07-17 00:00:00-04:00'
# print(f"{df2=}")

# index = df1[df1['Date'] == df2.at[df2.first_valid_index(), 'Date']].index

# # self._data[self._data['Date'] == bar.at[bar.first_valid_index(), 'Date']].index
# print(f"{index=}")

# df1 = pd.concat([df1,df2], ignore_index=True)
# df1.drop_duplicates(subset='Date', keep= "last", inplace= True)
# df1.sort_values(by=['Date'], inplace= True)
# df1.reset_index(inplace=True, drop=True)


# print(f"after drop_duplicates \n {df1=}")


# df3 = df1.merge(df2, how='right', on='Date')

# print(f"df1 is \n {df1}")
# print(f"df3 is \n {df3}")

# print(f"df1[1:] is \n {df1['Date']}")
# print(f"df1 is \n {df1[df1.columns]}")
# print(f"{df1.columns}")
# import numpy as np
# df1[df1.columns] = np.where(df1['Date'] == df2.at[0,'Date'],df2.iloc[0][df2.columns], df1[df1.columns])


# for index in df2.index:
#     print(f"{df2.iloc[[index]]=}")
#     df1.loc[df1['Date'] == df2.iloc[[index, 'Date']]]
#     df1.value


# _bar_picutures: dict[int, str] = {}

# print(f"{_bar_picutures=}")
# print(f"{type(_bar_picutures)=}")
# print(f"{len(_bar_picutures)=}")
# data_filename: str = "ib_contract_data.db"
# data_filepath: str = str(get_file_path(data_filename))
# print(f"{data_filepath}")

# # with shelve.open(data_filepath) as f:
# #     f["ib_contracts"] = []

# with shelve.open(data_filepath) as f:
#     _activeContracts = f.get("ib_contracts", [])
#     print(f"{_activeContracts}")
from zoneinfo import ZoneInfo
from tzlocal import get_localzone_name
import tzlocal
from datetime import timedelta
# end: datetime = datetime.now(ZoneInfo(get_localzone_name()))
# print(f"{end=} and {type(end)}")
zone = get_localzone_name()
print(f"zone info is {get_localzone_name()}")

end: datetime = datetime.now(ZoneInfo(get_localzone_name()))

print(f"{end.strftime("%Y%m%d %H:%M:%S %Z")}")

start: datetime = end - timedelta(days=500)
from dateutil import parser
# date6 = parser.parse("20240718 04:00:00 US/Eastern")
date6 = datetime.strptime("20240718 04:00:00", "%Y%m%d %H:%M:%S")


print(f"{date6}")

def getDuration(start: datetime, end: datetime) -> str:
    duration = ""
    delta = end - start
    seconds = int(delta.total_seconds())
    if seconds > 3600 * 24:
        duration = str(delta.days) + " D"
        print(f"{duration=}")
    else:
        duration = str(seconds)+'S'
        print(f"{duration=}")

getDuration(start, end)



import re
from typing import Literal

Interval = Literal["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "1wk"]
# durationStr: S/D/W/M/Y. Example '1 D'



def constructDataframe():
    dt = {'Date':1, 'Open':2, 'High':3, 'Low':4, 'Close':5, 'Volume':6, 'Wap':7, 'Symbol':8, 'Gateway':9}
    data = DataFrame(data=dt,index=[0])
    dt1 = {'Date':1, 'Open':2, 'High':3, 'Low':4, 'Close':5, 'Volume':6, 'Wap':7, 'Symbol':8, 'Gateway':9}
    data1 = DataFrame(data=dt,index=[0])

    data = pd.concat([data, data1], ignore_index=True)

    dt2 = {'Date':1, 'Open':2, 'High':3, 'Low':4, 'Close':5, 'Volume':6, 'Wap':7, 'Symbol':8, 'Gateway':9}
    data2 = DataFrame(data=dt,index=[0])
    dataDict = {"TSLA":dt, "AAPL":data1}

    data = pd.concat([data, data2], ignore_index=True)
    print(f"{data=}")
    print(f"{dataDict=}")
    dataDict.update({"TSLA":data})
    print(f"{dataDict=}")
constructDataframe()

async def check_connection() -> None:
        """检查连接"""
        i = 0
        while True:
            i += 1
            await asyncio.sleep(10)
            print(f"this is test round  {i=}")

def testasync():
    loop = asyncio.get_event_loop()
    future = loop.create_task(check_connection)
    # loop.run_until_complete(check_connection)

def shelveTest():
    print(f"{TEMP_DIR=} and {TRADER_DIR=}")
    data_filename: str = "ib_contract_data"
    data_filepath: str = str(get_file_path(data_filename))


    tag = "bond"
    value = "99999"
    currency = "USD"
    account: Account = Account()
    account.update(id=100,reqId=1000, accountValue={"stocks":["6666666","USD"]})
    account.get('accountValue').update({tag:[value, currency]})
    print(f"{account=}")

    reqId = {"last":[1,2,3,4], "bidask":-1}

    req = reqId.get("last1", None)
    if req is None:
        req = []
        reqId["last1"] = req
    req.append(6)

    print(f"{data_filepath=}")
    with shelve.open(data_filepath) as f:
        f["account"] = account


i = _idGenerator()
n = next(i)
print(f"{n=} and {type(n)}")

def generatorTest():
    i = _idGenerator()
    for k in range(20):
        print(f"{next(i)=}")


    # with open("./log/restats", "wb") as f:
    #     f.write(b"hello world")

    tag = "bond"
    value = "99999"
    currency = "USD"
    account: Account = Account()
    account.update(id=100,reqId=1000, accountValue={"stocks":["6666666","USD"]})
    account.get('accountValue').update({tag:[value, currency]})
    print(f"{account=}")

    reqId = {"last":[1,2,3,4], "bidask":-1}

    req = reqId.get("last1", None)
    if req is None:
        req = []
        reqId["last1"] = req
    req.append(6)

    print(f"{reqId=}")
    # for key, value in reqId.items():
    #     print(f"{key=} and {value=}")


def testLoc():
    data = data1
    # print(f"data.iloc[0]['Open'] is {data.iloc[0]['Open']}")
    # print(f"data.first_valid_index is {index_x}")
    # print(f"data.at[data.first_valid_index,'Open'] is {data.at[index_x, 'Open']}")
    # print(f"data.iat[0,0] is {data.iat[0,0]}")
    # print(f"data.iat[0,1] is {data.iat[0,1]}")
    # print(f"data['Open'].values[0] is {data['Open'].values[0]}")

    data1 = Asset("AAPL").fetch_his_price(period=1)
    data1 = data1.reset_index()
    print(data1)
    print("****************************")
    index = len(data1.index)
    print(f"index is {index}")
    data = data1.iloc[index-11:index]
    print(data)

    min = data['Low'].min()
    max = data['High'].max()
    print(f"min is {min} \n max is {max}")

def testConcat(data1):
    dm = DataManager(data1)
    data2 = data1[3:4]
    data3 = data1[5:10]
    # data2.set_index()
    print(f"data2 is {data2}")
    print(f"data3 is {data3}")
    data4 = pd.concat([data3, data2], ignore_index=True)
    print(f"data4 is {data4}")
    x = 0.33
    print(int(x))

def test6():
    bar = None
    if bar:
        print("bar is not none")
    else:
        print("bar is None")
    # testConcat()

    data = data1.iloc[[10]]
    print("data is \n", data)
    # data = DataFrame(data)
    print(data.index)
    print(data.at[10,'Open'])
    data.reset_index(inplace=True)
    print(data.index)
    print(data)

def test3():
    dm = DataManager(data1)

    date = dm.getDateTime(dm._data.first_valid_index())
    print(f"dm.  is \n {date}")
    print(f"type(date) is {type(date)}")



def test1():
    web_stats = {'Day': [1, 2, 3, 4, 2, 6],
                'Visitors': [43, 43, 34, 23, 43, 23],
                'Bounce_Rate': [3, 2, 4, 3, 5, 5]}
    df = DataFrame(web_stats)
    print(f"before drop, df is \n {df}")

    print(f"df.index \n {df.index}")

    print(f"df.first_valid_index \n {df.first_valid_index()}")

    print(f"df.loc[index] is \n {df.loc[df.first_valid_index()]}")

    print(f"df.loc[0:1] is \n {df.loc[0:1]}")
    print(f"df[0:1] is \n {df[0:1]}")

    print(f"type(df[0:1]) is \n {type(df[0:1])}")

    # print(f"df[index] is \n {df[df.first_valid_index()]}")

    d1 = df[df.first_valid_index():df.first_valid_index()+2]
    print(f"d1 is \n {d1}")

    df.drop(df.index, inplace=True)

    print(f"after drop, df is \n {df}")


def test2():

    index = data1.first_valid_index()
    print(f"data1.loc[data1.firstindex] is \n {data1.loc[index]}")
    print(f"data1.firstindex is \n {index}")

    date = data1.loc[index]['Date']
    print(f"data1.loc[data1.firstindex][date] is \n {date}")
    print(f"type(date) is \n {type(date)}")
    print(f"type(datetime) is {type(datetime)}")

    print(f"time.time is {time.time()}")
    print(f"datetime(time.time()) is \n {datetime.fromtimestamp(time.time())}")
    # print(f"datetime(time.time()) is \n {datetime.fromtimestamp(date.)}")


    date: pd.Timestamp = data1.loc[index]['Date']
    print(f"data1.loc[data1.firstindex][date] is \n {date}")
    print(f"type(date) is \n {type(date)}")

    print(date.to_pydatetime())
    print(type(date.to_pydatetime()))


# print(f"datetime(time.time()) is \n {datetime.strptime(date, '%Y-%m-%d %H:%M:%S')}")

# print(f"datetime.timestamp() is {datetime.timestamp()}")



"""
Python strftime cheatsheet
🐍🐍🐍

Code	Example	Description
%a	Sun	Weekday as locale’s abbreviated name.
%A	Sunday	Weekday as locale’s full name.
%w	0	Weekday as a decimal number, where 0 is Sunday and 6 is Saturday.
%d	08	Day of the month as a zero-padded decimal number.
%-d	8	Day of the month as a decimal number. (Platform specific)
%b	Sep	Month as locale’s abbreviated name.
%B	September	Month as locale’s full name.
%m	09	Month as a zero-padded decimal number.
%-m	9	Month as a decimal number. (Platform specific)
%y	13	Year without century as a zero-padded decimal number.
%Y	2013	Year with century as a decimal number.
%H	07	Hour (24-hour clock) as a zero-padded decimal number.
%-H	7	Hour (24-hour clock) as a decimal number. (Platform specific)
%I	07	Hour (12-hour clock) as a zero-padded decimal number.
%-I	7	Hour (12-hour clock) as a decimal number. (Platform specific)
%p	AM	Locale’s equivalent of either AM or PM.
%M	06	Minute as a zero-padded decimal number.
%-M	6	Minute as a decimal number. (Platform specific)
%S	05	Second as a zero-padded decimal number.
%-S	5	Second as a decimal number. (Platform specific)
%f	000000	Microsecond as a decimal number, zero-padded to 6 digits.
%z	+0000	UTC offset in the form ±HHMM[SS[.ffffff]] (empty string if the object is naive).
%Z	UTC	Time zone name (empty string if the object is naive).
%j	251	Day of the year as a zero-padded decimal number.
%-j	251	Day of the year as a decimal number. (Platform specific)
%U	36	Week number of the year (Sunday as the first day of the week) as a zero-padded decimal number. All days in a new year preceding the first Sunday are considered to be in week 0.
%-U	36	Week number of the year (Sunday as the first day of the week) as a decimal number. All days in a new year preceding the first Sunday are considered to be in week 0. (Platform specific)
%W	35	Week number of the year (Monday as the first day of the week) as a zero-padded decimal number. All days in a new year preceding the first Monday are considered to be in week 0.
%-W	35	Week number of the year (Monday as the first day of the week) as a decimal number. All days in a new year preceding the first Monday are considered to be in week 0. (Platform specific)
%c	Sun Sep 8 07:06:05 2013	Locale’s appropriate date and time representation.
%x	09/08/13	Locale’s appropriate date representation.
%X	07:06:05	Locale’s appropriate time representation.
%%	%	A literal '%' character.
"""