from collections import defaultdict
from typing import Callable, Dict, Optional

from event import Event, EventEngine
from datatypes import OrderData, OrderRequest, LogData, TradeData, TickData, TradeBook
from ordermanagement import MainEngine, BaseManagement as BaseEngine
from constant import EVENT_TRADE, EVENT_ORDER, EVENT_LOG, EVENT_TIMER, EVENT_TICK, RiskLevel
from constant import Direction, Status, Offset
from utility import load_json, save_json


APP_NAME = "RiskManager"


class RiskEngine(BaseEngine):
    """
    Risk management function.
    manage the total risk exposed by the account level.
        # number of active orders default 50
        # number of canceled orders. default 500
        # max number of trades: default 1000
        # max size per order. default 100
        # max orders per period: default 10 per 1 sencond
        # total profit limit (realize + unrealized): default 1000
        # realized profit limit: default 1000
        # total loss limit: default 150
        # realised loss limit: default 100
    """

    setting_filename: str = "risk_manager_setting.json"

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)

        # start risk management in the main engine or not
        self.active: bool = True

        # freeze all due to risk level too high.
        self.freeze: bool = True

        # max orders per period: default 10
        self.order_flow_count: int = 0
        self.order_flow_limit: int = 10

        # max orders period length: 1 sencond
        self.order_flow_clear: int = 1
        self.order_flow_timer: int = 0

        # max size per order. default 100
        self.order_size_limit: int = 100

        # max number of trades: default 1000
        self.trade_count: int = 0
        self.trade_limit: int = 1000

        # number of canceled orders. default 500
        self.order_cancel_limit: int = 500
        self.order_cancel_counts: Dict[str, int] = defaultdict(int)

        # number of active orders default 50
        self.active_order_limit: int = 50

        self.active_order_books: Dict[str, ActiveOrderBook] = {}

        # check the pnl periodcally. period 10 sec
        self.pnl_check_timer: int = 0
        self.pnl_check_period: int = 10

        # total profit limit (realize + unrealized): default 1000
        self.total_profit_limit: float = 1000
        self.total_profit: float = 0

        # realized profit limit: default 1000
        self.realised_profit_limit: float = 1000
        self.realised_profit: float = 0

        # total loss limit: default -150
        self.total_loss_limit: float = -150
        # self.total_loss: float = 0

        # realised loss limit: default -100
        self.realised_loss_limit: float = -100
        # self.realised_loss: float = 0


        # symbol to tradebook map
        self.active_trades: Dict[str, TradeBook] = {}
        self.all_trades: list[TradeData] = []

        self.load_setting()
        self.register_event()
        self.patch_send_order()

    def patch_send_order(self) -> None:
        """
        Patch send order function of MainEngine.
        """
        self._send_order: Callable[[OrderRequest, str], str] = self.main_engine.send_order
        self.main_engine.send_order = self.send_order

    def send_order(self, req: OrderRequest, gateway_name: str) -> str:
        """"""
        # check if the request is to cover positions
        isCover = self.check_is_cover(req)
        if isCover:
            result = ""
            self.write_log(f"RiskEngine:: covering positions by {req.symbol=} {req.direction=} {req.type=} {req.volume=}")
            # split orders to order size limit
            totalVolume = req.volume
            while totalVolume > self.order_size_limit:
                req.volume = self.order_size_limit
                totalVolume -= self.order_size_limit
                result = self._send_order(req, gateway_name)
            
            if totalVolume > 0:
                req.volume = totalVolume
                result = self._send_order(req, gateway_name)

            return result

        result: bool = self.check_risk(req, gateway_name)
        if not result:
            # self.write_log(f"RiskEngine: only orders for cover positions allowed!")
            return ""

        return self._send_order(req, gateway_name)

    def update_setting(self, setting: dict) -> None:
        """"""
        self.active = setting["active"]
        self.freeze = setting["freeze"]
        self.order_flow_limit = setting["order_flow_limit"]
        self.order_flow_clear = setting["order_flow_clear"]
        self.order_size_limit = setting["order_size_limit"]
        self.trade_limit = setting["trade_limit"]
        self.active_order_limit = setting["active_order_limit"]
        self.order_cancel_limit = setting["order_cancel_limit"]


        self.total_profit_limit = setting["total_profit_limit"]
        self.realised_profit_limit = setting["realised_profit_limit"]
        self.total_loss_limit = setting["total_loss_limit"]
        self.realised_loss_limit = setting["realised_loss_limit"]

        if self.active:
            self.write_log("Risk management started")
        else:
            self.write_log("Risk management stoped")

    def get_setting(self) -> dict:
        """"""
        setting: dict = {
            "active": self.active,
            "freeze": self.freeze,
            "order_flow_limit": self.order_flow_limit,
            "order_flow_clear": self.order_flow_clear,
            "order_size_limit": self.order_size_limit,
            "trade_limit": self.trade_limit,
            "active_order_limit": self.active_order_limit,
            "order_cancel_limit": self.order_cancel_limit,

            "total_profit_limit": self.total_profit_limit,
            "realised_profit_limit": self.realised_profit_limit,
            "total_loss_limit": self.total_loss_limit,
            "realised_loss_limit": self.realised_loss_limit,

        }
        return setting

    def load_setting(self) -> None:
        """"""
        setting: dict = load_json(self.setting_filename)
        if not setting:
            return

        self.update_setting(setting)

    def save_setting(self) -> None:
        """"""
        setting: dict = self.get_setting()
        save_json(self.setting_filename, setting)

    def register_event(self) -> None:
        """"""
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_TIMER, self.process_timer_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TICK, self.process_tick_event)

    def process_tick_event(self, event: Event) -> None:
        """
        process tick event when the risk management is active
        """
        if not self.active:
            return
        
        tick:TickData = event.data
        if tick.symbol in self.active_trades:
            self.active_trades.get(tick.symbol).on_tick(tick)

        return

    def process_order_event(self, event: Event) -> None:
        """process all order informatoin """
        order: OrderData = event.data

        order_book: ActiveOrderBook = self.get_order_book(order.vt_symbol)
        order_book.update_order(order)

        if order.status != Status.CANCELLED:
            return
        self.order_cancel_counts[order.vt_symbol] += 1

    def process_trade_event(self, event: Event) -> None:
        """ process all trades informatoin """
        trade: TradeData = event.data
        self.trade_count += trade.volume

        symbol = trade.symbolName
        activeTrade: TradeBook = self.active_trades.get(symbol, None)

        # if no trade data for this symbol yet. create it.
        if not activeTrade:
            activeTrade = self.active_trades[symbol] = TradeBook(symbol)

        # update trade related numbers.
        activeTrade.update_trades(trade)
        self.update_pnl_risk()
        self.check_pnl_risk()

    def process_timer_event(self, event: Event) -> None:
        """ 
        process the timer event when risk management is on
        and the application is not freezed due to high risk
        """
        if not self.active:
            return
        
        self.order_flow_timer += 1
        self.pnl_check_timer += 1

        if self.order_flow_timer >= self.order_flow_clear:
            self.order_flow_count = 0
            self.order_flow_timer = 0
        
        if self.pnl_check_timer >= self.pnl_check_period:
            self.pnl_check_timer = 0
            self.update_pnl_risk()
            riskLevel = self.check_pnl_risk()
            if self.freeze and riskLevel in [RiskLevel.LevelWarning, RiskLevel.LevelCritical]:
                self.write_log(f"riskLevel:{riskLevel}, trigger risk control to cover all trades")
                self.write_log(f"pnl={self.total_profit}, realised={self.realised_profit}, losslimit{self.total_loss_limit}, realisedLosslimit:{self.realised_loss_limit}")
                self.main_engine.cancel_all_orders()
                self.main_engine.cover_all_trades()
                # cover all outstanding positions to be added.
                
    def write_log(self, msg: str) -> None:
        """"""
        log: LogData = LogData(msg=msg, gateway_name="RiskManager")
        event: Event = Event(type=EVENT_LOG, data=log)
        self.event_engine.put(event)

    def update_pnl_risk(self) -> bool:
        """
        update realised_profit and total_profit based on the 
        lastest trades or 
        update total_profit only based on the lastest tick 
        price.
        """
        if not self.active or not self.active_trades:
            return True
        
        realised = 0
        total = 0
        for symbol, activeTrade in self.active_trades.items():
            realised += activeTrade.realised_pnl
            total += activeTrade.total_pnl
        
        if total != 0 and (self.total_profit != total or self.realised_profit != realised):
            self.write_log(f"Total.PnL={round(self.total_profit, 1)}, Realised={round(self.realised_profit, 1)}")
        self.realised_profit = realised
        self.total_profit = total
        

    def check_pnl_risk(self) -> int:
        """ 
        check the profit and loss risk periodically. 
        return the level of risk by a number RiskLevel:
        RiskLevel:
            LevelNormal/LevelWarning/LevelCritical
        """
        riskLevel = RiskLevel.LevelZero
        if not self.active or not self.active_trades:
            return riskLevel
        
        if self.total_profit < self.realised_loss_limit or self.total_profit > self.realised_profit_limit:
            riskLevel = RiskLevel.LevelNormal
        
        elif (self.realised_profit < self.realised_loss_limit or
            self.total_profit < self.total_loss_limit or
            self.realised_profit > self.realised_profit_limit or
            self.total_profit > self.total_profit_limit
            ):
            riskLevel = RiskLevel.LevelWarning
        
        elif self.realised_profit < self.total_loss_limit or self.realised_profit > self.total_profit_limit:
            riskLevel = RiskLevel.LevelCritical

        return riskLevel

    def check_risk(self, req: OrderRequest, gateway_name: str) -> bool:
        """"""
        if not self.active:
            return True
        riskLevel = self.check_pnl_risk()
        if riskLevel not in [RiskLevel.LevelZero, RiskLevel.LevelNormal]:
            self.write_log(f"Risk Management Warning:: current PnL risk level is {riskLevel}")
            return False

        # Check order volume
        if req.volume <= 0:
            self.write_log("委托数量必须大于0")
            return False

        if req.volume > self.order_size_limit:
            self.write_log(
                f"单笔委托数量{req.volume}，超过限制{self.order_size_limit}")
            return False

        # Check trade volume
        if self.trade_count >= self.trade_limit:
            self.write_log(
                f"今日总成交合约数量{self.trade_count}，超过限制{self.trade_limit}")
            return False

        # Check flow count
        if self.order_flow_count >= self.order_flow_limit:
            self.write_log(
                f"委托流数量{self.order_flow_count}，超过限制每{self.order_flow_clear}秒{self.order_flow_limit}次")
            return False

        # Check all active orders
        active_order_count: int = len(self.main_engine.get_all_active_orders())
        if active_order_count >= self.active_order_limit:
            self.write_log(
                f"当前活动委托次数{active_order_count}，超过限制{self.active_order_limit}")
            return False

        # Check order cancel counts
        order_cancel_count: int = self.order_cancel_counts.get(req.vt_symbol, 0)
        if order_cancel_count >= self.order_cancel_limit:
            self.write_log(f"当日{req.vt_symbol}撤单次数{order_cancel_count}，超过限制{self.order_cancel_limit}")
            return False

        # Check order self trade
        order_book: ActiveOrderBook = self.get_order_book(req.vt_symbol)
        if req.direction == Direction.LONG:
            best_ask: float = order_book.get_best_ask()
            if best_ask and req.price >= best_ask:
                self.write_log(f"买入价格{req.price}大于等于已挂最低卖价{best_ask}，可能导致自成交")
                return False
        else:
            best_bid: float = order_book.get_best_bid()
            if best_bid and req.price <= best_bid:
                self.write_log(f"卖出价格{req.price}小于等于已挂最低买价{best_bid}，可能导致自成交")
                return False

        # Add flow count if pass all checks
        self.order_flow_count += 1
        return True

    def check_is_cover(self,req: OrderRequest) -> bool:
        """
        check if the order is for cover the current outstanding trades/positions
        if it is orders to cover positions. return True. else False
        """
        if req and req.offset == Offset.COVER:
            return True
        return False

    def get_order_book(self, vt_symbol: str) -> "ActiveOrderBook":
        """"""
        order_book: Optional[ActiveOrderBook] = self.active_order_books.get(vt_symbol, None)
        if not order_book:
            order_book = ActiveOrderBook(vt_symbol)
            self.active_order_books[vt_symbol] = order_book
        return order_book


class ActiveOrderBook:
    """活动委托簿"""

    def __init__(self, vt_symbol: str) -> None:
        """"""
        self.vt_symbol: str = vt_symbol

        self.bid_prices: Dict[str, float] = {}
        self.ask_prices: Dict[str, float] = {}

    def update_order(self, order: OrderData) -> None:
        """更新委托数据"""
        if order.is_active():
            if order.direction == Direction.LONG:
                self.bid_prices[order.vt_orderid] = order.price
            else:
                self.ask_prices[order.vt_orderid] = order.price
        else:
            if order.vt_orderid in self.bid_prices:
                self.bid_prices.pop(order.vt_orderid)
            elif order.vt_orderid in self.ask_prices:
                self.ask_prices.pop(order.vt_orderid)

    def get_best_bid(self) -> float:
        """获取最高买价"""
        if not self.bid_prices:
            return 0
        return max(self.bid_prices.values())

    def get_best_ask(self) -> float:
        """获取最低卖价"""
        if not self.ask_prices:
            return 0
        return min(self.ask_prices.values())