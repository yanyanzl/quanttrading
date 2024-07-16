import logging.handlers
from constant import ChartInterval
import yfinance as yf
import requests_cache
from data.finlib import Asset
from constant import ChartInterval, ChartPeriod
from utility import volumeToPicture

import logging
from datetime import datetime
import os

print(f"equal {"abc" != "abcd"}")

def logTest():
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    logger.info('Started')
    print("this is the somthing")
    logger.info('Finished')

def setUpLogger(loggingLevel) ->str:
    """
    set up the logger for the whole programme.
    loggingLevel could be :
    logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL
    """
    # same path as utility
    fh = logging.FileHandler(_getLogFileName())
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    handlers = [fh, ch]
    logging.basicConfig(handlers=handlers, level=loggingLevel)

def _getLogFileName() -> str:
    timestring = datetime.now().strftime("%Y-%m-%d-%H")
    return os.path.dirname(os.path.abspath(__file__)) + '/log/' + 'quanttrading'+timestring+'.log'

def getLogger(name:str) -> logging.Logger:
    logger = logging.getLogger(name)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(_getLogFileName())
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    # ch.setLevel(logging.ERROR)
    # create formatter and add it to the handlers
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # fh.setFormatter(formatter)
    # ch.setFormatter(formatter)
    # add the handlers to the logger

    # logger.addHandler(fh)
    # logger.addHandler(ch)
    logger.info('Started')
    return logger

setUpLogger(logging.INFO)
# getLogger(__name__)
logger = logging.getLogger(__name__)
logger.info("this is the correct one!")

def intTofloat():
    y = volumeToPicture(25678900, 3)
    print(f"y = {y}")
    i = 2567890
    n = i // 10
    m = i / 10
    k = str(i)
    k = k[0]+"."+k[1:]
    k = float(k)

    print(f"n = {n} and m = {m} and k is {k} and type of k is {type(k)}")

    print(f"3.0 >= 2 is {int(3.3)}")

def assetTest():
    asset = Asset("TSLA")
    print(f"asset is {asset}")
    data = asset.getMarketData(ChartInterval.M15, ChartPeriod.D5)
    data.reset_index(inplace=True)
    print(f"self._data is \n {data.index}")
    print(f"self._data is \n {data.columns}")
    data.rename(columns={"Datetime":"Date"}, inplace=True)
    print(f"self._data is \n {data}")
    data.rename(columns={"Datetime":"Date"}, inplace=True)
    print(f"self._data is \n {data}")

    min = data['Volume'].min()
    max = data['Volume'].max()

    print(f"min is {min} \n max is {max}")

ac = None
if not ac:
    print("ac is None!!!")
    
print(f"Interval is {ChartInterval}")
print(f"Interval is {ChartInterval.M1}")
print(f"Interval is {ChartInterval.M1.name}")
print(f"Interval is {ChartInterval.M1.value}")

print(f"M1.value is in {ChartInterval.M1.value in ["1s", "1m", "5m", "15m", "30m", "1h"]}")


"""
To use a custom requests session, pass a session= argum.ent to the 
Ticker constructor. This allows for caching calls to the API as well 
as a custom way to modify requests via the User-agent header.

or Combine requests_cache with rate-limiting to avoid 
triggering Yahoo's rate-limiter/blocker that can corrupt data.

from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter
class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass

session = CachedLimiterSession(
    limiter=Limiter(RequestRate(2, Duration.SECOND*5)),  # max 2 requests per 5 seconds
    bucket_class=MemoryQueueBucket,
    backend=SQLiteCache("yfinance.cache"),
)
"""
def sessionTest():
    session = requests_cache.CachedSession('yfinance.cache')
    session.headers['User-agent'] = 'my-program/1.0'

    msft = yf.Ticker("MSFT", session=session)

    # get all stock info
    print(f"info is {msft}")

    # get historical market data
    hist = msft.history(period="1mo",)

    print(f"hist is {hist}")


    ticker = yf.Ticker('msft', session=session)
    # The scraped response will be stored in the cache
    print(f"ticker.actions is {ticker.actions}")