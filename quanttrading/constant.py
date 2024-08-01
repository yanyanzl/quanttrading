"""
General constant enums used in the trading platform.
"""

from enum import Enum
from typing import List

# from .locale import _

LOCAL_TZ = ZoneInfo(get_localzone_name())
def _(name):
    """
    use _() as a function to translate the locale.
    could be replaced by locale in the future when needed.
    """
    return str(name)


class ChartInterval(Enum):
    """
    interval for the chart candles.
    1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo Intraday data cannot extend last 60 days
    """
    S1 = "1s"
    M1 = "1m"
    M5 = "5m"
    # M10 = "10"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    # H4 = "1d"
    D1 = "1d"
    W1 = "1Wk"

    @staticmethod
    def values() -> List[str]:
        return ["1s", "1m", "5m", "15m", "30m", "1h", "1d", "1wk"]

def stringToInterval(value:str) -> ChartInterval:
    if value == "1s":
        return ChartInterval.S1
    elif value == "1m":
        return ChartInterval.M1
    elif value == "5m":
        return ChartInterval.M5
    elif value == "15m":
        return ChartInterval.M15
    elif value == "30m":
        return ChartInterval.M30
    elif value == "1h":
        return ChartInterval.H1
    elif value == "1d":
        return ChartInterval.D1
    elif value == "1wk":
        return ChartInterval.W1
    else:
        return ChartInterval.D1

class ChartPeriod(Enum):
    """
    the period for the chart candles.
    Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd, max Either Use period parameter or use start and end
    """
    D1 = "1d"
    D5 = "5d"
    M1 = "1mo"
    M3 = "3mo"
    M6 = "6mo"
    Y1 = "1y"
    Y2 = "2y"
    Y5 = "5y"
    y10 = "10y"
    MAX = "max"


"""
Event type string used in the trading platform.
"""

EVENT_TICK = "eTick."
EVENT_TRADE = "eTrade."
EVENT_ORDER = "eOrder."
EVENT_POSITION = "ePosition."
EVENT_ACCOUNT = "eAccount."
EVENT_QUOTE = "eQuote."
EVENT_CONTRACT = "eContract."
EVENT_LOG = "eLog"
EVENT_TIMER = "eTimer"
EVENT_HISDATA = "eHisotryData"
EVENT_HISDATA_UPDATE = "eHistoryDataUpdate"
EVENT_REALTIME_DATA = "eRealtimeData"
EVENT_TICK_LAST_DATA = "eTickLastData"
EVENT_TICK_BIDASK_DATA = "eTickBidAskData"
EVENT_PORTFOLIO = "ePortfolio"
EVENT_ORDER_STATUS = "eOrderStatus"
EVENT_OPEN_ORDER = "eOpenOrder"

class RiskLevel(Enum):
    """
    risk levels
    """
    LevelZero = 0
    LevelNormal = 1
    LevelWarning = 2
    LevelCritical = 3

class Direction(Enum):
    """
    Direction of order/trade/position.
    """
    LONG = _("多")
    SHORT = _("空")
    NET = _("净")


class Offset(Enum):
    """
    Offset of order/trade.
    """
    NONE = ""
    OPEN = _("开")
    CLOSE = _("平")
    CLOSETODAY = _("平今")
    CLOSEYESTERDAY = _("平昨")
    COVER = "cover"


class Status(Enum):
    """
    Order status.
    """
    SUBMITTING = _("提交中")
    NOTTRADED = _("未成交")
    PARTTRADED = _("部分成交")
    ALLTRADED = _("全部成交")
    CANCELLED = _("已撤销")
    REJECTED = _("拒单")


class Product(Enum):
    """
    Product class.
    """
    EQUITY = _("股票")
    FUTURES = _("期货")
    OPTION = _("期权")
    INDEX = _("指数")
    FOREX = _("外汇")
    SPOT = _("现货")
    ETF = "ETF"
    BOND = _("债券")
    WARRANT = _("权证")
    SPREAD = _("价差")
    FUND = _("基金")
    CFD = "CFD"
    SWAP = _("互换")


class OrderType(Enum):
    """
    Order type.
    """
    LIMIT = _("限价")
    MARKET = _("市价")
    STOP = "STOP"
    FAK = "FAK"
    FOK = "FOK"
    RFQ = _("询价")


class OptionType(Enum):
    """
    Option type.
    """
    CALL = _("看涨期权")
    PUT = _("看跌期权")


class Exchange(Enum):
    """
    Exchange.
    """
    # Chinese
    CFFEX = "CFFEX"         # China Financial Futures Exchange
    SHFE = "SHFE"           # Shanghai Futures Exchange
    CZCE = "CZCE"           # Zhengzhou Commodity Exchange
    DCE = "DCE"             # Dalian Commodity Exchange
    INE = "INE"             # Shanghai International Energy Exchange
    GFEX = "GFEX"           # Guangzhou Futures Exchange
    SSE = "SSE"             # Shanghai Stock Exchange
    SZSE = "SZSE"           # Shenzhen Stock Exchange
    BSE = "BSE"             # Beijing Stock Exchange
    SHHK = "SHHK"           # Shanghai-HK Stock Connect
    SZHK = "SZHK"           # Shenzhen-HK Stock Connect
    SGE = "SGE"             # Shanghai Gold Exchange
    WXE = "WXE"             # Wuxi Steel Exchange
    CFETS = "CFETS"         # CFETS Bond Market Maker Trading System
    XBOND = "XBOND"         # CFETS X-Bond Anonymous Trading System

    # Global
    SMART = "SMART"         # Smart Router for US stocks
    NYSE = "NYSE"           # New York Stock Exchnage
    NASDAQ = "NASDAQ"       # Nasdaq Exchange
    ARCA = "ARCA"           # ARCA Exchange
    EDGEA = "EDGEA"         # Direct Edge Exchange
    ISLAND = "ISLAND"       # Nasdaq Island ECN
    BATS = "BATS"           # Bats Global Markets
    IEX = "IEX"             # The Investors Exchange
    AMEX = "AMEX"           # American Stock Exchange
    TSE = "TSE"             # Toronto Stock Exchange
    NYMEX = "NYMEX"         # New York Mercantile Exchange
    COMEX = "COMEX"         # COMEX of CME
    GLOBEX = "GLOBEX"       # Globex of CME
    IDEALPRO = "IDEALPRO"   # Forex ECN of Interactive Brokers
    CME = "CME"             # Chicago Mercantile Exchange
    ICE = "ICE"             # Intercontinental Exchange
    SEHK = "SEHK"           # Stock Exchange of Hong Kong
    HKFE = "HKFE"           # Hong Kong Futures Exchange
    SGX = "SGX"             # Singapore Global Exchange
    CBOT = "CBT"            # Chicago Board of Trade
    CBOE = "CBOE"           # Chicago Board Options Exchange
    CFE = "CFE"             # CBOE Futures Exchange
    DME = "DME"             # Dubai Mercantile Exchange
    EUREX = "EUX"           # Eurex Exchange
    APEX = "APEX"           # Asia Pacific Exchange
    LME = "LME"             # London Metal Exchange
    BMD = "BMD"             # Bursa Malaysia Derivatives
    TOCOM = "TOCOM"         # Tokyo Commodity Exchange
    EUNX = "EUNX"           # Euronext Exchange
    KRX = "KRX"             # Korean Exchange
    OTC = "OTC"             # OTC Product (Forex/CFD/Pink Sheet Equity)
    IBKRATS = "IBKRATS"     # Paper Trading Exchange of IB
    IBIS = "IBIS"           # for Europe
    LSE = "LSE"             # for UK

    # Special Function
    LOCAL = "LOCAL"         # For local generated data


class Currency(Enum):
    """
    Currency.
    """
    USD = "USD"
    HKD = "HKD"
    CNY = "CNY"
    CAD = "CAD"


class Interval(Enum):
    """
    Interval of bar data.
    """
    MINUTE = "1m"
    HOUR = "1h"
    DAILY = "d"
    WEEKLY = "w"
    TICK = "tick"
