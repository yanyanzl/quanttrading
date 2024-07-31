
from datafeed import BaseDatafeed
from datatypes import HistoryRequest, Optional, BarData, TickData, Interval
from typing import Callable, get_args
import yfinance as yf
import logging
import requests_cache
from datetime import timedelta
from utility import getDuration, _wrapBarbyDataFrame
from pandas import DataFrame

logger = logging.getLogger(__name__)


# cache time for the connection sessions
expire_after = timedelta(days=1)

# With caching, the response will be fetched once, saved to cache.sqlite,
# and subsequent requests will return the cached response near-instantly.
csession = requests_cache.CachedSession(
    cache_name="cache",
    backend="sqlite",
    expire_after=expire_after,
    cache_control=True,
)

class YfDatafeed(BaseDatafeed):
    """
    yahoo finance datafeed
    """
    gateway_name = "Yahoo Finance"
    def init(self, output: Callable = print) -> bool:
        """
        Initialize datafeed service connection.
        """
        output(f"{__name__} initiated successfully!")

    def query_bar_history(self, req: HistoryRequest, output: Callable = print) -> Optional[list[BarData]]:
        """
        Query history bar data.
        get the candle stick data for the asset based on the interval, 
        ticker: self.name
        period : str
            Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max Either Use period parameter or use start and end
        interval : str
            Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo Intraday data cannot extend last 60 days
        start: str
            Download start date string (YYYY-MM-DD) or _datetime, inclusive. Default is 99 years ago E.g. for start="2020-01-01", the first data point will be on "2020-01-01"
        end: str
            Download end date string (YYYY-MM-DD) or _datetime, exclusive. Default is now E.g. for end="2023-01-01", the last data point will be on "2022-12-31"
                    symbol=symbol,
                    exchange=exchange,
                    interval=interval,
                    start=start,
                    end=end
        """
        if not req:
            return
        
        try:
            interval = req.interval
            if not interval or interval not in get_args(Interval):
                logger.info(f"{req.interval=} is not valid!")


            if req.start and req.end:
                period = getDuration(req.start, req.end)
            else:
                period = req.duration

            if interval in ['1m', '2m','5m','15m']:
                period = "1d"
            if not period:
                period = "1mo"

            his_price: DataFrame = yf.download(req.symbol, interval=interval,
                                            period=period,
                                            rounding=True, 
                                            session=csession
                                            )
            his_price.reset_index(inplace=True)
            bars = _wrapBarbyDataFrame(his_price, gateway_name=self.gateway_name, symbol=req.symbol, interval=interval)

            return bars
        except Exception as e:
            logger.warning(f"can't get data. {e=} for {req.symbol} for interval {interval} and period: {period}")
            return None

    def query_tick_history(self, req: HistoryRequest, output: Callable = print) -> Optional[list[TickData]]:
        """
        Query history tick data. 
        """

        bars = self.query_bar_history(req, output)
        ticks: list[TickData] = []
        for bar in bars:
            
            tick: TickData = TickData(bar.gateway_name, bar.symbol, bar.exchange, bar.datetime, "")
            tick.volume = bar.volume
            tick.last_price = bar.close_price
            ticks.append(tick)
        return ticks
