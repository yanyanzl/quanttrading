"""
Technical analysis
technical indicators. signals.
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
import requests_cache
from typing import get_args

from .base import TickerData, TICKER_DATA_KEYS
from datatypes import Minutes_DAYS

__all__ = ["TechAnalysis"]

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

class TechAnalysis(object):

    def __init__(self, symbol:str) -> None:
        """
        Technical analysis class to get technical indicators.
        symbol is the target to be analysed. Like: TSLA for Tesla, 
        AAPL for Apple.
        you can change it by call setSymbol() method
        """
        self._symbol = symbol
        self.ticker = yf.Ticker(symbol)
        self.isValid = True
        self.getBasicInfo()

    def getBasicInfo(self) -> TickerData|None:
        """ 
        get the basic infomation for the ticker
        "dayLow", "dayHigh", "lastPrice","fiftyDayAverage",
        "twoHundredDayAverage", "marketCap", "shares", "currency",
        "lastVolume","tenDayAverageVolume","threeMonthAverageVolume",
        "yearHigh", "yearLow", "yearChange"
        """
        try:
            tickerData = TickerData({"symbol":self._symbol})
            basic_info:dict = self.ticker.basic_info
            for info in basic_info.keys():
                if info in TICKER_DATA_KEYS:
                    tickerData[info] = basic_info[info]
            return tickerData
        except Exception as e:
            logger.info(f"invalid symbol.{self._symbol} can't get info")
            self.isValid = False
            return None
    
    def setSymbol(self, symbol:str) -> bool:
        """
        change the symbol of the TechAnalysis
        return True if the symbol exist and setted.
        otherwise return False
        """
        if symbol:
            self._symbol = symbol
            self.ticker = yf.Ticker(symbol)
            self.getBasicInfo()
            return self.isValid
        else:
            logger.info(f"invalid symbol.{symbol}")
            return False
        
    @staticmethod
    def true_range_by_datas(high:float, low:float, pervious_close:float) -> float:
        """
        single period true range.
        True Range =  max[(high -low), abs(high - previous close),
        abs (low - previous close)
        """
        if high and low and pervious_close and high >= low:
            return max((high-low), abs(high-pervious_close), abs(low-pervious_close))
        return 0


    def ATR_minite_summary(self, period:int=14, days:Minutes_DAYS = "5d", hours:int = 7, count:int = 6) -> dict[datetime, list]:
        """
        Valid days: 1d,5d. get result for last 1 day or 5 days.
        valid hours: 1 to 7. get result for the last 1 hour or up to 7 hours.
        count: valid 1 to 60 - period. number of ATRs per hour to be returned.
        return datetime to the list of ATRs for that time range (per hour)
        """
        assert days in get_args(Minutes_DAYS)
        if hours < 1 or hours > 7:
            hours = 7
        
        data = self.ticker.history(period=days, interval="1m")

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
                ATR_summary.update({last_hour - timedelta(hours=1+j): self.ATR_by_datas(high, low, close, period)})
            
        print(f"{ATR_summary}")

    @classmethod
    def ATR_by_datas(cls, high:pd.Series, low:pd.Series, close:pd.Series, period:int=14) -> list[float]:
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

                true_range = cls.true_range_by_datas(high[i], low[i],close[i-1])

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
