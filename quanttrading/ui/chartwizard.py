
from copy import copy
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from tzlocal import get_localzone_name

from event import EventEngine, Event
from pandas import DataFrame
import logging
from ordermanagement import MainEngine
from ui import QtWidgets, QtCore
# from event import EVENT_TICK
from datatypes import ContractData, TickData, BarData, SubscribeRequest, Interval, HistoryRequest
from utility import BarGenerator, ZoneInfo
from data.finlib import Asset

from constant import (
    # Interval,
    Exchange,
    EVENT_TICK,
    EVENT_HISDATA,
    EVENT_TICK_LAST_DATA,
    EVENT_TIMER
)
from .chart import Chart
from .chartitems import CandlestickItems, VolumeItem
# from vnpy_spreadtrading.base import SpreadItem, EVENT_SPREAD_DATA
# from ..engine import APP_NAME, EVENT_CHART_HISTORY, ChartWizardEngine

logger = logging.getLogger(__name__)

class ChartWizardWidget(QtWidgets.QWidget):
    """charts control widget"""

    signal_tick: QtCore.pyqtSignal = QtCore.pyqtSignal(Event)
    signal_spread: QtCore.pyqtSignal = QtCore.pyqtSignal(Event)
    signal_history: QtCore.pyqtSignal = QtCore.pyqtSignal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """ """
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        # self.chart_engine: ChartWizardEngine = main_engine.get_engine(APP_NAME)

        self.bgs: Dict[str, BarGenerator] = {}
        self.charts: Dict[str, Chart] = {}

        self.init_ui()
        self.register_event()

    def init_ui(self) -> None:
        """initialise UI part"""
        self.setWindowTitle("Candlestick Chart")

        self.tab: QtWidgets.QTabWidget = QtWidgets.QTabWidget()

        self.tab.setTabsClosable(True)
        self.tab.tabCloseRequested.connect(self.close_tab)

        self.symbol_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()

        self.button: QtWidgets.QPushButton = QtWidgets.QPushButton("New Chart")
        self.button.clicked.connect(self.new_chart)

        hbox: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel("Ticker"))
        hbox.addWidget(self.symbol_line)
        hbox.addWidget(self.button)
        hbox.addStretch()

        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.tab)

        self.setLayout(vbox)

    def create_chart(self, symbol:str=None) -> Chart:
        """创建图表对象"""
        chart: Chart = Chart("Real Time Chart", symbol)
        chart.add_plot("candle", hide_x_axis=False)
        chart.add_plot("volume", maximum_height=200)
        chart.add_item(CandlestickItems, "candle", "candle")
        chart.add_item(VolumeItem, "volume", "volume")
        chart.add_cursor()
        return chart

    def show(self) -> None:
        """最大化显示"""
        self.showMaximized()

    def close_tab(self, index: int) -> None:
        """关闭标签"""
        vt_symbol: str = self.tab.tabText(index)

        self.tab.removeTab(index)
        self.charts.pop(vt_symbol)
        self.bgs.pop(vt_symbol)

    def new_chart(self) -> None:
        """创建新的图表"""
        # Filter invalid vt_symbol
        symbol: str = self.symbol_line.text()
        if not symbol:
            return

        if symbol in self.charts:
            return

        # if "LOCAL" not in symbol:
        #     contract: Optional[ContractData] = self.main_engine.get_contract(symbol)
        #     if not contract:
        #         return

        # Create new chart
        self.bgs[symbol] = BarGenerator(self.on_bar)

        chart: Chart = self.create_chart(symbol)
        self.charts[symbol] = chart

        self.tab.addTab(chart, symbol)

        # Query history data
        end: datetime = datetime.now(ZoneInfo(get_localzone_name()))
        start: datetime = end - timedelta(days=1)

        exchange = Exchange.SMART
        self.query_history(
            symbol, 
            exchange, 
            "1m",
            start,
            end
        )
    
    def new_interval(self, symbol:str, interval:Interval) -> None:
        """
        change the chart interval for an existing chart
        """
        # Filter invalid vt_symbol
        if not symbol or not interval or symbol not in self.charts:
            return

        # Query history data
        start, end = self._getStartEndByIntervale(interval)
        exchange = Exchange.SMART
        self.query_history(
            symbol, 
            exchange, 
            interval,
            start,
            end
        )

    def _getStartEndByIntervale(self, interval:Interval) -> tuple[datetime, datetime]:
        """
        return start and end as datetime format based on Interval.
        Literal['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '1wk']
        """
        if not interval:
            return None
        days = 1
        if interval in ['1m', '2m']:
            pass
        elif interval in ['5m', '15m']:
            days = 5
        elif interval in ['30m', '60m', '90m', '1h']:
            days = 90
        elif interval in ['1d', '1wk']:
            days = 760

        end: datetime = datetime.now(ZoneInfo(get_localzone_name()))
        start: datetime = end - timedelta(days=days)
        return start, end


    def register_event(self) -> None:
        """注册事件监听"""
        self.signal_tick.connect(self.process_tick_event)
        self.signal_history.connect(self.process_history_event)
        # self.signal_spread.connect(self.process_spread_event)

        # This kind of different-thread problems happen all the
        #  time with Qt when you use multiple threads. 
        # The canonical way to solve this problem is to use signals and slots.
        # self.event_engine.register(EVENT_HISDATA, self.process_history_event)
        self.event_engine.register(EVENT_HISDATA, self.signal_history.emit)
        self.event_engine.register(EVENT_TICK_LAST_DATA, self.signal_tick.emit)
        # self.event_engine.register(EVENT_SPREAD_DATA, self.signal_spread.emit)

    def process_tick_event(self, event: Event) -> None:
        """process Tick Data Event"""
        tick: TickData = event.data
        logger.debug(f"entering  process_tick_event:: {tick.symbol=}")
        if tick is None:
            return
        symbol = tick.symbol
        # logger.info(f"entering  process_tick_event:: {self.bgs=}")
        bg: Optional[BarGenerator] = self.bgs.get(symbol, None)
        logger.debug(f"process_tick_event:: {bg=}")
        if bg:
            bg.update_tick(tick)

            chart: Chart = self.charts[tick.symbol]
            bar: BarData = copy(bg.bar)
            bar.datetime = bar.datetime.replace(second=0, microsecond=0)
            logger.debug(f"process_tick_event:: {bar=} ...... ")
            chart.update_bar(bar)

    def process_history_event(self, event: Event) -> None:
        """
        process the history data (candlestick data) for a symbol
        in a chart.
        """
        history: DataFrame = event.data
        if history is None or not isinstance(history, DataFrame) or history.empty:
            return

        symbol: str = history.at[history.first_valid_index(), 'Symbol']
        chart: Chart = self.charts[symbol]
        logger.info(f"ChartWizardWidget:: process the history event data:\n {len(history)}")
        chart.clearAll()
        chart.update_history(history)

        # Subscribe following data update
        contract: Optional[ContractData] = self.main_engine.get_contract(symbol)
        logger.info(f"ChartWizardWidget:: process the history :: after chart update_history"+
                    f"{symbol=} and {contract=}")
        # if contract:
        #     logger.info(f"ChartWizardWidget:: process the history :: enter if ...")
        #     req: SubscribeRequest = SubscribeRequest(
        #         contract.symbol,
        #         contract.exchange
        #     )
        #     self.main_engine.subscribe(req, contract.gateway_name)
        req: SubscribeRequest = SubscribeRequest(
                symbol,
                Exchange.SMART,
                'AllLast'
            )
        gateways = self.main_engine.get_all_gateway_names()
        if gateways is not None and len(gateways) > 0:
            self.main_engine.subscribe(req, gateways[0])

    def process_spread_event(self, event: Event) -> None:
        """处理价差事件"""
        # spread_item: SpreadItem = event.data
        # tick: TickData = TickData(
        #     symbol=spread_item.name,
        #     exchange=Exchange.LOCAL,
        #     datetime=spread_item.datetime,
        #     name=spread_item.name,
        #     last_price=(spread_item.bid_price + spread_item.ask_price) / 2,
        #     bid_price_1=spread_item.bid_price,
        #     ask_price_1=spread_item.ask_price,
        #     bid_volume_1=spread_item.bid_volume,
        #     ask_volume_1=spread_item.ask_volume,
        #     gateway_name="SPREAD"
        # )

        # bg: Optional[BarGenerator] = self.bgs.get(tick.vt_symbol, None)
        # if bg:
        #     bg.update_tick(tick)

        #     chart: Chart = self.charts[tick.vt_symbol]
        #     bar: BarData = copy(bg.bar)
        #     bar.datetime = bar.datetime.replace(second=0, microsecond=0)
        #     chart.update_bar(bar)
        pass

    def on_bar(self, bar: BarData) -> None:
        """K线合成回调"""
        chart: Chart = self.charts[bar.symbol]
        chart.update_bar(bar)

    def _query_history(
        self,
        vt_symbol: str,
        interval: Interval,
        start: datetime,
        end: datetime
    ) -> None:
        """"""
        # thread: Thread = Thread(
        #     target=self._query_history,
        #     args=[vt_symbol, interval, start, end]
        # )
        # thread.start()
        pass

    def query_history(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        start: datetime,
        end: datetime
    ) -> None:
        """"""

        req: HistoryRequest = HistoryRequest(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            start=start,
            end=end
        )

        # to be implement changes to select gateway?
        gateways = self.main_engine.get_all_gateway_names()
        if gateways is not None:
            self.main_engine.query_history(req, gateways[0])
        else:
            data = Asset(symbol).getMarketData(interval)
            event = Event(EVENT_HISDATA, data)
            self.event_engine.put(event)
        # else:
        #     # to be implemented for get data from database 
        #     # data: List[BarData] = self.database.load_bar_data(
        #     #     symbol,
        #     #     exchange,
        #     #     interval,
        #     #     start,
        #     #     end
        #     # )
        #     pass
