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
from datatypes import Minutes_DAYS, TickData

# __all__ = ["TechAnalysis, TickManager, "]

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

def true_range_by_datas(high:float, low:float, pervious_close:float) -> float:
    """
    single period true range.
    True Range =  max[(high -low), abs(high - previous close),
    abs (low - previous close)
    """
    if high and low and pervious_close and high >= low:
        return max((high-low), abs(high-pervious_close), abs(low-pervious_close))
    return 0

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

            true_range = true_range_by_datas(high[i], low[i],close[i-1])

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
            # print(f"current_data: {current_data}")
            # skip those non-trading days.
            if current_data.empty:
                continue
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
                # print(f"{close=}")
                ATR_summary.update({last_hour - timedelta(hours=1+j): ATR_by_datas(high, low, close, period)})

        # print(f"{ATR_summary}")
        return ATR_summary
    
    def ATR_days(self, period:int=14, startDate:str = None) -> float:
        """
        Average True Range for days range. 

        :Valid period (int), 2 to 90.
        :start date string (YYYY-MM-DD), E.g. for start="2020-01-01", 
            the first data point will be on "2020-01-01". default 
            start from "period" days ago.
        :return ATR for the previous period of time.
        """
        
        data = self.ticker.history(period="3mo", start=startDate, interval="1d")
        data.reset_index(inplace=True)

        num = round(period*9/7)
        data = data.loc[0:num]
        # last_date:pd.Timestamp = data.loc[data.last_valid_index()].name.replace(hour=23)
        ATR_summary:list = []

        # hour_data = hour_data.loc[0:num]

        close = data["Close"]
        high = data["High"]
        low = data["Low"]
        ATR_summary = ATR_by_datas(high, low, close, period)
        if ATR_summary is not None and len(ATR_summary) > 0:
            return ATR_summary[0]
        else:
            return 0


class TickManager(object):
    """
    For:
    1. calculating technical indicator value for ticks
    2. currently support RSI, ATR (Average True Range)
    """

    def __init__(self, size: int = 200, min_move_range:float=0.1) -> None:
        """
        tick data manager. to generate indicators. around
        20 ticks per second generated by the market.
        size: is the ticks will be saved for the tickmanager
        minimum:200
        min_move_range is the range the price moving will trigger the 
        indicators. like rsi. 
        """
        self.count: int = 0
        if size < 200:
            size = 200
        self.size: int = size
        self.inited: bool = False

        self.min_move_relative:float = 1/1000
        self.min_move_range: float = min_move_range

        self.ticks_array: np.ndarray = np.zeros(size)

        self.atr_hisdata:list = []
        self.atr_inited:bool = False

    def on_tick(self, tick: TickData) -> None:
        """
        Update new tick data into tick manager.
        """
        if tick and tick.last_price and tick.last_price > 0:
            self.count += 1
            if not self.inited and self.count >= self.size:
                self.inited = True

            self.ticks_array[:-1] = self.ticks_array[1:]

            self.ticks_array[-1] = tick.last_price

    def rsi(self, rsi_window:int) -> float:
        """
        calculate the rsi for the specified rsi_window.
        """
        result = None
        if self.ticks_array[0]:
            move_range = self.min_move_relative * self.ticks_array[0]
            move_range = max(self.min_move_range, move_range)
        else:
            move_range = self.min_move_range

        if self.inited:
            result = 50
            start = max(0, self.size-rsi_window)
            delta = np.diff(self.ticks_array[start:])
            delta  = delta[1:]
            # print(f"start:{start}, array is {self.ticks_array[start:]} \n delta={delta}")
            up, down = delta.clip(min=0), delta.clip(max=0)
            up, down = up[up!=0], down[down!=0]

            # print(f"{up.any()}, {up.all()}, {down.any()}, {down.all()}")

            # price not moving (up or down). return.
            if not up.any() and not down.any():
                return None
            
            # no upward moving for the past period.
            elif not up.any():
                down_range = down.sum()
                if abs(down_range) >= move_range:
                    return 10
                else:
                    return 50
            
            # no downward moving for the past period.
            elif not down.any():
                up_range = up.sum()
                # print(f"uprange is {up_range} and up is {up}, {move_range=}")
                if up_range >= move_range:
                    return 90
                else:
                    return 50
            
            converge_range = abs(up.sum() - abs(down.sum()))
            if converge_range >= move_range:

                roll_up, roll_down = np.average(up), np.average(down)
                # roll_up, roll_down = np.nanmean(up), np.nanmean(down)
                # print(f"roll_up is {roll_up} and \n roll_down is {roll_down}")
                rs = roll_up/abs(roll_down)
                result = 100.0 - (100.0 / (1.0 + rs))
            else:
                result = 50

            if np.isnan(result):
                result = None

        return result
    
    def atr(self, period:int = 14, ticks_num:int=100) -> float:
        """
        average True range. tick wise. around 20 ticks/second
        so ticks_num = 200 means around 10 seconds
        """

        if not ticks_num or ticks_num > self.size or ticks_num < 0:
            ticks_num = self.size
        
        ticks = self.ticks_array[-ticks_num:]
        true_range = ticks.max() - ticks.min()
        self.atr_hisdata.append(true_range)
        
        if len(self.atr_hisdata) > period:
            self.atr_hisdata = self.atr_hisdata[-period:]

        total = sum(self.atr_hisdata)
        average_num = total/len(self.atr_hisdata)
        return average_num

    def realRange(self, ticks_num:int = 20, period_num:int = 5) -> float:
        """ to be improved....
        calculate the real price moving range in the last period_num
        periods.
        ticks_num is the number of ticks that moved the range.
        period_num is used to average the range in those periods so to
        have a smooth range.
        ticks_num * period_num should <= size of the Tickmanager.
        otherwise, will return the max num of ticks_num's average based on
        the full size of the tick manager.
        """

        real_ranges:np.ndarray = np.zeros(period_num)
        periods = 0

        for i in range(0, self.size, ticks_num):
            end_index = self.size - i
            up, down = self.up_and_downs(ticks_num, end_index)
            # print(f"{up=} and {down=}")

            # price moving up and down.
            if up.any() and down.any():
                real_ranges[periods] = (up.sum() - abs(down.sum()))
            
            # no upward moving for the past ticks_num.
            elif not up.any():
                real_ranges[periods] = down.sum()
            
            # no downward moving for the past ticks_num.
            elif not down.any():
                real_ranges[periods] = up.sum()
            
            periods += 1
            if periods >= period_num:
                break
        
        # print(f"{real_ranges=}")
        real_range = (real_ranges.sum() / periods)
        del up, down
        return real_range
    

    def up_and_downs(self, range:int, end_index:int = -1) -> tuple[np.ndarray,np.ndarray]:
        """
        list of price ups and price downs in the last range ticks
        end_index: end index of the ticks in self.ticks_array.
        default -1, will start from the last index. 
        """
        if self.inited and end_index >= -1:
            if end_index == -1:
                end_index = self.size

            start = max(0, end_index-range)

            delta = np.diff(self.ticks_array[start:end_index])
            delta  = delta[1:]
            # print(f"start:{start}, array is {self.ticks_array[start:]} \n delta={delta}")
            up, down = delta.clip(min=0), delta.clip(max=0)
            up, down = up[up!=0], down[down!=0]
            return up, down
        else:
            return np.zeros(1),np.zeros(1)