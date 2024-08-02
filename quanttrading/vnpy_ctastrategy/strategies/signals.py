"""
multiple signal trigger the strategy.

"""
from abc import ABC, abstractmethod
from constant import (
    Exchange,
    EVENT_SIGNAL,
    )
from datatypes import TradingSignal, SignalType

from vnpy_ctastrategy import (
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
    CtaSignal,
    TargetPosTemplate
)
from event import Event


class BaseSignal(ABC):

    def __init__(self, symbol:str, on_signal:callable) -> None:
        """"""
        self.signal_pos = 0
        self.on_signal = on_signal
        self.symbol = symbol

    @abstractmethod
    def on_tick(self, tick: TickData) -> None:
        """
        Callback of new tick data update.
        """
        pass

    @abstractmethod
    def on_bar(self, bar: BarData) -> None:
        """
        Callback of new bar data update.
        """
        pass

    def set_signal_pos(self, pos) -> None:
        """"""
        if self.signal_pos != pos:
            self.send_signal(pos)
            self.signal_pos = pos

    def get_signal_pos(self):
        """"""
        return self.signal_pos

    @abstractmethod
    def send_signal(self, pos) -> None:
        """ """
        pass

class RSISignal(BaseSignal):
    """ 
     Relative Strenght Index (RSI) signal 
    """

    def __init__(self, symbol:str, on_signal:callable, rsi_window: int, rsi_level: float):
        """
        Constructor.
        rsi_window: period of the RSI
        rsi_level: level to trigger signal
        high will be 50 + rsi_level and 
        low will be 50 - rsi_level
        if rsi level < low. trigger rsi signal : -1
        if rsi level > high. trigger rsi signal : 1
        otherwise signal : 0
        """
        super().__init__(symbol, on_signal)

        self.rsi_window = rsi_window
        self.rsi_level = rsi_level
        self.rsi_long = 50 + self.rsi_level
        self.rsi_short = 50 - self.rsi_level

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        # check this part and update the detail of the calculation
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)

        rsi_value = self.am.rsi(self.rsi_window)

        if rsi_value >= self.rsi_long:
            self.set_signal_pos(1)
        elif rsi_value <= self.rsi_short:
            self.set_signal_pos(-1)
        else:
            self.set_signal_pos(0)
    
    def send_signal(self, pos) -> None:
        signal: TradingSignal = TradingSignal(type=SignalType.SIGNAL_RSI, symbol=self.symbol, value=pos)
        event: Event = Event(EVENT_SIGNAL, signal)
        print(f"sending signal now: {signal=}")
        self.on_signal(event)


class CCISignal(BaseSignal):
    """ 
    Commodity Channel Index (CCI) Signal 
    measures the current price level relative to an average 
    price level over a given period of time. 

    CCI is relatively high when prices are far above their average. 
    CCI is relatively low when prices are far below their average.

    When the CCI is above zero, it indicates the price is above 
    the historic average. Conversely, when the CCI is below zero,
      the price is below the historic average.

    """

    def __init__(self, symbol:str, on_signal:callable, cci_window: int, cci_level: float):
        """ 
        cci_window: period of CCI
        cci_level: level to trigger the cci signal
        if cci level < - cci_level. trigger cci signal : -1
        if cci level > cci_level. trigger cci signal : 1
        otherwise signal : 0
        The CCI is an unbounded oscillator, meaning it can go higher or
          lower indefinitely. For this reason, overbought and oversold
            levels are typically determined for each individual asset by
              looking at historical extreme CCI levels where the price 
              reversed from
        """
        super().__init__(symbol, on_signal)

        self.cci_window = cci_window
        self.cci_level = cci_level
        self.cci_long = self.cci_level
        self.cci_short = -self.cci_level

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)

        cci_value = self.am.cci(self.cci_window)

        if cci_value >= self.cci_long:
            self.set_signal_pos(1)
        elif cci_value <= self.cci_short:
            self.set_signal_pos(-1)
        else:
            self.set_signal_pos(0)

    def send_signal(self, pos) -> None:
        signal: TradingSignal = TradingSignal(type=SignalType.SIGNAL_CCI, symbol=self.symbol, value=pos)
        event: Event = Event(EVENT_SIGNAL, signal)
        self.on_signal(event)

class MacrossSignal(BaseSignal):
    """ 
    Fast and Slow Moving Averages Crossover signal 
    The fast and slow moving average crossover strategy is a 
    quantitative trading strategy that generates trading signals by
      comparing fast and slow moving averages. It goes long when the
        fast MA crosses above the slow MA, and goes short when the 
        fast MA crosses below the slow MA. The strategy aims to capture
          trend turning points on the medium-short term timeframe
    """

    def __init__(self, symbol:str, on_signal:callable, fast_window: int, slow_window: int):
        """
        fast_window: period for short term SMA. example 50
        slow_window: period for long term SMA. example 200
        long when fast MA crosses above slow MA. signal : 1
        short when fast MA crosses below slow MA. signal : -1

        The fast MA reacts swiftly to price changes and reflects the
          latest trend. The slow MA filters out low frequency noises
            and captures the major trend. Crossovers signal potential
              trend reversals for improved trading accuracy.
        """
        super().__init__(symbol, on_signal)

        self.fast_window = fast_window
        self.slow_window = slow_window

        self.bg = BarGenerator(self.on_bar, 5, self.on_5min_bar)
        self.am = ArrayManager()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_5min_bar(self, bar: BarData):
        """"""
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)

        fast_ma = self.am.sma(self.fast_window)
        slow_ma = self.am.sma(self.slow_window)

        if fast_ma > slow_ma:
            self.set_signal_pos(1)
        elif fast_ma < slow_ma:
            self.set_signal_pos(-1)
        else:
            self.set_signal_pos(0)

    def send_signal(self, pos) -> None:
        signal: TradingSignal = TradingSignal(type=SignalType.SIGNAL_MA, symbol=self.symbol, value=pos)
        event: Event = Event(EVENT_SIGNAL, signal)
        self.on_signal(event)

class Signals(TargetPosTemplate):
    """ multi-signal strategy class """

    author = "Steven Jiang"

    rsi_window = 14
    rsi_level = 20
    cci_window = 30
    cci_level = 10
    fast_window = 5
    slow_window = 20
    exchange = Exchange.SMART

    signal_pos = {}
    # parameters is used to control the signal parameters like:
    # period, trigger level etc. which is different for different
    # strategy signals.
    parameters = ["exchange", "rsi_window", "rsi_level", "cci_window",
                  "cci_level", "fast_window", "slow_window"]
    
    variables = ["signal_pos"]

    def __init__(self, cta_engine, strategy_name, symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, symbol, setting)

        self.rsi_signal = RSISignal(symbol, self.on_signal, self.rsi_window, self.rsi_level)
        self.cci_signal = CCISignal(symbol, self.on_signal, self.cci_window, self.cci_level)
        self.ma_signal = MacrossSignal(symbol, self.on_signal, self.fast_window, self.slow_window)
        
        self.signal_pos = {
            "rsi": 0,
            "cci": 0,
            "ma": 0
        }

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("Signal generation initialize started")
        self.load_bar(10)
    
    def on_signal(self, event:Event):
        """
        """
        self.cta_engine.put_event(event)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("Signal generation started")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("Sginal stopped")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        # super(Signals, self).on_tick(tick)

        self.rsi_signal.on_tick(tick)
        self.cci_signal.on_tick(tick)
        self.ma_signal.on_tick(tick)

        # self.calculate_target_pos()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        # super(Signals, self).on_bar(bar)

        self.rsi_signal.on_bar(bar)
        self.cci_signal.on_bar(bar)
        self.ma_signal.on_bar(bar)

        # self.calculate_target_pos()

    def calculate_target_pos(self):
        """"""
        # self.signal_pos["rsi"] = self.rsi_signal.get_signal_pos()
        # self.signal_pos["cci"] = self.cci_signal.get_signal_pos()
        # self.signal_pos["ma"] = self.ma_signal.get_signal_pos()

        # target_pos = 0
        # for v in self.signal_pos.values():
        #     target_pos += v

        # self.set_target_pos(target_pos)
        pass

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        # super(Signals, self).on_order(order)
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        # self.put_event()
        pass

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
