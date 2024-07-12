from constant import ChartInterval
import yfinance as yf
import requests_cache
from data.finlib import Asset
from constant import ChartInterval, ChartPeriod
from utility import volumeToPicture

y = volumeToPicture(25678900, 3)
print(f"y = {y}")
i = 2567890
n = i // 10
m = i / 10
k = str(i)
k = k[0]+"."+k[1:]
k = float(k)

print(f"n = {n} and m = {m} and k is {k} and type of k is {type(k)}")

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