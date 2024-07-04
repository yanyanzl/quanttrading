from pandas import DataFrame, to_datetime
import pandas as pd
from data.finlib import Asset
from datetime import datetime
import time
from ui.chartitems import DataManager


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

def testConcat():
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



