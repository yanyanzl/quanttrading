from PySide6.QtCore import QObject
from pandas import DataFrame, to_datetime
import pandas as pd
from data.finlib import Asset
from datetime import datetime, timedelta
import time
from datatypes import Account
from ui.chartitems import DataManager
from utility import _idGenerator, TEMP_DIR, TRADER_DIR, get_file_path
import shelve
import asyncio
import yfinance as yf
from zoneinfo import ZoneInfo
from tzlocal import get_localzone_name
import tzlocal
import inspect
from riskmanager.engine import TradeBook, RiskLevel
from pathlib import Path
# from vnpy_ctastrategy import CtaTemplate, TargetPosTemplate
from glob import glob
import importlib, traceback
from constant import _, Exchange
from types import ModuleType

from database import get_database
from datatypes import Interval, TradingSignal, SignalType
from typing import get_args
from data.yfdatafeed import YfDatafeed
from datatypes import HistoryRequest, TickManager, TickData, PlotData
import numpy as np
from utility import dateToLocal, LOCAL_TZ
from vnpy_algotrading.algos.hft_direction_algo import TradingStatus
from constant import OrderType, Direction, Offset, EVENT_PLOT

from random import randrange
import csv
from itertools import product
from pandas import DataFrame, Series
from ui.dataplot import DataPlot
from event import EventEngine, Event
from threading import Thread
import pyqtgraph as pg
from datetime import timedelta
import logging

from typing import get_args
from data.base import TickerData, TICKER_DATA_KEYS
from datatypes import Minutes_DAYS
logger = logging.getLogger(__name__)

from data.techanalysis import TechAnalysis, TickManager

ta: TechAnalysis = TechAnalysis("TSLA")
basicinfo:TickerData = ta.getBasicInfo()
print(round(3.3))
# print(f"{basicinfo}")
# print(f"{ta.ATR_minite_summary()}")
print(f"{ta.ATR_days()}")
# print(f"{basicinfo.__getattribute__("symbol")=}")
# print(f"{basicinfo.__getattribute__("xxx")=}")
# print(f"{ta.ATR_minite_summary(days="1d")}")


symbol = "TSLA"
ticker = TickerData({"symbol":symbol})
tsla = yf.Ticker(symbol)

def getBasicInfo():
    basic_info:dict = tsla.basic_info
    for info in basic_info.keys():

        # print(f"{info=}")
        if info in TICKER_DATA_KEYS:
            ticker[info] = basic_info[info]

def _true_range(high:float, low:float, pervious_close:float) -> float:
    """
    single period true range.
    True Range =  max[(high -low), abs(high - previous close),
      abs (low - previous close)
    """
    if high and low and pervious_close and high >= low:
        return max((high-low), abs(high-pervious_close), abs(low-pervious_close))
    return 0


def ATR_minite_summary(period:int=14, days:Minutes_DAYS = "5d", hours:int = 7, count:int = 6) -> dict[datetime, list]:
    """
    Valid days: 1d,5d. get result for last 1 day or 5 days.
    valid hours: 1 to 7. get result for the last 1 hour or up to 7 hours.
    count: valid 1 to 60 - period. number of ATRs per hour to be returned.
    return datetime to the list of ATRs for that time range (per hour)
    """
    assert days in get_args(Minutes_DAYS)
    if hours < 1 or hours > 7:
        hours = 7
    
    data = tsla.history(period=days, interval="1m")

    last_date:pd.Timestamp = data.loc[data.last_valid_index()].name.replace(hour=23)
    ATR_summary:dict[datetime, list] = {}
    if days == "1d":
        days = 1
    else:
        days = 5
    for i in range(days):

        current_data = data.loc[last_date - timedelta(days=i, hours=23) : last_date - timedelta(days=i)]
        # print(f"{current_data}")
        last_hour:pd.Timestamp = current_data.loc[current_data.last_valid_index()].name
        last_hour = last_hour.replace(hour=last_hour.hour+1, minute=0)
        for j in range(hours):
            hour_data = current_data.loc[last_hour - timedelta(hours=1+j) : last_hour - timedelta(hours=j,minutes=1)]
            num = min(len(hour_data), (period+count))

            hour_data.reset_index(inplace=True)
            hour_data = hour_data.loc[0:num]

            close = hour_data["Close"]
            high = hour_data["High"]
            low = hour_data["Low"]
            # print(f"{hour_data=}")
            ATR_summary.update({last_hour - timedelta(hours=1+j): ATR_by_datas(high, low, close, period)})
        
    print(f"{ATR_summary}")


def ATR_by_datas(high:pd.Series, low:pd.Series, close:pd.Series, period:int=14) -> list[float]:
    """
    get the day/hour/minite/second level ATR by providing the highs, lows, closes and period.
    return all available ATR series based on these data.
    for lasest one, get the last data from the returned list.
    """
    if (high is not None and low is not None and close is not None
         and high.count() >= low.count() >= close.count() > period+1
         ):

        true_ranges:np.ndarray = np.zeros(period)
        datacount = close.count()
        average_TRs:list = []

        current_range:int = 0
        last_average_TR:float = 0

        for i in range(1, datacount):

            true_range = _true_range(high[i], low[i],close[i-1])

            if current_range >= period:
                # start to calculate the Average True Range.
                average_TR = (last_average_TR * (period - 1) + true_range) / period
                average_TRs.append(average_TR)
                last_average_TR = average_TR
                # print(f"round start {i}: {average_TR=} with true{true_range} high:{high[i]} low:{low[i]}, close: {close[i-1]}")

            else:
                true_ranges[current_range] = true_range
                current_range += 1
                if current_range == period:
                    last_average_TR = true_ranges.sum()/period
                    # print(f"{last_average_TR=}")
        return average_TRs
    else:
        logger.info(f"invalid input for ATR_minite: high {high}, low: {low}, close:{close}")
        return []


# ATR_minite_summary(14)

# tartget = tsla.get_upgrades_downgrades()
# print(f"{tsla.actions=}")

# print(f"{tsla.info=}")
# print(f"{tsla.fast_info=}")
# print(f"{tsla.trend_details=}")

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


# date = datetime.now().strftime("%H:%M:%S.%f")
# origin_data_x: np.ndarray = np.array([date for _ in range(20)], dtype=object)
# origin_data_x.fill()
# print(origin_data_x)
def dbtest():
    from database import get_database
    from vnpy_sqlite.sqlite_database import SqliteDatabase, DbDailyProfit

    db:SqliteDatabase = get_database()
    # db.save_daily_pnl(datetime.now(), 66, 50)
    daily_pnl: DbDailyProfit = db.load_last_daily_pnl()
    print(f"{daily_pnl.date},{daily_pnl.total_pnl} {type(daily_pnl)}")

def testDataPlot():
    app = pg.mkQApp("Plotting Example")

    eventengine = EventEngine(1)
    eventengine.start()

    def send_event(i):
        # x = datetime.now().strftime('%H:%M:%S.%f')
        x = datetime.now().timestamp()
        y = np.random.randint(1, 10)
        eventengine.put(Event(EVENT_PLOT, PlotData(desc="Tick",x_data=x, y_data=y)))

    def dataplot():
        for i in range(20):
            send_event(i)
            time.sleep(1)

    pg.QtCore.QThread()
    dataplot_thread = Thread(target=dataplot)
    dataplot_thread.start()

    dataPlot = DataPlot(eventengine, 30)

    app.exec()
    eventengine.stop()
    dataplot_thread.join()


def arrayTest():
    newarray = np.zeros(10)
    newarray[5] = 10
    newarray[6] = 106
    newarray[0:4] = 100
    # print(f"{newarray=} and {newarray.sum()}")

    print(f"{newarray.max()=} and {type(newarray.min())}")

    data: np.ndarray = np.zeros((3,2),dtype= float)
    data[-2] = (1,3)
    data[-1] = (3,3)
    offset1 = 2
    offset = - offset1
    print(f"{data=}, {data[:,0]=}, {data[:,1]=}, {offset=} {data[offset,1]=}, {data[offset][1]=}")

    for i in range(0,100,5):
        print(f"{100-i}")

# arrayTest()

def seriesTest():
    r = [1,3,5,6]
    ser = pd.Series(r)

    print(f"{ser.iloc[-2]}")

    setting = [[3,5,7,9,10],[3,5,7,9,10]]
    settings = product(*setting)
    for _ in settings:

        print(f"{_=}")

def load_modules() -> list[str]:
    symbols:list[str] = []
    for filepath in glob("**/*.py", recursive=True):
        filename = filepath.removesuffix(".py")
        modulename = filename.replace("/",".")

        symbols.append(modulename)
    print(symbols)
    return symbols


# load_modules()

def readCSV():
    dataPath = Path(__file__).parent.joinpath("data/symbols.csv")
    # dataPath = dataPath
    # dataPath = dataPath
    # print(f"{dataPath=}")
    with open(dataPath, newline='') as csvfile:
        spamreader = csv.reader(csvfile)
        for row in spamreader:
            symbol = row.pop()
            print(f"{symbol} and {type(symbol)}")

# USED_SIGNAL_TYPES = [SignalType.SIGNAL_SLOW_OPEN, SignalType.SIGNAL_SLOW_CLOSE, SignalType.SIGNAL_RSI]

# signal = TradingSignal(type=SignalType.SIGNAL_SLOW_CLOSE,symbol="TSLA",value=1)
# if signal:
#     print(f" {signal["symbol"] == "TSLA"},  {signal["type"] in USED_SIGNAL_TYPES} , {USED_SIGNAL_TYPES=}")
#     if signal["symbol"] == "TSLA" and signal["type"] in USED_SIGNAL_TYPES:
#         print(f" {signal["symbol"] == "TSLA"},  {signal["type"] in USED_SIGNAL_TYPES} , {USED_SIGNAL_TYPES=}")

# print(f"{Direction.values()[0] == Direction.LONG.value}")

def tickManage():
    tickmanager = TickManager(100)

    a = np.random.random(200) + 50
    # a = np.arange(50,60,0.05)
    for num in a:
        # print(f"num={num}")
        tick = TickData("", "tsla", Exchange.SMART, datetime.now(LOCAL_TZ), last_price=num)
        tickmanager.on_tick(tick)

    rsi_result = tickmanager.rsi(10)

    realrange20 = tickmanager.realRange(100, 1)
    realrange10 = tickmanager.realRange(150, 1)
    # atr_1 = tickmanager.atr(14, 100)
    # atr_1 = tickmanager.atr(14, 100)
    atr_1 = tickmanager.atr(14, 50)

    print(f"rsi = {rsi_result} and {np.isnan(rsi_result)}")

    print(f"{realrange10=} and {realrange20=}")
    print(f"{atr_1=}")
    

# tickManage()

# print(f"{a=}")
# dt = datetime.now(LOCAL_TZ).second
# print(f"{dt=} ")

def yfTest():
    df = YfDatafeed()
    end: datetime = datetime.now()
    start: datetime = end - timedelta(1)

    req = HistoryRequest("TSLA", Exchange.SMART, start, end, "", "1m" )
    data = df.query_bar_history(req)

    print(f"{data}")
# yfTest()
# from pandas import Timestamp

# dates = data['Datetime']

# stamp: Timestamp = dates[0]
# stamp = stamp.tz_convert(get_localzone_name())
# date  = Timestamp.strftime(stamp, '%Y-%m-%d %X')
# k = datetime.strptime(date, '%Y-%m-%d %X')

# print(f"{k=}")
# print(f"{type(k)}")
# print(f"{stamp.tz_convert(get_localzone_name())} and {stamp=} ")

# date  = Timestamp.strftime(stamp, '%Y-%m-%d %X %z')
# print(f"{date=} and {type(date)=}")

# x = "555"
# if x not in get_args(Interval):
#     print(f"{x} is not in {get_args(Interval)=}")

# db = get_database()
# print(f"{db=}")

def stringTest():
    sting1 = "tsla.smart"

    if sting1 and "." in sting1:
        sting2 = sting1.split('.')[0]
        print(f"{sting2=} is empty")

    else:
        print("not there ")

def load_strategy_class_from_folder(path: Path, module_name: str = "") -> None:
    """
    Load strategy class from certain folder.
    """
    for suffix in ["py", "pyd", "so"]:
        pathname: str = str(path.joinpath(f"*.{suffix}"))
        print(f"{suffix=} and \n {pathname=}")
        # glob() Return a list of paths matching a pathname pattern.
        # The pattern may contain simple shell-style wildcards a la 
        # fnmatch. Unlike fnmatch, filenames starting with a dot are
        #  special cases that are not matched by '*' and '?' patterns
        #  by default.
        for filepath in glob(pathname):
            # stem: The final path component, minus its last suffix.
            # so you get the file name if filepath point to a full path
            # of a file like get 'enngine' for:
            # /Users/z/python/quanttrading/quanttrading/event/engine.py
            filename = Path(filepath).stem
            name: str = f"{module_name}.{filename}"
            print(f"{module_name=} and \n {filename=} and {name=}")
            # load_strategy_class_from_module(name)

def load_strategy_class() -> None:
    """
    Load strategy class from source code.
    """
    path1: Path = Path(__file__).parent.joinpath("event/engine.py")
    load_strategy_class_from_folder(path1, "vnpy_ctastrategy.strategies")

    path2: Path = Path.cwd().joinpath("strategies")
    load_strategy_class_from_folder(path2, "strategies")
    # path1 = str(path1.joinpath("*.py"))
    print(f"{path1.stem=} and {path2=}")
    print(f"{path1.exists()=} and {path2.exists()=}")

# load_strategy_class()

def load_strategy_class_from_module(module_name: str) -> None:
    """
    Load strategy class from module file.
    """
    try:
        classes: dict = {}
        # importlib.import_module(name, package=None)
        # Import a module. The name argument specifies what module to
        #  import in absolute or relative terms (e.g. either pkg.mod 
        # or ..mod). If the name is specified in relative terms, then
        #  the package argument must be set to the name of the package
        #  which is to act as the anchor for resolving the package name
        #  (e.g. import_module('..mod', 'pkg.subpkg') will import pkg.mod).
        module: ModuleType = importlib.import_module(module_name)

        # importlib.reload(module)
        # Reload a previously imported module. The argument must be a
        # module object, so it must have been successfully imported 
        # before. This is useful if you have edited the module source 
        # file using an external editor and want to try out the new 
        # version without leaving the Python interpreter. 
        # The return value is the module object (which can be different
        #  if re-importing causes a different object to be placed in 
        # sys.modules).
        importlib.reload(module)
        print(f"{module.__name__=}")
        for name in dir(module):
            value = getattr(module, name)
            print(f"{name=} and {value=}")
            if (
                isinstance(value, type)
                and issubclass(value, CtaTemplate)
                and value not in {CtaTemplate, TargetPosTemplate}
            ):
                classes[value.__name__] = value
    except:  # noqa
        msg: str = _("策略文件{}加载失败，触发异常：\n{}").format(module_name, traceback.format_exc())
        print(msg)

# load_strategy_class_from_module("utility")

def noneEmptyInObjectTest():
    for risk in RiskLevel:
        print(f"{risk.name=}")

    book = TradeBook("TSLA")
    activeTradeBook: dict[str, TradeBook] = {}

    if not activeTradeBook:
        print(f"activeTradeBook is empty {activeTradeBook}")

    activeTradeBook["TSLA"] = book
    symbol = "TSLA"
    if symbol in activeTradeBook:
        print(f"{activeTradeBook.get(symbol)}")
    else: 
        print(f"{symbol=}")

    contract = symbol if symbol else "IBDE30"

    print(f"{contract=}")

def updateDict():
    _bar_picutures: dict[int, set] = {1:{"name","age"}, 2:{"age"}, 3:{"address"}}

    print(f"{_bar_picutures=}")

    bars = _bar_picutures.get(2)
    bars.add("contact number")
    print(f"{bars=}")
    print(f"{_bar_picutures=}")

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
    zone = get_localzone_name()
    print(f"zone info is {get_localzone_name()}")

    end: datetime = datetime.now(ZoneInfo(get_localzone_name()))

    print(f"{end.strftime("%Y%m%d %H:%M:%S %Z")}")

    start: datetime = end - timedelta(days=500)
    from dateutil import parser
    # date6 = parser.parse("20240718 04:00:00 US/Eastern")
    date6 = datetime.strptime("20240718 04:00:00", "%Y%m%d %H:%M:%S")


    print(f"{date6}")

def timeZone():
    # from datetime import
    from pandas import Timestamp
    stamp = Timestamp('2024-07-25 12:11:00+0100', tz='Europe/London')
    print(f"{stamp=}")
    date = datetime.fromtimestamp(stamp.timestamp())
    print(f"{date=}")

    LOCAL_TZ = ZoneInfo(get_localzone_name())
    print(f"{LOCAL_TZ=}")
    # date = date.astimezone(LOCAL_TZ)
    date = date.replace(tzinfo=LOCAL_TZ)

    print(f"{date=}")


def constructDataframe():
    dt = {'Date':1, 'Open':2, 'High':3, 'Low':4, 'Close':5, 'Volume':6, 'Wap':7, 'Symbol':8, 'Gateway':9}
    data = DataFrame(data=dt,index=[0])
    dt1 = {'Date':2, 'Open':2, 'High':3, 'Low':4, 'Close':5, 'Volume':6, 'Wap':7, 'Symbol':8, 'Gateway':9}
    data1 = DataFrame(data=dt,index=[0])

    data = pd.concat([data, data1], ignore_index=True)

    dt2 = {'Date':3, 'Open':2, 'High':3, 'Low':4, 'Close':5, 'Volume':6, 'Wap':7, 'Symbol':8, 'Gateway':9}
    data2 = DataFrame(data=dt2,index=[0])
    dataDict = {"TSLA":dt, "AAPL":data1}

    data = pd.concat([data, data2], ignore_index=True)
    print(f"{data=}")

    index = data[data['Date'] == data2.at[data2.first_valid_index(), 'Date']].first_valid_index()

    print(f"{index=} and {type(index)}")
    # dataDict.update({"TSLA":data})
    # print(f"{dataDict=}")
    # dtt = DataFrame()
    # dtlist = [[1, 2, 3, 4, 5, 6]]
    # dffromlist = DataFrame(dtlist)
    # print(f"{dffromlist=}")
    # dtt = pd.concat([dtt,dffromlist], ignore_index=True)
    # print(f"{dtt=}")


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