"""
Basic data structure used for general trading function in the trading platform.
define all types of data object in this module

"""
import logging
import sys
# from abc import ABC
# from pathlib import Path

# import sys
# from typing import Union, List, Optional, Any as PythonAny


if sys.version_info.minor >= 8:
    from typing import TypedDict, Literal, Dict
else:
    from typing import Dict
    from typing_extensions import Literal
    TypedDict = Dict

if sys.version_info.minor >= 11:
    from typing import NotRequired
else:
    from typing_extensions import NotRequired


TICKER_DATA_KEYS:list = ["symbol", "dayLow", "dayHigh", "lastPrice",
                         "fiftyDayAverage","twoHundredDayAverage",
                           "marketCap", "shares", "currency", "lastVolume",
                             "tenDayAverageVolume", "threeMonthAverageVolume",
                               "yearHigh", "yearLow", "yearChange"
                               ]
class TickerData(TypedDict):
    symbol:str
    dayLow:float = 0
    dayHigh:float = 0
    lastPrice: float = 0
    fiftyDayAverage:float = 0
    twoHundredDayAverage:float = 0
    marketCap: float = 0
    shares: int|float = 0
    currency:str = "USD"
    lastVolume: int|float = 0
    tenDayAverageVolume: int|float = 0
    threeMonthAverageVolume: int|float = 0
    yearHigh:float = 0
    yearLow:float =0
    yearChange:float = 0.0