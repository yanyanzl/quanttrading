# this is a learning file for IB TWS connection


from ibapi.account_summary_tags import AccountSummaryTags
from ibapi.contract import Contract
# from ibapi.ticktype import TickTypeEnum
# from ibapi.execution  import Execution

from ibapi.common import * # @UnusedWildImport
from ibapi.utils import * # @UnusedWildImport
from ibapi.order import *

import pandas
import time
import random
import queue
from abc import ABC, abstractmethod
from typing import Any
import asyncio

# from ibkr import *
from .aiorder import *
from .aicontract import *
from .ibkr import IbkrApp
from .aitools import StoppableThread
from .aicontract import stock_contract

from event.engine import Event, EventEngine
from utility import _idGenerator
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
        self._app = IbkrApp()
        self._app_thread: StoppableThread = None
        self._gatewaySetting: dict[str,str|int] = {}
        self._active: bool = False
        self._check_connection_future = None


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

        self._loop = asyncio.get_event_loop()
        self._check_connection_future = self._loop.create_task(self.check_connection())

    async def check_connection(self) -> None:
        """check the connection every 10 seconds."""
        while self._active:
            await asyncio.sleep(10)
            if self._app.isConnected():
                return

            if self._app.status:
                self.close()

            self._app.connect(self._gatewaySetting.get('IP'), self._gatewaySetting.get('PORT'), self._gatewaySetting.get('CLIENTID'))

            self._app_thread = StoppableThread(target=self._app.run, daemon=True)
            self._app_thread.start()

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
        # time.sleep(1)
        logger.info("Exiting Program...")

        # self.event_engine.stop()
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
            self._app.reqHistoricalData(self.nextId, stock_contract(req.symbol,req.exchange), req.end, req.duration, req.interval, "Trades", req.useRTH, 1, req.keepUpdate, [])
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

def main():
    engine = EventEngine(10)
    gw = IbkrGateway(engine, "IbkrGateway")
    gw.connect()

    logger.info("connect completed!")

def tmpHolder():
    message_q = queue.Queue()

    def worker():
        while True:
            if not message_q.empty():
                item = message_q.get()
                # print(f'Working on {item}')
                # if item:
                #     if mainframe:
                #         display_message(str(item),mainframe.message_area)
                #     if str(item) == Aiconfig.get("SYMBOL_CHANGED"):
                #         if app and mainframe:
                #             app.set_current_Contract(stock_contract(mainframe.symbol_selected))
                # print(f'Finished {item}')
                message_q.task_done()

    # Turn-on the worker thread.
    que_thread = StoppableThread(target=worker, daemon=True)
    que_thread.start()

    def exit_app():
        # Once the subscription to account updates is no longer needed, it can be cancelled by invoking the IBApi.EClient.reqAccountUpdates method while specifying the susbcription flag to be False.
        app.reqAccountUpdates(False, app.account)
        time.sleep(1) 
        print("Exiting Program...")
        app.disconnect()
        api_thread.stop()
        que_thread.stop()

    def tick_data():
        for key in Aiconfig.get('TICK_BIDASK'):
            on_press(key)
    def bar_data():
        for key in Aiconfig.get('REQUIRE_REALTIME_BAR'):
            on_press(key)

    def key_press(event):
        """
        # function to be called when keyboard buttons are pressed
        # key = event.char
        """
        keysymbol = str(event.keysym).lower()

        if len(keysymbol) > 1:
            keysymbol = "key."+keysymbol.strip('_l').strip('_r')
        # print(key, 'is pressed')
        print(keysymbol, 'is pressed')
        # display_message(str(event), mainframe.message_area)
        # display_message(keysymbol, mainframe.message_area)
        on_press(keysymbol)

    def key_release(event):
        # key = event.char
        keysymbol = str(event.keysym).lower()
        
        if len(keysymbol) > 1:
            keysymbol = "key."+keysymbol.strip('_l').strip('_r')
        # print(key, 'is pressed')
        print(keysymbol, 'is released')
        on_release(keysymbol)


    app = IbkrApp()
    print("program is starting ...")
    app.connect('127.0.0.1', 7497, 36)
    # app.connect('192.168.1.146', 7497, 1)
    
    print(app.isConnected())

    app.nextorderId = None
    
    #Start the socket in a thread
    api_thread = StoppableThread(target=app.run, daemon=True)
    api_thread.start()
    
    #Check if the API is connected via orderid
    while True:
        if isinstance(app.nextorderId, int):
            print('connected')
            break
        else:
            print('waiting for connection')
            time.sleep(1)

    time.sleep(1) #Sleep interval to allow time for connection to server

    # requre all the 
    app.reqAccountSummary(9001, "All", AccountSummaryTags.AllTags)

    #Sleep interval to allow time for response data from server
    time.sleep(2) 

    # The IBApi.EClient.reqAccountUpdates function creates a subscription to the TWS through which account and portfolio information is delivered. This information is the exact same as the one displayed within the TWS’ Account Window. Just as with the TWS’ Account Window, unless there is a position change this information is updated at a fixed interval of three minutes.
    app.reqAccountUpdates(True, app.account)

    app.set_current_Contract(stock_contract("AAPL"))

    # time.sleep(2)


    ################ keyboard input monitoring part start
    # monitoring the keyboard and make it available to control the order
    combo_key = set()

    def on_press(key):
        try:
            message = ""
            # print('alphanumeric key pressed', key.char.lower())
            # change object key to lower string case without quotation mark.
            key = str(key).lower().strip("'")

            print(f"key is --- : {key}")
            # print(Aiconfig.get('PLACE_BUY_ORDER'))

            # place limit buy order Tif = day
            if key == Aiconfig.get('PLACE_BUY_ORDER'):
                place_lmt_order(app, "BUY", increamental=Aiconfig.get("BUY_LMT_PLUS"))

            # place limit buy order Tif = day
            elif key == Aiconfig.get('PLACE_SELL_ORDER'):
                place_lmt_order(app, "SELL", increamental=Aiconfig.get("SELL_LMT_PLUS"))

             
            # # cancel last order
            # elif any([key in COMBO for COMBO in Aiconfig.get('CANCEL_LAST_ORDER')]): # Checks if pressed key is in any combinations
            #     combo_key.add(key)
            #     if any(all (k in combo_key for k in COMBO) for COMBO in Aiconfig.get('CANCEL_LAST_ORDER')): # Checks if every key of the combination has been pressed
            #         cancel_last_order(app)
            #         combo_key.clear()
            
            # cancel last order
            elif any([key in Aiconfig.get('CANCEL_LAST_ORDER')]): # Checks if pressed key is in any combinations
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('CANCEL_LAST_ORDER')): # Checks if every key of the combination has been pressed
                    cancel_last_order(app)
                    combo_key.clear()

            elif key == Aiconfig.get('CHANGE_CONTRACT'):
                message = "change current contract..."
                print(message)
                change_current_Contract(app)
            
            elif key == Aiconfig.get('SHOW_CURRENT_CONTRACT'):
                show_current_Contract(app)

            # cancel all orders
            elif any([key in Aiconfig.get('CANCEL_ALL_ORDER')]): # Checks if pressed key is in any combinations
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('CANCEL_ALL_ORDER')): # Checks if every key of the combination has been pressed
                    cancel_all_order(app)
                    combo_key.clear()

            elif key == Aiconfig.get('PLACE_IOC_BUY'):
                 place_lmt_order(app, "BUY", tif="IOC", increamental=Aiconfig.get('BUY_LMT_PLUS'), priceTickType="ASK")
            
            elif key ==  Aiconfig.get('PLACE_IOC_SELL'):
                 place_lmt_order(app, "SELL", tif="IOC", increamental=Aiconfig.get('SELL_LMT_PLUS'), priceTickType="BID")
            
            ########### to be completed
            elif key ==  Aiconfig.get('PLACE_STOP_SELL'):
                 pass
            
            elif key ==  Aiconfig.get('PLACE_STOP_BUY'):
                 pass
            
            elif key ==  Aiconfig.get('PLACE_BRACKET_BUY'):
                 pass
            
            elif key ==  Aiconfig.get('PLACE_BRACKET_SELL'):
                 pass
            
            elif any([key in Aiconfig.get('REQ_OPEN_ORDER')]): #  Requests all current open orders in associated accounts at the current moment. The existing orders will be received via the openOrder and orderStatus events. Open orders are returned once; this function does not initiate a subscription.
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('REQ_OPEN_ORDER')): # Checks if every key of the combination has been pressed
                    message = "requesting all Open orders from server now ..."
                    print(message)
                    app.reqAllOpenOrders()
                    combo_key.clear()

            elif any([key in Aiconfig.get('TICK_BIDASK')]): 
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('TICK_BIDASK')): # Checks if every key of the combination has been pressed
                    message = f"requesting tick by tick bidask data from server for {app.currentContract} now ..."
                    print()
                    app.reqTickByTickData(19003, app.currentContract, "BidAsk", 0, True)
                    combo_key.clear()

            elif any([key in Aiconfig.get('CANCEL_TICK_BIDASK')]): 
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('CANCEL_TICK_BIDASK')): # Checks if every key of the combination has been pressed
                    message = "cancelling tick by tick bidask data from server now ..."
                    print(message)
                    app.cancelTickByTickData(19003)
                    combo_key.clear()

            elif any([key in Aiconfig.get('SHOW_PORT')]): 
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('SHOW_PORT')): # Checks if every key of the combination has been pressed
                    show_portforlio(app)
                    combo_key.clear()

            elif any([key in Aiconfig.get('SHOW_SUMMARY')]): 
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('SHOW_SUMMARY')): # Checks if every key of the combination has been pressed
                    show_summary(app)
                    combo_key.clear()

            elif any([key in Aiconfig.get('REQUIRE_REALTIME_BAR')]): 
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('REQUIRE_REALTIME_BAR')): 
                    message = "requesting real time Bars data from server now ..."
                    print(message)
                    # whatToShow	the nature of the data being retrieved: TRADES, MIDPOINT, BID, ASK
                    app.reqRealTimeBars(19002,app.currentContract,1,"TRADES", 0,[])
                    combo_key.clear() 

            elif any([key in Aiconfig.get('CANCEL_REALTIME_BAR')]): 
                combo_key.add(key)
                if all (k in combo_key for k in Aiconfig.get('CANCEL_REALTIME_BAR')): 
                    message = "cancalling real time Bars data from server now ..."
                    print(message)
                    app.cancelRealTimeBars(19002)
                    combo_key.clear()        

            else:
                #  if DEBUG:
                     pass
                    #print(f"{key} is not defined for any function now ...")
            if message and IbkrApp.has_message_queue():
                IbkrApp.message_q.put(message)

        except AttributeError:
            message = 'special key {0} pressed'.format(key)
            print(message)

    def on_release(key):
        # print('{0} released'.format(key))
        # change object key to lower string case without quotation mark.
        key = str(key).lower().strip("'")
        message = ""
        if key == 'key.esc' or key == 'key.escape':
            # Stop listener
            message = "Stopping Listener..."
            print(message)
            if IbkrApp.has_message_queue():
                IbkrApp.message_q.put(message)
            exit_app()
            return False # return False to the call thread. it will terminate the thread
        
        # in case only part of the key pressed. those key should be removed from combo_key.
        elif any([key in combo_key]):
             combo_key.remove(key)
            #  print(f"removing...{key}")
        # else:
        #     print(f"you pressed...{key}")

    IbkrApp.message_q = message_q


# get the histroy data for a contract
def get_his_data(app=IbkrApp(),contract=Contract()):
    #Request historical candles
    app.reqHistoricalData(1, contract, '', '5 D', '1 hour', 'BID', 0, 2, False, [])

    #Sleep interval to allow time for incoming price data. 
    # without this sleep. the data will be empty
    time.sleep(2) 
    # transform data to Dataframe format. 
    df = pandas.DataFrame(app.data, columns=['DateTime', 'Close'])
    df['DateTime'] = pandas.to_datetime(df['DateTime'],unit="s")

    # 20 SMA of the close price.
    df['20SMA'] = df['Close'].rolling(20).mean()
    # print(df.tail(10))


def change_current_Contract(app=IbkrApp()):
    """ change the current contract object for the current IbkrApp instance.
    """
    try:
        if app.isConnected():

            while True:
                contractType = input("Input F (for FX) or S (for Stock):")
                if any([contractType.lower() in ['f','s']]):
                    break
                else:
                    print("invalid input...")

            while True:
                if contractType.lower() == 'f':
                    symbol = input("Input FX name (six letter, like EURUSD):")
                    if symbol and len(symbol) == 6:
                        app.set_current_Contract(fx_contract(symbol))
                        break
                        
                else:
                    symbol = input("Input stock tick name (like TSLA or AAPL):")
                    if symbol and len(symbol) > 0:
                        app.set_current_Contract(stock_contract(symbol))
                        break
                print("invalid input...")

    except Exception as ex:
        print("failed to change current contract. invalid input.")

def show_current_Contract(app=IbkrApp()):
    """ show the current contract in the current IbkrApp instance. 
    """
    message = ""
    if app.isConnected() and app.currentContract:
        message = f"current contract is :{app.currentContract}"

    else:
        message = f"show current contract failed.connected: {app.isConnected()}. current contract {app.currentContract}"

    print(message)
    if IbkrApp.has_message_queue():
        IbkrApp.message_q.put(message)


if __name__ == "__main__":
    main()
