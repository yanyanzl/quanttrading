"""
Basic data structure used for general trading function in the trading platform.
define all types of data object in this module

"""
from PySide6 import QtGui
from dataclasses import dataclass, field
from datetime import datetime
from logging import INFO
from abc import ABC
from pathlib import Path
from typing import Type, TYPE_CHECKING
import sys
# import types
from typing import Union, List, Optional, Any as PythonAny
from decimal import Decimal

from constant import Direction, Exchange, Offset, Status, Product, OptionType, OrderType

ACTIVE_STATUSES = set([Status.SUBMITTING, Status.NOTTRADED, Status.PARTTRADED])


if TYPE_CHECKING:
    from .ordermanagement import BaseManagement

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


OrderSide = Literal['buy', 'sell']
# OrderType = Literal['limit', 'market']
PositionSide = Literal['long', 'short']
Any = PythonAny

IndexType = Union[str, int]
Num = Union[None, str, float, int, Decimal]
Str = Optional[str]
Strings = Optional[List[str]]
Int = Optional[int]
Bool = Optional[bool]
MarketType = Literal['spot', 'margin', 'swap', 'future', 'option']
SubType = Literal['linear', 'inverse']
Interval = Literal["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "1wk"]


class FeeInterface(TypedDict):
    currency: Str
    cost: Num
    rate: NotRequired[Num]


Fee = Optional[FeeInterface]


class Balance(TypedDict):
    free: Num
    used: Num
    total: Num
    debt: NotRequired[Num]

class BalanceAccount(TypedDict):
    free: Str
    used: Str
    total: Str

class Account(TypedDict):
    id: Str
    reqId: Str
    code: Str
    accountValue: Dict[str, list[str,str]] = {}
    # any information for the account.
    info: Dict[str, Any]

class Ticker(TypedDict):
    info: Dict[str, Any]
    symbol: Str
    timestamp: Int
    datetime: Str
    high: Num
    low: Num
    bid: Num
    bidVolume: Num
    ask: Num
    askVolume: Num
    vwap: Num
    open: Num
    close: Num
    last: Num
    previousClose: Num
    change: Num
    percentage: Num
    average: Num
    quoteVolume: Num
    baseVolume: Num


Tickers = Dict[str, Ticker]


class BaseApp(ABC):
    """
    Absstract class for app.
    """

    app_name: str = ""                          # Unique name used for creating engine and widget
    app_module: str = ""                        # App module string used in import_module
    app_path: Path = ""                         # Absolute path of app folder
    display_name: str = ""                      # Name for display on the menu.
    engine_class: Type["BaseManagement"] = None     # App management class
    widget_name: str = ""                       # Class name of app widget
    icon_name: str = ""                         # Icon file name of app widget


@dataclass
class BaseData:
    """
    Any data object needs a gateway_name as source
    and should inherit base data.
    """
    gateway_name: str

    extra: dict = field(default=None, init=False)


@dataclass
class TickData(BaseData):
    """
    Tick data contains information about:
        * last trade in market
        * orderbook snapshot
        * intraday market statistics.
    """

    symbol: str
    exchange: Exchange
    datetime: datetime

    name: str = ""
    volume: float = 0
    turnover: float = 0
    open_interest: float = 0
    last_price: float = 0
    last_volume: float = 0
    limit_up: float = 0
    limit_down: float = 0

    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    pre_close: float = 0

    bid_price_1: float = 0
    bid_price_2: float = 0
    bid_price_3: float = 0
    bid_price_4: float = 0
    bid_price_5: float = 0

    ask_price_1: float = 0
    ask_price_2: float = 0
    ask_price_3: float = 0
    ask_price_4: float = 0
    ask_price_5: float = 0

    bid_volume_1: float = 0
    bid_volume_2: float = 0
    bid_volume_3: float = 0
    bid_volume_4: float = 0
    bid_volume_5: float = 0

    ask_volume_1: float = 0
    ask_volume_2: float = 0
    ask_volume_3: float = 0
    ask_volume_4: float = 0
    ask_volume_5: float = 0

    localtime: datetime = None

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"

@dataclass
class CandleData(BaseData):
    """
    Candlestick bar data of a certain trading period.
    """

    symbol: str
    exchange: Exchange
    datetime: datetime

    interval: Interval = None
    volume: float = 0
    turnover: float = 0
    open_interest: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0
    wap: float = 0
    barcount = 0

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"

@dataclass
class BarData(BaseData):
    """
    Candlestick bar data of a certain trading period.
    """

    symbol: str
    exchange: Exchange
    datetime: datetime

    interval: Interval = None
    volume: float = 0
    turnover: float = 0
    open_interest: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderData(BaseData):
    """
    Order data contains information for tracking lastest status
    of a specific order.
    """

    symbol: str
    exchange: Exchange
    orderid: str

    type: OrderType = OrderType.LIMIT
    direction: Direction = None
    offset: Offset = Offset.NONE
    price: float = 0
    volume: float = 0
    traded: float = 0
    status: Status = Status.SUBMITTING
    datetime: datetime = None
    reference: str = ""

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid: str = f"{self.gateway_name}.{self.orderid}"

    def is_active(self) -> bool:
        """
        Check if the order is active.
        """
        return self.status in ACTIVE_STATUSES

    def create_cancel_request(self) -> "CancelRequest":
        """
        Create cancel request object from order.
        """
        req: CancelRequest = CancelRequest(
            orderid=self.orderid, symbol=self.symbol, exchange=self.exchange
        )
        return req


@dataclass
class TradeData(BaseData):
    """
    Trade data contains information of a fill of an order. One order
    can have several trade fills.
    """

    symbol: str
    exchange: Exchange
    orderid: str
    tradeid: str
    direction: Direction = None

    offset: Offset = Offset.NONE
    price: float = 0
    volume: float = 0
    datetime: datetime = None
    symbolName: str = ""

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid: str = f"{self.gateway_name}.{self.orderid}"
        self.vt_tradeid: str = f"{self.gateway_name}.{self.tradeid}"


@dataclass
class PositionData(BaseData):
    """
    Position data is used for tracking each individual position holding.
    """

    symbol: str
    exchange: Exchange
    direction: Direction

    volume: float = 0
    frozen: float = 0
    price: float = 0
    pnl: float = 0
    yd_volume: float = 0
    symbolName: str = ""
    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"
        self.vt_positionid: str = f"{self.gateway_name}.{self.vt_symbol}.{self.direction.value}"


@dataclass
class AccountData(BaseData):
    """
    Account data contains information about balance, frozen and
    available.
    """

    accountid: str

    balance: float = 0
    frozen: float = 0

    def __post_init__(self) -> None:
        """"""
        self.available: float = self.balance - self.frozen
        self.vt_accountid: str = f"{self.gateway_name}.{self.accountid}"


@dataclass
class LogData(BaseData):
    """
    Log data is used for recording log messages on GUI or in log files.
    """

    msg: str
    level: int = INFO

    def __post_init__(self) -> None:
        """"""
        self.time: datetime = datetime.now()


@dataclass
class ContractData(BaseData):
    """
    Contract data contains basic information about each contract traded.
    """

    symbol: str
    exchange: Exchange
    name: str
    product: Product
    size: float
    pricetick: float

    min_volume: float = 1           # minimum trading volume of the contract
    stop_supported: bool = False    # whether server supports stop order
    net_position: bool = False      # whether gateway uses net position volume
    history_data: bool = False      # whether gateway provides bar history data

    option_strike: float = 0
    option_underlying: str = ""     # vt_symbol of underlying contract
    option_type: OptionType = None
    option_listed: datetime = None
    option_expiry: datetime = None
    option_portfolio: str = ""
    option_index: str = ""          # for identifying options with same strike price
    symbolName: str = ""

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class QuoteData(BaseData):
    """
    Quote data contains information for tracking lastest status
    of a specific quote.
    """

    symbol: str
    exchange: Exchange
    quoteid: str

    bid_price: float = 0.0
    bid_volume: int = 0
    ask_price: float = 0.0
    ask_volume: int = 0
    bid_offset: Offset = Offset.NONE
    ask_offset: Offset = Offset.NONE
    status: Status = Status.SUBMITTING
    datetime: datetime = None
    reference: str = ""

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"
        self.vt_quoteid: str = f"{self.gateway_name}.{self.quoteid}"

    def is_active(self) -> bool:
        """
        Check if the quote is active.
        """
        return self.status in ACTIVE_STATUSES

    def create_cancel_request(self) -> "CancelRequest":
        """
        Create cancel request object from quote.
        """
        req: CancelRequest = CancelRequest(
            orderid=self.quoteid, symbol=self.symbol, exchange=self.exchange
        )
        return req


@dataclass
class SubscribeRequest:
    """
    Request sending to specific gateway for subscribing tick data update.
    """

    symbol: str
    exchange: Exchange
    tickType: Literal['Last', 'AllLast', 'BidAsk', 'MidPoint'] = "AllLast"
    realTime: bool = True  # real time market data or not.

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderRequest:
    """
    Request sending to specific gateway for creating a new order.
    """

    symbol: str
    exchange: Exchange
    direction: Direction
    type: OrderType
    volume: float
    price: float = 0
    offset: Offset = Offset.NONE
    reference: str = ""

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"

    def create_order_data(self, orderid: str, gateway_name: str) -> OrderData:
        """
        Create order data from request.
        """
        order: OrderData = OrderData(
            symbol=self.symbol,
            exchange=self.exchange,
            orderid=orderid,
            type=self.type,
            direction=self.direction,
            offset=self.offset,
            price=self.price,
            volume=self.volume,
            reference=self.reference,
            gateway_name=gateway_name,
        )
        return order


@dataclass
class CancelRequest:
    """
    Request sending to specific gateway for canceling an existing order.
    """

    orderid: str
    symbol: str
    exchange: Exchange

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class HistoryRequest:
    """
    Request sending to specific gateway for querying history data.
    """

    symbol: str
    exchange: Exchange
    start: datetime = None
    end: datetime = None
    duration: str = ""
    interval: Interval = None
    keepUpdate: bool = False
    useRTH: bool = False

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class QuoteRequest:
    """
    Request sending to specific gateway for creating a new quote.
    """

    symbol: str
    exchange: Exchange
    bid_price: float
    bid_volume: int
    ask_price: float
    ask_volume: int
    bid_offset: Offset = Offset.NONE
    ask_offset: Offset = Offset.NONE
    reference: str = ""

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"

    def create_quote_data(self, quoteid: str, gateway_name: str) -> QuoteData:
        """
        Create quote data from request.
        """
        quote: QuoteData = QuoteData(
            symbol=self.symbol,
            exchange=self.exchange,
            quoteid=quoteid,
            bid_price=self.bid_price,
            bid_volume=self.bid_volume,
            ask_price=self.ask_price,
            ask_volume=self.ask_volume,
            bid_offset=self.bid_offset,
            ask_offset=self.ask_offset,
            reference=self.reference,
            gateway_name=gateway_name,
        )
        return quote


class TradeBook:
    """
    long/short trades for a single symbol
    the trade.symbolName should be same as the
    tradeBook's vt_symbol
    calculate the PnL based on the trades
    """

    def __init__(self, vt_symbol: str) -> None:
        """"""
        self.vt_symbol: str = vt_symbol

        # long position size * price
        self.long_cost:float  = 0

        # short position size * price
        self.short_cost: float = 0

        self.long_size: int = 0

        self.short_size: int = 0

        self.exchange: Exchange = None
        self.gateway_name: str = ""

        # the realised pnl for this symbol. 
        # positive for profit. negative for loss
        self.realised_pnl = 0

        # the total pnl for this symbol. 
        # positive for profit. negative for loss
        self.total_pnl = 0

        self.cover_req: OrderRequest = None

    def update_trades(self, trade: TradeData) -> None:
        """update the trades information."""
        if trade is not None and isinstance(trade, TradeData) and trade.symbolName == self.vt_symbol:
            self.exchange = trade.exchange
            self.gateway_name = trade.gateway_name

            if trade.direction == Direction.LONG:
                self.long_size += trade.volume
                self.long_cost += (trade.volume * trade.price)
            else:
                self.short_size += trade.volume
                self.short_cost += (trade.volume * trade.price)
            
            self.total_pnl = (trade.price * self.long_size - self.long_cost) + (self.short_cost - trade.price * self.short_size)
            if self.long_size >= self.short_size > 0:
                self.realised_pnl = self.short_size * (self.short_cost/self.short_size - self.long_cost/self.long_size)
            elif self.short_size > self.long_size > 0:
                self.realised_pnl = self.long_size * (self.short_cost/self.short_size - self.long_cost/self.long_size)

    def on_tick(self, tick:TickData) -> None:
        """
        update the pnl based on the tickdata.
        """
        
        self.total_pnl = (tick.last_price * self.long_size - self.long_cost) + (self.short_cost - tick.last_price * self.short_size)
        return
    
    def create_cover_req(self) -> OrderRequest:
        """
        creating a orderrequest to cover all the outstanding postion for this symbol
        if no outstanding position. Return None
        cover by a Market order by default. can only creat once
        """
        print(f"{self.vt_symbol=} and {self.exchange=}, {self.long_size=} and {self.short_size=}")
        if not self.vt_symbol or not self.exchange:
            return
        
        if self.long_size == self.short_size:
            return
        
        if self.cover_req:
            return
        
        direction = Direction.LONG
        volume = self.long_size - self.short_size
        if volume > 0:
            direction = Direction.SHORT
        self.cover_req = OrderRequest(self.vt_symbol, self.exchange, direction, OrderType.MARKET, abs(volume), offset=Offset.COVER)
        return self.cover_req


class Validator(QtGui.QValidator):
    def validate(self, string:str, pos):
        return QtGui.QValidator.Acceptable, string.upper(), pos
        # for old code still using QString, use this instead
        # string.replace(0, string.count(), string.toUpper())
        # return QtGui.QValidator.Acceptable, pos