from constant import ChartInterval
import yfinance as yf
import requests_cache

print(f"Interval is {ChartInterval}")
print(f"Interval is {ChartInterval.M1}")
print(f"Interval is {ChartInterval.M1.name}")
print(f"Interval is {ChartInterval.M1.value}")

"""
To use a custom requests session, pass a session= argument to the 
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