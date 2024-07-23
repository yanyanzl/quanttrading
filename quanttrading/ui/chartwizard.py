
from copy import copy
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from tzlocal import get_localzone_name

from event import EventEngine, Event

from ordermanagement import MainEngine
from ui import QtWidgets, QtCore
# from event import EVENT_TICK
from datatypes import ContractData, TickData, BarData, SubscribeRequest, Interval
from utility import BarGenerator, ZoneInfo
from constant import (
    # Interval,
    Exchange,
    EVENT_TICK,
    EVENT_HISDATA,
    EVENT_TIMER
)
from .chart import Chart
# from vnpy_spreadtrading.base import SpreadItem, EVENT_SPREAD_DATA

# from ..engine import APP_NAME, EVENT_CHART_HISTORY, ChartWizardEngine

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

    def create_chart(self) -> Chart:
        """创建图表对象"""
        chart: Chart = Chart("Real Time Chart", "TSLA")
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
        vt_symbol: str = self.symbol_line.text()
        if not vt_symbol:
            return

        if vt_symbol in self.charts:
            return

        # if "LOCAL" not in vt_symbol:
        #     contract: Optional[ContractData] = self.main_engine.get_contract(vt_symbol)
        #     if not contract:
        #         return

        # Create new chart
        self.bgs[vt_symbol] = BarGenerator(self.on_bar)

        chart: Chart = self.create_chart()
        self.charts[vt_symbol] = chart

        self.tab.addTab(chart, vt_symbol)

        # Query history data
        end: datetime = datetime.now(ZoneInfo(get_localzone_name()))
        start: datetime = end - timedelta(days=5)

        exchange = Exchange.SMART
        self.query_history(
            vt_symbol, 
            exchange, 
            "1m",
            start,
            end
        )

    def register_event(self) -> None:
        """注册事件监听"""
        self.signal_tick.connect(self.process_tick_event)
        self.signal_history.connect(self.process_history_event)
        self.signal_spread.connect(self.process_spread_event)

        self.event_engine.register(EVENT_HISDATA, self.signal_history.emit)
        self.event_engine.register(EVENT_TICK, self.signal_tick.emit)
        # self.event_engine.register(EVENT_SPREAD_DATA, self.signal_spread.emit)

    def process_tick_event(self, event: Event) -> None:
        """处理Tick事件"""
        tick: TickData = event.data
        bg: Optional[BarGenerator] = self.bgs.get(tick.vt_symbol, None)

        if bg:
            bg.update_tick(tick)

            chart: Chart = self.charts[tick.vt_symbol]
            bar: BarData = copy(bg.bar)
            bar.datetime = bar.datetime.replace(second=0, microsecond=0)
            chart.update_bar(bar)

    def process_history_event(self, event: Event) -> None:
        """处理历史事件"""
        history: List[BarData] = event.data
        if not history:
            return

        bar: BarData = history[0]
        chart: Chart = self.charts[bar.vt_symbol]
        chart.update_history(history)

        # Subscribe following data update
        contract: Optional[ContractData] = self.main_engine.get_contract(bar.vt_symbol)
        if contract:
            req: SubscribeRequest = SubscribeRequest(
                contract.symbol,
                contract.exchange
            )
            self.main_engine.subscribe(req, contract.gateway_name)

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
        chart: Chart = self.charts[bar.vt_symbol]
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
        from datatypes import HistoryRequest
        from data.finlib import Asset
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
