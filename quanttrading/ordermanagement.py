"""
this is the main order management system for the whole platform.
the MainEngine is the main entry/control point of the system.
it's a processing class. build the while processing architecture.
setup the gateway (application connect to gateway), 


"""
import logging
from logging import Logger
import smtplib
import os
from abc import ABC
from pathlib import Path
from datetime import datetime
from email.message import EmailMessage
from queue import Empty, Queue
from threading import Thread
from pandas import DataFrame
from typing import Any, Type, Dict, List, Optional

from event.engine import Event, EventEngine

from constant import (
    EVENT_TICK,
    EVENT_ORDER,
    EVENT_TRADE,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_CONTRACT,
    EVENT_LOG,
    EVENT_QUOTE,
    EVENT_HISDATA,
    EVENT_HISDATA_UPDATE,
    EVENT_OPEN_ORDER,
    EVENT_ORDER_STATUS,
    EVENT_PORTFOLIO,
    EVENT_REALTIME_DATA,
    EVENT_TICK_BIDASK_DATA,
    EVENT_TICK_LAST_DATA,
)
from data.gateway.gateway import BaseGateway
from datatypes import (
    BaseApp,
    CancelRequest,
    LogData,
    OrderRequest,
    QuoteData,
    QuoteRequest,
    SubscribeRequest,
    HistoryRequest,
    OrderData,
    BarData,
    TickData,
    TradeData,
    PositionData,
    AccountData,
    ContractData,
    Exchange,
    CandleData,
    Account
)
from setting import SETTINGS
from utility import get_folder_path, TRADER_DIR
from converter import OffsetConverter
from constant import _

logger = logging.getLogger(__name__)

class MainEngine:
    """
    Acts as the core of the trading platform.
    """

    def __init__(self, event_engine: EventEngine = None) -> None:
        """"""
        # all events are processed in this event_engine.
        # log, data communication between modules
        if event_engine:
            self.event_engine: EventEngine = event_engine
        else:
            self.event_engine = EventEngine()
        self.event_engine.start()

        # the programme could have multiple gateways
        # which connect to different provider. like IBKR for stocks
        # and Coinbase for bitcoin 
        self.gateways: Dict[str, BaseGateway] = {}

        # there are the list of the supported exchanges by 
        # those connected gateways. one gateway to multiple 
        # exchanges.
        self.exchanges: List[Exchange] = []

        # log, email, Order management functions. 
        # normally one order management for the whole MainEngine.
        self.managementUnits: Dict[str, BaseManagement] = {}

        # not used now. 
        self.apps: Dict[str, BaseApp] = {}
        # not used for now.
        os.chdir(TRADER_DIR)    # Change working directory

        self.initManagements()     # Initialize function managementUnits

    def initManagements(self) -> None:
        """
        Init all management functions.
        """
        self.addManagement(LogManagement)
        self.addManagement(OrderManagement)
        # self.addManagement(EmailManagement)

    def addManagement(self, managementClass: Any) -> "BaseManagement":
        """
        Add management functions.
        """
        management: BaseManagement = managementClass(self, self.event_engine)
        self.managementUnits[management.management_name] = management
        return management

    def add_gateway(self, gateway_class: Type[BaseGateway], gateway_name: str = "") -> BaseGateway:
        """
        Add gateway. like IBKR, Coinbase, Binance, Trading212, TradingView etc
        after the mainengine initialized. it needs to add a gateway to start 
        the connection and communication with the gateway.
        """
        # Use default name if gateway_name not passed
        if not gateway_name:
            gateway_name: str = gateway_class.default_name

        gateway: BaseGateway = gateway_class(self.event_engine, gateway_name)
        self.gateways[gateway_name] = gateway

        # Add gateway supported exchanges
        for exchange in gateway.exchanges:
            if exchange not in self.exchanges:
                self.exchanges.append(exchange)

        return gateway

    def add_app(self, app_class: Type[BaseApp]) -> "BaseManagement":
        """
        Add app.
        """
        app: BaseApp = app_class()
        self.apps[app.app_name] = app

        engine: BaseManagement = self.addManagement(app.engine_class)
        return engine

    def write_log(self, msg: str, source: str = "") -> None:
        """
        Put log event with specific message.
        """
        log: LogData = LogData(msg=msg, gateway_name=source)
        event: Event = Event(EVENT_LOG, log)
        self.event_engine.put(event)

    def get_gateway(self, gateway_name: str) -> BaseGateway:
        """
        Return gateway object by name.
        """
        gateway: BaseGateway = self.gateways.get(gateway_name, None)
        if not gateway:
            self.write_log(_(f"Can't find {gateway_name=}"))
        return gateway

    def get_engine(self, engine_name:str) -> "BaseManagement":
        """
        Return engine object by name.
        """
        return self.getManagement(engine_name)

    def getManagement(self, management_name: str) -> "BaseManagement":
        """
        Return engine object by name.
        """
        engine: BaseManagement = self.managementUnits.get(management_name, None)
        if not engine:
            self.write_log(_("can't find management module：{}").format(management_name))
        return engine

    def get_default_setting(self, gateway_name: str) -> Optional[Dict[str, Any]]:
        """
        Get default setting dict of a specific gateway.
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.get_default_setting()
        return None

    def get_all_gateway_names(self) -> List[str]:
        """
        Get all names of gateway added in main engine.
        """
        return list(self.gateways.keys())

    def get_all_apps(self) -> List[BaseApp]:
        """
        Get all app objects.
        """
        return list(self.apps.values())

    def get_all_exchanges(self) -> List[Exchange]:
        """
        Get all exchanges.
        """
        return self.exchanges

    def connect(self, setting: dict, gateway_name: str) -> None:
        """
        Start connection of a specific gateway.
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.connect(setting)

    def subscribe(self, req: SubscribeRequest, gateway_name: str) -> None:
        """
        Subscribe tick data update of a specific gateway.
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.subscribe(req)

    def add_contract(self, symbol:str, exchange: Exchange, gateway_name:str) -> None:
        """
        add a contract to the system
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.add_contract(symbol, exchange)
        else:
            return ""
        
    def send_order(self, req: OrderRequest, gateway_name: str) -> str:
        """
        Send new order request to a specific gateway.
        """
        
        gateway: BaseGateway = self.get_gateway(gateway_name)
        self.write_log(f"main engine send_order: {gateway=} and {req=}  ")
        if gateway:
            return gateway.send_order(req)
        else:
            return ""

    def cancel_order(self, req: CancelRequest, gateway_name: str) -> None:
        """
        Send cancel order request to a specific gateway.
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_order(req)

    def send_quote(self, req: QuoteRequest, gateway_name: str) -> str:
        """
        Send new quote request to a specific gateway.
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_quote(req)
        else:
            return ""

    def cancel_quote(self, req: CancelRequest, gateway_name: str) -> None:
        """
        Send cancel quote request to a specific gateway.
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_quote(req)

    def query_history(self, req: HistoryRequest, gateway_name: str) -> Optional[List[BarData]]:
        """
        send request to Query bar history data from a specific gateway.
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.query_history(req)
        else:
            return None
        
    def cancel_all_orders(self, symbol:str=None) -> None:
        """
        cancel all active orders for a specified Symbol. 
        call all active orders for all symbols if symbol is not given
        """
        self.write_log(f"Cancelling all active orders ...... ")
        orders: list[OrderData] = self.get_all_active_orders()
        if symbol:
            tempOrders: list[OrderData] = []
            for _ in orders:
               if _.symbol == symbol:
                   self.write_log(f"cancel_all_orders: {_.symbol} and {_.vt_symbol}")
                   tempOrders.append(_)
            orders = tempOrders
        self.write_log(f"order list to be cancelled: {orders}")

        if not orders:
            return
        for order in orders:
            cancelRequest = order.create_cancel_request()
            self.cancel_order(cancelRequest, order.gateway_name)

        return None

    def cover_all_trades(self, server: bool = False) -> None:
        """
        call this function very carefully. it will cover all 
        your open trades
        cover all trades
        server: 
            True: all positions on server (may include positions not 
        opened by this trading platform)
            False: all positions opened by this trading platform
        """
        
        trades:list[TradeData] = []
        if server:
            trades = self.getall

        return None

    def close(self) -> None:
        """
        Make sure every gateway and app is closed properly before
        programme exit.
        """
        # Stop event engine first to prevent new timer event.
        self.event_engine.stop()

        for engine in self.managementUnits.values():
            engine.close()

        for gateway in self.gateways.values():
            gateway.close()


class BaseManagement(ABC):
    """
    Abstract class for implementing a management function
    in order management system .
    """

    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        management_name: str,
    ) -> None:
        """"""
        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        self.management_name: str = management_name
        self.app_name: str = management_name

    def close(self) -> None:
        """"""
        pass


class LogManagement(BaseManagement):
    """
    Processes log event and output with logging module.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super(LogManagement, self).__init__(main_engine, event_engine, "log")

        if not SETTINGS["log.active"]:
            return

        self.level: int = SETTINGS["log.level"]

        self.logger: Logger = logging.getLogger("Quanttrading")
        self.logger.setLevel(self.level)

        self.formatter: logging.Formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s: %(message)s"
        )

        self.add_null_handler()

        if SETTINGS["log.console"]:
            self.add_console_handler()

        if SETTINGS["log.file"]:
            self.add_file_handler()

        self.register_event()

    def add_null_handler(self) -> None:
        """
        Add null handler for logger.
        """
        null_handler: logging.NullHandler = logging.NullHandler()
        self.logger.addHandler(null_handler)

    def add_console_handler(self) -> None:
        """
        Add console output of log.
        """
        console_handler: logging.StreamHandler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def add_file_handler(self) -> None:
        """
        Add file output of log.
        """
        today_date: str = datetime.now().strftime("%Y%m%d")
        filename: str = f"vt_{today_date}.log"
        log_path: Path = get_folder_path("log")
        file_path: Path = log_path.joinpath(filename)

        file_handler: logging.FileHandler = logging.FileHandler(
            file_path, mode="a", encoding="utf8"
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def register_event(self) -> None:
        """"""
        self.event_engine.register(EVENT_LOG, self.process_log_event)

    def process_log_event(self, event: Event) -> None:
        """
        Process log event.
        """
        log: LogData = event.data
        self.logger.log(log.level, log.msg)


class OrderManagement(BaseManagement):
    """
    Provides order management system function.
    all order related data are processed, kept here.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super(OrderManagement, self).__init__(main_engine, event_engine, "oms")

        # used to save the historical data bars for symbols
        # symbol name to data dict
        self._hisData: Dict[str, list[CandleData]] = {}

        # used to save the update of the historical data
        #  bars. symbol name to data. 
        self._hisDateUpdate: Dict[str, CandleData] = {}

        # symbol map to tick data (last trade)
        self._ticksLast: Dict[str, TickData] = {}

        # symbol map to tick data (bid ask)
        self._ticksBidAsk: Dict[str, TickData] = {}

        self.orders: Dict[str, OrderData] = {}

        # trade.vt_tradeid to TradeData
        self.trades: Dict[str, TradeData] = {}

        # all the positions holded
        self.positions: Dict[str, PositionData] = {}
        
        # all account infomation
        self.accounts: Dict[str, AccountData] = {}

        self.contracts: Dict[str, ContractData] = {}
        self.quotes: Dict[str, QuoteData] = {}

        self.active_orders: Dict[str, OrderData] = {}
        self.active_quotes: Dict[str, QuoteData] = {}

        self.offset_converters: Dict[str, OffsetConverter] = {}

        self.add_function()
        self.register_event()

    def add_function(self) -> None:
        """Add query function to main engine."""
        self.main_engine.getTickLast = self.getTickLast
        self.main_engine.getTickBidAsk = self.getTickBidAsk
        self.main_engine.getHisData = self.getHisData
        self.main_engine.getHisDataUpdate = self.getHisDataUpdate
        self.main_engine.get_order = self.get_order
        self.main_engine.get_trade = self.get_trade
        self.main_engine.get_position = self.get_position
        self.main_engine.get_account = self.get_account
        self.main_engine.get_contract = self.get_contract
        self.main_engine.get_quote = self.get_quote

        self.main_engine.get_all_ticks = self.get_all_ticks
        self.main_engine.get_all_orders = self.get_all_orders
        self.main_engine.get_all_trades = self.get_all_trades
        self.main_engine.get_all_positions = self.get_all_positions
        self.main_engine.get_all_accounts = self.get_all_accounts
        self.main_engine.get_all_contracts = self.get_all_contracts
        self.main_engine.get_all_quotes = self.get_all_quotes
        self.main_engine.get_all_active_orders = self.get_all_active_orders
        self.main_engine.get_all_active_quotes = self.get_all_active_quotes

        self.main_engine.update_order_request = self.update_order_request
        self.main_engine.convert_order_request = self.convert_order_request
        self.main_engine.get_converter = self.get_converter

    def register_event(self) -> None:
        """"""
        # self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        self.event_engine.register(EVENT_ACCOUNT, self.process_account_event)
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)
        self.event_engine.register(EVENT_QUOTE, self.process_quote_event)

        # self.event_engine.register(EVENT_HISDATA, self.processHisData)
        # self.event_engine.register(EVENT_HISDATA_UPDATE, self.processHisDataUpdate)
        # self.event_engine.register(EVENT_REALTIME_DATA, self.processHisDataUpdate)
        # self.event_engine.register(EVENT_TICK_LAST_DATA, self.process_tick_event)
        # self.event_engine.register(EVENT_TICK_BIDASK_DATA, self.process_tick_event)
        self.event_engine.register(EVENT_PORTFOLIO, self.eventTest)
        self.event_engine.register(EVENT_ORDER_STATUS, self.eventTest)
        # self.event_engine.register(EVENT_ACCOUNT, self.eventTest)


        # self.event_engine.register_general(self.eventTest)

    def eventTest(self, event:Event):
        logger.info(f"orderManagement:: eventTest:: ====== " +
                    f" {event.type=}")
        pass

    def processHisData(self, event:Event) -> bool:
        """
        process the historical data for a 
        """
        logger.info(f"processing HisData................ \n {event.type=} and {event.data}")
        candle: CandleData = event.data
        candleList = self._hisData.get(candle.symbol, None)
        if candleList is None:
            candleList = []
            self._hisData[candle.symbol] = candleList
        candleList.append(candle)
        
        return True
    
    def processHisDataUpdate(self, event:Event) -> bool:
        """
        process the historical data update every 5 seconds
        same for realtime data.
        """
        logger.info(f"processing HisDataUpdate................ \n {event.type=} and {event.data}")
        candle: CandleData = event.data
        self._hisDateUpdate[candle.symbol] = candle
        
        return True
    
    def process_tick_event(self, event: Event) -> None:
        """"""
        tick: TickData = event.data
        if event.type == EVENT_TICK_LAST_DATA:
            self._ticksLast[tick.symbol] = tick
        elif event.type == EVENT_TICK_BIDASK_DATA:
            self._ticksBidAsk[tick.symbol] = tick

    def process_order_event(self, event: Event) -> None:
        """"""
        order: OrderData = event.data
        self.orders[order.vt_orderid] = order

        # If order is active, then update data in dict.
        if order.is_active():
            self.active_orders[order.vt_orderid] = order
        # Otherwise, pop inactive order from in dict
        elif order.vt_orderid in self.active_orders:
            self.active_orders.pop(order.vt_orderid)

        # Update to offset converter
        converter: OffsetConverter = self.offset_converters.get(order.gateway_name, None)
        if converter:
            converter.update_order(order)

    def process_trade_event(self, event: Event) -> None:
        """"""
        trade: TradeData = event.data
        self.trades[trade.vt_tradeid] = trade

        # Update to offset converter
        converter: OffsetConverter = self.offset_converters.get(trade.gateway_name, None)
        if converter:
            converter.update_trade(trade)

    def process_position_event(self, event: Event) -> None:
        """"""
        position: PositionData = event.data
        self.positions[position.vt_positionid] = position

        # Update to offset converter
        converter: OffsetConverter = self.offset_converters.get(position.gateway_name, None)
        if converter:
            converter.update_position(position)

    def process_account_event(self, event: Event) -> None:
        """
        account information. saved in DataFrame object.
        """
        account: AccountData = event.data
        # account: DataFrame = 
        self.accounts[account.accountid] = account

    def process_contract_event(self, event: Event) -> None:
        """"""
        contract: ContractData = event.data
        self.contracts[contract.vt_symbol] = contract
        print(f"process_contract_event =========================== {contract=}")
        # Initialize offset converter for each gateway
        if contract.gateway_name not in self.offset_converters:
            self.offset_converters[contract.gateway_name] = OffsetConverter(self)

    def process_quote_event(self, event: Event) -> None:
        """"""
        quote: QuoteData = event.data
        self.quotes[quote.vt_quoteid] = quote

        # If quote is active, then update data in dict.
        if quote.is_active():
            self.active_quotes[quote.vt_quoteid] = quote
        # Otherwise, pop inactive quote from in dict
        elif quote.vt_quoteid in self.active_quotes:
            self.active_quotes.pop(quote.vt_quoteid)

    def getHisData(self, symbol: str) -> Optional[list[CandleData]]:
        """
        """
        return self._hisData.get(symbol,None)
    
    def getHisDataUpdate(self, symbol: str) -> Optional[CandleData]:
        """
        """
        return self._hisDateUpdate.get(symbol,None)
    
    def getTickLast(self, symbol: str) -> Optional[TickData]:
        """
        Get latest market tick data by symbol.
        """
        return self._ticksLast.get(symbol, None)
    
    def getTickBidAsk(self, symbol: str) -> Optional[TickData]:
        """
        Get latest market tick data by symbol.
        """
        return self._ticksBidAsk.get(symbol, None)

    def get_order(self, vt_orderid: str) -> Optional[OrderData]:
        """
        Get latest order data by vt_orderid.
        """
        return self.orders.get(vt_orderid, None)

    def get_trade(self, vt_tradeid: str) -> Optional[TradeData]:
        """
        Get trade data by vt_tradeid.
        """
        return self.trades.get(vt_tradeid, None)

    def get_position(self, vt_positionid: str) -> Optional[PositionData]:
        """
        Get latest position data by vt_positionid.
        """
        return self.positions.get(vt_positionid, None)

    def get_account(self, vt_accountid: str) -> Optional[AccountData]:
        """
        Get latest account data by vt_accountid.
        """
        return self.accounts.get(vt_accountid, None)

    def get_contract(self, vt_symbol: str) -> Optional[ContractData]:
        """
        Get contract data by vt_symbol.
        """
        logger.info(f"--------------get_contract {vt_symbol=} and {self.contracts=}")
        contract = self.contracts.get(vt_symbol, None)
        if not contract:
            if not self.contracts:
                pass
            else:
                for _ in self.contracts.values():
                    logger.info(f"{_.symbolName=}")
                    if _.symbolName == vt_symbol:
                        contract = _
                        break
        return contract

    def get_quote(self, vt_quoteid: str) -> Optional[QuoteData]:
        """
        Get latest quote data by vt_orderid.
        """
        return self.quotes.get(vt_quoteid, None)

    def get_all_ticks(self) -> List[TickData]:
        """
        Get all tick data.
        """
        return list(self._ticksLast.values())

    def get_all_orders(self) -> List[OrderData]:
        """
        Get all order data.
        """
        return list(self.orders.values())

    def get_all_trades(self) -> List[TradeData]:
        """
        Get all trade data.
        """
        return list(self.trades.values())

    def get_all_positions(self) -> List[PositionData]:
        """
        Get all position data.
        """
        return list(self.positions.values())

    def get_all_accounts(self) -> List[AccountData]:
        """
        Get all account data.
        """
        return list(self.accounts.values())

    def get_all_contracts(self) -> List[ContractData]:
        """
        Get all contract data.
        """
        return list(self.contracts.values())

    def get_all_quotes(self) -> List[QuoteData]:
        """
        Get all quote data.
        """
        return list(self.quotes.values())

    def get_all_active_orders(self, vt_symbol: str = "") -> List[OrderData]:
        """
        Get all active orders by vt_symbol.

        If vt_symbol is empty, return all active orders.
        """
        if not vt_symbol:
            return list(self.active_orders.values())
        else:
            active_orders: List[OrderData] = [
                order
                for order in self.active_orders.values()
                if order.vt_symbol == vt_symbol
            ]
            return active_orders

    def get_all_active_quotes(self, vt_symbol: str = "") -> List[QuoteData]:
        """
        Get all active quotes by vt_symbol.
        If vt_symbol is empty, return all active qutoes.
        """
        if not vt_symbol:
            return list(self.active_quotes.values())
        else:
            active_quotes: List[QuoteData] = [
                quote
                for quote in self.active_quotes.values()
                if quote.vt_symbol == vt_symbol
            ]
            return active_quotes

    def update_order_request(self, req: OrderRequest, vt_orderid: str, gateway_name: str) -> None:
        """
        Update order request to offset converter.
        """
        converter: OffsetConverter = self.offset_converters.get(gateway_name, None)
        if converter:
            converter.update_order_request(req, vt_orderid)

    def convert_order_request(
        self,
        req: OrderRequest,
        gateway_name: str,
        lock: bool,
        net: bool = False
    ) -> List[OrderRequest]:
        """
        Convert original order request according to given mode.
        """
        converter: OffsetConverter = self.offset_converters.get(gateway_name, None)
        if not converter:
            return [req]

        reqs: List[OrderRequest] = converter.convert_order_request(req, lock, net)
        return reqs

    def get_converter(self, gateway_name: str) -> OffsetConverter:
        """
        Get offset converter object of specific gateway.
        """
        return self.offset_converters.get(gateway_name, None)

# class DataManagement(BaseManagement):

class EmailManagement(BaseManagement):
    """
    Provides email sending function.
    rewrite it to asyc instead of seperate thread.
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super(EmailManagement, self).__init__(main_engine, event_engine, "email")

        self.thread: Thread = Thread(target=self.run)
        self.queue: Queue = Queue()
        self.active: bool = False

        self.main_engine.send_email = self.send_email

    def send_email(self, subject: str, content: str, receiver: str = "") -> None:
        """"""
        # Start email engine when sending first email.
        if not self.active:
            self.start()

        # Use default receiver if not specified.
        if not receiver:
            receiver: str = SETTINGS["email.receiver"]

        msg: EmailMessage = EmailMessage()
        msg["From"] = SETTINGS["email.sender"]
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.set_content(content)

        self.queue.put(msg)

    def run(self) -> None:
        """"""
        while self.active:
            try:
                msg: EmailMessage = self.queue.get(block=True, timeout=1)

                with smtplib.SMTP_SSL(
                    SETTINGS["email.server"], SETTINGS["email.port"]
                ) as smtp:
                    smtp.login(
                        SETTINGS["email.username"], SETTINGS["email.password"]
                    )
                    smtp.send_message(msg)
            except Empty:
                pass

    def start(self) -> None:
        """"""
        self.active = True
        self.thread.start()

    def close(self) -> None:
        """"""
        if not self.active:
            return

        self.active = False
        self.thread.join()
