# this is a learning file for IB TWS connection


from ibapi.account_summary_tags import AccountSummaryTags
from ibapi.contract import Contract
# from ibapi.ticktype import TickTypeEnum
# from ibapi.execution  import Execution

from ibapi.common import * # @UnusedWildImport
from ibapi.utils import * # @UnusedWildImport
from ibapi.order import *
from tzlocal import get_localzone_name
import pandas
import time
import random
import queue
from abc import ABC, abstractmethod
from typing import Any
import asyncio
import re

# from ibkr import *
from .aiorder import *
from .aicontract import *
from .ibkr import IbkrApp
from .aitools import StoppableThread
from .aicontract import stock_contract

from event.engine import Event, EventEngine
from utility import _idGenerator, create_bg_loop, getDuration
from constant import (
    EVENT_TICK,
    EVENT_ORDER,
    EVENT_TRADE,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_CONTRACT,
    EVENT_LOG,
    EVENT_QUOTE,
)
from datatypes import (
    TickData,
    OrderData,
    TradeData,
    PositionData,
    AccountData,
    ContractData,
    LogData,
    QuoteData,
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
    HistoryRequest,
    QuoteRequest,
    Exchange,
    BarData
)

# Exchanges mapping
EXCHANGE_QT2IB: dict[Exchange, str] = {
    Exchange.SMART: "SMART",
    Exchange.NYMEX: "NYMEX",
    Exchange.COMEX: "COMEX",
    Exchange.GLOBEX: "GLOBEX",
    Exchange.IDEALPRO: "IDEALPRO",
    Exchange.CME: "CME",
    Exchange.CBOT: "CBOT",
    Exchange.CBOE: "CBOE",
    Exchange.ICE: "ICE",
    Exchange.SEHK: "SEHK",
    Exchange.SSE: "SEHKNTL",
    Exchange.SZSE: "SEHKSZSE",
    Exchange.HKFE: "HKFE",
    Exchange.CFE: "CFE",
    Exchange.TSE: "TSE",
    Exchange.NYSE: "NYSE",
    Exchange.NASDAQ: "NASDAQ",
    Exchange.AMEX: "AMEX",
    Exchange.ARCA: "ARCA",
    Exchange.EDGEA: "EDGEA",
    Exchange.ISLAND: "ISLAND",
    Exchange.BATS: "BATS",
    Exchange.IEX: "IEX",
    Exchange.IBKRATS: "IBKRATS",
    Exchange.OTC: "PINK",
    Exchange.SGX: "SGX",
    Exchange.EUREX: "EUREX",
}

EXCHANGE_IB2QT: dict[str, Exchange] = {v: k for k, v in EXCHANGE_QT2IB.items()}

def intervalToIB(interval) -> str:
    """ 
    change interval to Ibkr's barsizesetting
    Interval = Literal["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "1wk"]
    # barSizeSetting: 1/5/10/15/30 secs, 1 min, 2/3/5/10/15/20/30 mins,
    # 1 hour, 2/3/4/8 hours, 1 day, 1W, 1M"
    #     example '1 hour' or '1 min'
    """
    tobe = re.sub('1m','1 min', interval)
    replaceDict = {'1m':'1 min', 'm': ' mins', '1h': '1 hour', 'h': ' hours', '1d': '1 day', '1wk':'1W'}
    for ori, rep in replaceDict.items():
        if tobe != interval:
            break
        tobe = re.sub(ori, rep, interval)
    
    return tobe

class BaseGateway(ABC):
    """
    Abstract gateway class for creating gateways connection
    to different trading systems.

    # How to implement a gateway:
    ---
    ## Basics
    A gateway should satisfies:
    * this class should be thread-safe:
        * all methods should be thread-safe
        * no mutable shared properties between objects.
    * all methods should be non-blocked
    * satisfies all requirements written in docstring for every method and callbacks.
    * automatically reconnect if connection lost.

    ---
    ## methods must implements:
    all @abstractmethod

    ---
    ## callbacks must response manually:
    * on_tick
    * on_trade
    * on_order
    * on_position
    * on_account
    * on_contract

    All the XxxData passed to callback should be constant, which means that
        the object should not be modified after passing to on_xxxx.
    So if you use a cache to store reference of data, use copy.copy to create a new object
    before passing that data into on_xxxx
    """

    # Default name for the gateway.
    default_name: str = ""

    # Fields required in setting dict for connect function.
    default_setting: dict[str, Any] = {}

    # Exchanges supported in the gateway.
    # exchanges: list[Exchange] = []

    def __init__(self, event_engine: EventEngine, gateway_name: str) -> None:
        """"""
        self.event_engine: EventEngine = event_engine
        self.gateway_name: str = gateway_name

    def on_event(self, type: str, data: Any = None) -> None:
        """
        General event push.
        """
        event: Event = Event(type, data)
        self.event_engine.put(event)

    def on_tick(self, tick: TickData) -> None:
        """
        Tick event push.
        Tick event of a specific vt_symbol is also pushed.
        """
        self.on_event(EVENT_TICK, tick)
        self.on_event(EVENT_TICK + tick.vt_symbol, tick)

    def on_trade(self, trade: TradeData) -> None:
        """
        Trade event push.
        Trade event of a specific vt_symbol is also pushed.
        """
        self.on_event(EVENT_TRADE, trade)
        self.on_event(EVENT_TRADE + trade.vt_symbol, trade)

    def on_order(self, order: OrderData) -> None:
        """
        Order event push.
        Order event of a specific vt_orderid is also pushed.
        """
        self.on_event(EVENT_ORDER, order)
        self.on_event(EVENT_ORDER + order.vt_orderid, order)

    def on_position(self, position: PositionData) -> None:
        """
        Position event push.
        Position event of a specific vt_symbol is also pushed.
        """
        self.on_event(EVENT_POSITION, position)
        self.on_event(EVENT_POSITION + position.vt_symbol, position)

    def on_account(self, account: AccountData) -> None:
        """
        Account event push.
        Account event of a specific vt_accountid is also pushed.
        """
        self.on_event(EVENT_ACCOUNT, account)
        self.on_event(EVENT_ACCOUNT + account.vt_accountid, account)

    def on_quote(self, quote: QuoteData) -> None:
        """
        Quote event push.
        Quote event of a specific vt_symbol is also pushed.
        """
        self.on_event(EVENT_QUOTE, quote)
        self.on_event(EVENT_QUOTE + quote.vt_symbol, quote)

    def on_log(self, log: LogData) -> None:
        """
        Log event push.
        """
        self.on_event(EVENT_LOG, log)

    def on_contract(self, contract: ContractData) -> None:
        """
        Contract event push.
        """
        self.on_event(EVENT_CONTRACT, contract)

    def write_log(self, msg: str) -> None:
        """
        Write a log event from gateway.
        """
        log: LogData = LogData(msg=msg, gateway_name=self.gateway_name)
        self.on_log(log)

    @abstractmethod
    def connect(self, setting: dict) -> None:
        """
        Start gateway connection.

        to implement this method, you must:
        * connect to server if necessary
        * log connected if all necessary connection is established
        * do the following query and response corresponding on_xxxx and write_log
            * contracts : on_contract
            * account asset : on_account
            * account holding: on_position
            * orders of account: on_order
            * trades of account: on_trade
        * if any of query above is failed,  write log.

        future plan:
        response callback/change status instead of write_log

        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close gateway connection.
        """
        pass

    @abstractmethod
    def subscribe(self, req: SubscribeRequest) -> None:
        """
        Subscribe tick data update.
        """
        pass

    @abstractmethod
    def send_order(self, req: OrderRequest) -> str:
        """
        Send a new order to server.

        implementation should finish the tasks blow:
        * create an OrderData from req using OrderRequest.create_order_data
        * assign a unique(gateway instance scope) id to OrderData.orderid
        * send request to server
            * if request is sent, OrderData.status should be set to Status.SUBMITTING
            * if request is failed to sent, OrderData.status should be set to Status.REJECTED
        * response on_order:
        * return vt_orderid

        :return str vt_orderid for created OrderData
        """
        pass

    @abstractmethod
    def cancel_order(self, req: CancelRequest) -> None:
        """
        Cancel an existing order.
        implementation should finish the tasks blow:
        * send request to server
        """
        pass

    def send_quote(self, req: QuoteRequest) -> str:
        """
        Send a new two-sided quote to server.

        implementation should finish the tasks blow:
        * create an QuoteData from req using QuoteRequest.create_quote_data
        * assign a unique(gateway instance scope) id to QuoteData.quoteid
        * send request to server
            * if request is sent, QuoteData.status should be set to Status.SUBMITTING
            * if request is failed to sent, QuoteData.status should be set to Status.REJECTED
        * response on_quote:
        * return vt_quoteid

        :return str vt_quoteid for created QuoteData
        """
        return ""

    def cancel_quote(self, req: CancelRequest) -> None:
        """
        Cancel an existing quote.
        implementation should finish the tasks blow:
        * send request to server
        """
        pass

    @abstractmethod
    def query_account(self) -> None:
        """
        Query account balance.
        """
        pass

    @abstractmethod
    def query_position(self) -> None:
        """
        Query holding positions.
        """
        pass

    def query_history(self, req: HistoryRequest) -> list[BarData]:
        """
        Query bar history data.
        """
        pass

    def get_default_setting(self) -> dict[str, Any]:
        """
        Return default setting dict.
        """
        return self.default_setting


class IbkrGateway(BaseGateway):
    default_name: str = "IB"
    exchanges: list[str] = list(EXCHANGE_QT2IB.keys())
    default_setting: dict = {
        "TWS地址": "127.0.0.1",
        "TWS端口": 7497,
        "客户号": 1,
        "交易账户": ""
    }

    def __init__(self, event_engine: EventEngine, gateway_name: str) -> None:
        """"""
        super().__init__(event_engine, gateway_name)
        self.reqIdGenerator = _idGenerator()
        self._app = IbkrApp(event_engine,gwName = gateway_name)
        self._app_thread: StoppableThread = None
        self._gatewaySetting: dict[str,str|int] = {}
        self._active: bool = False
        self._check_connection_task = None


    def connect(self, setting: dict) -> None:
        """
        Start gateway connection.

        to implement this method, you must:
        * connect to server if necessary
        * log connected if all necessary connection is established
        * do the following query and response corresponding on_xxxx and write_log
            * contracts : on_contract
            * account asset : on_account
            * account holding: on_position
            * orders of account: on_order
            * trades of account: on_trade
        * if any of query above is failed,  write log.
        """
        if self._active:
            return
        
        self._active = True

        if setting is None:
            setting = {}
        
        # the TWS client which is running your account
        localTWSIP = setting.get("IP", "127.0.0.1")
        # default to 7497. which is the test/paper trading TWS
        localTWSport = setting.get("PORT", 7497)
        # clientId:int - A number used to identify this client connection. 
        # All orders placed/modified from this client will be associated with this client identifier.
        localClientId = setting.get("ClIENTID", random.randint(1,100))

        logger.info(f"program is starting ... ip:port:id is {localTWSIP}:{localTWSport}:{localClientId}")
        self._gatewaySetting.update({'IP':localTWSIP, 'PORT':localTWSport, 'CLIENTID':localClientId})

        self._app.connect(localTWSIP, localTWSport, localClientId)
        # self._app.connect('192.168.1.146', 7497, 1)
        
        logger.info(f"IbkrGateway is Connected? : {self._app.isConnected()}")

        self._app.nextorderId = None
        
        #Start the socket in a thread
        self._app_thread = StoppableThread(target=self._app.run, daemon=True)
        self._app_thread.start()

        # requre all the 
        # self._app.reqAccountSummary(9001, "All", AccountSummaryTags.AllTags)

        #Sleep interval to allow time for response data from server
        # time.sleep(2) 

        # The IBApi.EClient.reqAccountUpdates function creates a subscription 
        # to the TWS through which account and portfolio information is 
        # delivered. This information is the exact same as the one displayed
        #  within the TWS’ Account Window. Just as with the TWS’ Account 
        # Window, unless there is a position change this information is
        #  updated at a fixed interval of three minutes.
        # self._app.reqAccountUpdates(True, self._app.account)
        # self._app.set_current_Contract(stock_contract("AAPL"))
        # logger.info("entered starting event loop  ")
        # self._loop = create_bg_loop()
        # self._check_connection_task = asyncio.run_coroutine_threadsafe(self.check_connection(), self._loop)
        
    async def check_connection(self) -> None:
        """check the connection every 10 seconds."""
        while self._active:
            await asyncio.sleep(10)
            if self._app.isConnected():
                logger.info("ibkrgateway connected...")
                return

            if self._app.status:
                self._app.disconnect()

            self._app.connect(self._gatewaySetting.get('IP'), self._gatewaySetting.get('PORT'), self._gatewaySetting.get('CLIENTID'))
            logger.debug(f"ibkrgateway: trying to connect to {self._gatewaySetting}......")

    def close(self) -> None:
        """
        Close gateway connection.
        """
        # Once the subscription to account updates is no longer needed,
        #  it can be cancelled by invoking the 
        # IBApi.EClient.reqAccountUpdates method while specifying 
        # the susbcription flag to be False.
        if not self._active:
            return 
        
        self._active = False

        # self._app.reqAccountUpdates(False, self._app.account)
        logger.info("Exiting Program...")
        # self.event_engine.stop()
        # self._loop.stop()
        self._app_thread.stop()
        self._app.disconnect()

    def subscribe(self, req: SubscribeRequest) -> None:
        """
        Subscribe tick data update.
        """
        pass

    def send_order(self, req: OrderRequest) -> str:
        """
        Send a new order to server.

        implementation should finish the tasks blow:
        * create an OrderData from req using OrderRequest.create_order_data
        * assign a unique(gateway instance scope) id to OrderData.orderid
        * send request to server
            * if request is sent, OrderData.status should be set to Status.SUBMITTING
            * if request is failed to sent, OrderData.status should be set to Status.REJECTED
        * response on_order:
        * return vt_orderid

        :return str vt_orderid for created OrderData
        """
        pass

    def cancel_order(self, req: CancelRequest) -> None:
        """
        Cancel an existing order.
        implementation should finish the tasks blow:
        * send request to server
        """
        pass

    def query_history(self, req: HistoryRequest) -> list[BarData]:
        super().query_history(req)
        if self._app.isConnected():
            # contract: Contract, The IBApi.Contract object you are working with.
            # endDateTime: String, The request’s end date and time.
            # This should be formatted as “YYYYMMDD HH:mm:ss TMZ” or an empty string indicates current present moment).
            # durationStr: S/D/W/M/Y. Example '1 D'
            # barSizeSetting: 1/5/10/15/30 secs, 1 min, 2/3/5/10/15/20/30 mins,
            # 1 hour, 2/3/4/8 hours, 1 day, 1W, 1M"
            #     example '1 hour' or '1 min'
            # whatToShow: These values are used to request different data such as TRADES, MIDPOINT, BID_ASK, ASK, BID data and more.
            # example: 'Trades
            # formatDate: 1 String Time Zone Date “20231019 16:11:48 America/New_York”
            #     2 Epoch Date 1697746308
            #     3 Day & Time Date “1019 16:11:48 America/New_York”
            # useRTH 0 = Includes data outside of RTH. 1 = RTH data only

            endDateTime = req.end.strftime("%Y%m%d %H:%M:%S ") + get_localzone_name()
            interval = intervalToIB(req.interval)
            duration = getDuration(req.start, req.end)
            contract = stock_contract(req.symbol, EXCHANGE_QT2IB.get(req.exchange, 'SMART'))
            self._app.reqHistoricalData(self.nextId(), contract, endDateTime, duration, interval, "Trades", req.useRTH, 1, req.keepUpdate, [])
        else:
            logger.info(f"Ibkrgateway is not connected to the server yet. please connect it first!")
            return None

    def query_account(self) -> None:
        """
        Query account balance.
        """
        pass

    def query_position(self) -> None:
        """
        Query holding positions.
        """
        pass

    def nextId(self) -> int:
        """"""
        return next(self.reqIdGenerator)