from abc import ABC, abstractmethod
from copy import copy
from typing import Any, Callable, List

# from constant import Interval, Direction, Offset
from datatypes import BarData, TickData, OrderData, TradeData
from utility import virtual

from .base import StopOrder, EngineType


class BacktestTemplate(ABC):
    """ 
    This is the base class for every strategy to inherite from
    So we could do the back test for the strategy implement those
    attribute and methods for back testing.
    """

    author: str = "Steven J"
    parameters: list = []
    variables: list = []

    def __init__(
        self,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ) -> None:
        """
        these are all the all the parameters needed to initialise a 
        instance of the strategy by back test engine.
        every strategy should inherite from this class to be able to do
        the back test. make sure the strategy could be created by:
        strategy_class(
            engine, strategy_class.__name__, symbol, settings
        )
        plus one more requirement: the strategy should call it's own
        engine's send_order method for every single order. for back test,
        the backtestingEngine will create the strategy with it self as
        the strategy's engine (also baseengine type). So the backtestingengine
        will get all orders from the strategy.
        the send_order method should compatible with the following 
        parameter sequence. :
        def send_order(
            self,
            strategy: BacktestTemplate,
            direction: Direction,
            offset: Offset,
            price: float,
            volume: float,
            stop: bool = False,
            lock: bool = False,
            net: bool = False
        )
        """

        # used by backtesting engine also.
        self.strategy_name: str = strategy_name

        self.vt_symbol: str = vt_symbol
        self.symbol: str = ""
        if vt_symbol and "." in vt_symbol:
            self.symbol = vt_symbol.split('.')[0]

        # used by backtesting engine to mark the status of the strategy
        self.inited: bool = False
        self.trading: bool = False

        # position already hold for this strategy. add when long
        # subtract when short. By engine or backtest engine
        self.pos: int = 0

        # Copy a new variables list here to avoid duplicate insert when multiple
        # strategy instances are created with the same strategy class.
        self.variables = copy(self.variables)
        self.variables.insert(0, "inited")
        self.variables.insert(1, "trading")
        self.variables.insert(2, "pos")

        self.update_setting(setting)

    # ========== this part is used to be called to create strategy
    # instances. So that it could setting those parameters.
    def update_setting(self, setting: dict) -> None:
        """
        Update strategy parameter wtih value in setting dict.
        add those parameters to be attributes of the strategy.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])

    @classmethod
    def get_class_parameters(cls) -> dict:
        """
        Get default parameters dict of strategy class.
        """
        class_parameters: dict = {}
        for name in cls.parameters:
            class_parameters[name] = getattr(cls, name)
        return class_parameters

    def get_parameters(self) -> dict:
        """
        Get strategy parameters dict.
        """
        strategy_parameters: dict = {}
        for name in self.parameters:
            strategy_parameters[name] = getattr(self, name)
        return strategy_parameters

    def get_variables(self) -> dict:
        """
        Get strategy variables dict.
        """
        strategy_variables: dict = {}
        for name in self.variables:
            strategy_variables[name] = getattr(self, name)
        return strategy_variables

    def get_data(self) -> dict:
        """
        Get strategy data.
        """
        strategy_data: dict = {
            "strategy_name": self.strategy_name,
            "vt_symbol": self.vt_symbol,
            "class_name": self.__class__.__name__,
            "author": self.author,
            "parameters": self.get_parameters(),
            "variables": self.get_variables(),
        }
        return strategy_data

    # =============== this part is action when receiving those
    # callbacks.
    @abstractmethod
    def on_init(self) -> None:
        """
        for back testing
        Callback when strategy is inited.
        """
        pass

    @abstractmethod
    def on_start(self) -> None:
        """
        for back testing
        Callback when strategy is started.
        """
        pass

    @abstractmethod
    def on_stop(self) -> None:
        """
        for back testing
        Callback when strategy is stopped.
        """
        pass

    @abstractmethod
    def on_tick(self, tick: TickData) -> None:
        """
        for back testing
        Callback of new tick data update.
        """
        pass

    @abstractmethod
    def on_bar(self, bar: BarData) -> None:
        """
        for back testing
        Callback of new bar data update.
        """
        pass

    @abstractmethod
    def on_trade(self, trade: TradeData) -> None:
        """
        for back testing
        Callback of new trade data update.
        """
        pass

    @abstractmethod
    def on_order(self, order: OrderData) -> None:
        """
        for back testing
        Callback of new order data update.
        """
        pass

    @abstractmethod
    def on_stop_order(self, stop_order: StopOrder) -> None:
        """
        for back testing
        Callback of stop order update.
        """
        pass
    

class BackTestExampleStrategy(BacktestTemplate):
    """"""
    tick_add = 1

    last_tick: TickData = None
    last_bar: BarData = None
    target_pos = 0

    def __init__(self, engine, strategy_name, vt_symbol, setting) -> None:
        """"""
        super().__init__(engine, strategy_name, vt_symbol, setting)

        self.active_orderids: list = []
        self.cancel_orderids: list = []

        self.variables.append("target_pos")

    @virtual
    def on_tick(self, tick: TickData) -> None:
        """
        Callback of new tick data update.
        """
        self.last_tick = tick

    @virtual
    def on_bar(self, bar: BarData) -> None:
        """
        Callback of new bar data update.
        """
        self.last_bar = bar

    @virtual
    def on_order(self, order: OrderData) -> None:
        """
        Callback of new order data update.
        """
        vt_orderid: str = order.vt_orderid

        if not order.is_active():
            if vt_orderid in self.active_orderids:
                self.active_orderids.remove(vt_orderid)

            if vt_orderid in self.cancel_orderids:
                self.cancel_orderids.remove(vt_orderid)

    def check_order_finished(self) -> bool:
        """"""
        if self.active_orderids:
            return False
        else:
            return True

    def set_target_pos(self, target_pos) -> None:
        """"""
        self.target_pos = target_pos
        self.trade()

    def trade(self) -> None:
        """"""
        if not self.check_order_finished():
            self.cancel_old_order()
        else:
            self.send_new_order()

    def cancel_old_order(self) -> None:
        """"""
        for vt_orderid in self.active_orderids:
            if vt_orderid not in self.cancel_orderids:
                self.cancel_order(vt_orderid)
                self.cancel_orderids.append(vt_orderid)

    def send_new_order(self) -> None:
        """"""
        pos_change = self.target_pos - self.pos
        if not pos_change:
            return

        long_price = 0
        short_price = 0

        if self.last_tick:
            if pos_change > 0:
                long_price = self.last_tick.ask_price_1 + self.tick_add
                if self.last_tick.limit_up:
                    long_price = min(long_price, self.last_tick.limit_up)
            else:
                short_price = self.last_tick.bid_price_1 - self.tick_add
                if self.last_tick.limit_down:
                    short_price = max(short_price, self.last_tick.limit_down)

        else:
            if pos_change > 0:
                long_price = self.last_bar.close_price + self.tick_add
            else:
                short_price = self.last_bar.close_price - self.tick_add

        if self.get_engine_type() == EngineType.BACKTESTING:
            if pos_change > 0:
                vt_orderids: list = self.buy(long_price, abs(pos_change))
            else:
                vt_orderids: list = self.short(short_price, abs(pos_change))
            self.active_orderids.extend(vt_orderids)

        else:
            if self.active_orderids:
                return

            if pos_change > 0:
                if self.pos < 0:
                    if pos_change < abs(self.pos):
                        vt_orderids: list = self.cover(long_price, pos_change)
                    else:
                        vt_orderids: list = self.cover(long_price, abs(self.pos))
                else:
                    vt_orderids: list = self.buy(long_price, abs(pos_change))
            else:
                if self.pos > 0:
                    if abs(pos_change) < self.pos:
                        vt_orderids: list = self.sell(short_price, abs(pos_change))
                    else:
                        vt_orderids: list = self.sell(short_price, abs(self.pos))
                else:
                    vt_orderids: list = self.short(short_price, abs(pos_change))
            self.active_orderids.extend(vt_orderids)
