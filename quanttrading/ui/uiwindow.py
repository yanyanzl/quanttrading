
"""
Implements main window of the trading platform.
"""

from types import ModuleType
import webbrowser
from functools import partial
from importlib import import_module
from typing import Callable, Dict, List, Tuple
import sys
import logging

from pathlib import Path  # if you haven't already done so
file = Path(__file__).resolve()
sys.path.append(str(file.parents[1]))

from vnpy_algotrading.ui.widget import AlgoManager, APP_NAME
# from .chart import Chart
# from .chartwizard import ChartWizardWidget
from .uiapp import QtCore, QtGui, QtWidgets
from .dataplot import DataPlot
from .widget import (
    BaseMonitor,
    TickMonitor,
    OrderMonitor,
    TradeMonitor,
    PositionMonitor,
    AccountMonitor,
    LogMonitor,
    ActiveOrderMonitor,
    ConnectDialog,
    ContractManager,
    TradingWidget,
    AboutDialog,
    GlobalDialog,
    ReloadDialog,
)
from ordermanagement import MainEngine, BaseApp
from event.engine import EventEngine
from utility import get_icon_path, TRADER_DIR
from constant import _

logger = logging.getLogger(__name__)

TAB_NAME = "central_tab"
DATA_PLOT_NAME = "data_plot"

class MainWindow(QtWidgets.QMainWindow):
    """
    Main window of the trading platform.
    """

    def __init__(self, main_engine, event_engine) -> None:
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.window_title: str = _("Quant Trading")

        self.widgets: Dict[str, QtWidgets.QWidget] = {}
        self.monitors: Dict[str, BaseMonitor] = {}
        # self.chartWidget: Chart = None

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle(self.window_title)
        self.init_dock()
        self.init_toolbar()
        self.init_menu()
        self.load_window_setting("custom")
        self.init_central()

    def init_dock(self) -> None:
        """"""
        self.trading_widget, trading_dock = self.create_dock(
            TradingWidget, _("Trading"), QtCore.Qt.LeftDockWidgetArea
        )
        tick_widget, tick_dock = self.create_dock(
            TickMonitor, _("MarketData"), QtCore.Qt.DockWidgetArea.RightDockWidgetArea
        )
        order_widget, order_dock = self.create_dock(
            OrderMonitor, _("Order"), QtCore.Qt.RightDockWidgetArea
        )
        active_widget, active_dock = self.create_dock(
            ActiveOrderMonitor, _("ActiveOrder"), QtCore.Qt.RightDockWidgetArea
        )
        trade_widget, trade_dock = self.create_dock(
            TradeMonitor, _("Trade"), QtCore.Qt.RightDockWidgetArea
        )
        log_widget, log_dock = self.create_dock(
            LogMonitor, _("Log"), QtCore.Qt.BottomDockWidgetArea
        )
        account_widget, account_dock = self.create_dock(
            AccountMonitor, _("Account"), QtCore.Qt.BottomDockWidgetArea
        )
        position_widget, position_dock = self.create_dock(
            PositionMonitor, _("Position"), QtCore.Qt.BottomDockWidgetArea
        )

        self.tabifyDockWidget(active_dock, order_dock)

        self.save_window_setting("default")

        tick_widget.itemDoubleClicked.connect(self.trading_widget.update_with_cell)
        position_widget.itemDoubleClicked.connect(self.trading_widget.update_with_cell)

    def init_central(self) -> None:
        """
        initiate the chart graph
        """
        # central_widget:QtWidgets.QFrame = QtWidgets.QFrame()
        # central_layout:QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        # central_widget.setLayout(central_layout)
        # self.widgets["central_widget"] = central_widget

        # to be changed: ***************
        # self.chartWidget = Chart("Real Time Chart", "TSLA")
        # self.chartWidget = ChartWizardWidget(self.main_engine,self.event_engine)
        
        tab = QtWidgets.QTabWidget(self,tabsClosable=True)
        self.widgets[TAB_NAME] = tab
        tab.setMovable(True)
        tab.tabCloseRequested.connect(self.remove_tab)

        _central = AlgoManager(self.main_engine, self.event_engine)
        self.widgets[APP_NAME] = _central

        tab.addTab(_central, APP_NAME)

        # central_layout.addWidget(_central)

        self.setCentralWidget(tab)

    
    def add_tab(self, widget:QtWidgets.QWidget, name:str) -> None:
        """
        add a tab to the tabwidget which is the central widget.
        """
        tab: QtWidgets.QTabWidget = self.widgets[TAB_NAME]
        if tab.indexOf(widget) == -1:
            tab.addTab(widget, name)
            self.widgets.update({name:widget})

        tab.setCurrentWidget(widget)
    
    def remove_tab(self, index:int) -> None:
        """
        remove a tab from the tabwidget which is the central widget.
        """
        try:
            tab: QtWidgets.QTabWidget = self.widgets[TAB_NAME]
            widget = tab.widget(index)
            name = tab.tabText(index)
            # widget.close()
            tab.removeTab(index)
            # self.widgets.pop(name)
        except Exception as e:
            logger.info(f"can't close the tab {name}, reason: {e.args}")

    def init_menu(self) -> None:
        """"""
        bar: QtWidgets.QMenuBar = self.menuBar()
        bar.setNativeMenuBar(False)     # for mac and linux

        # System menu
        sys_menu: QtWidgets.QMenu = bar.addMenu(_("System"))

        gateway_names: list = self.main_engine.get_all_gateway_names()
        for name in gateway_names:
            func: Callable = partial(self.connect, name)
            self.add_action(
                sys_menu,
                _("Connect {}").format(name),
                # get_icon_path(__file__, "connect.ico"),
                "connect.ico",
                func
            )

        sys_menu.addSeparator()

        self.add_action(
            sys_menu,
            _("退出"),
            # get_icon_path(__file__, "exit.ico"),
            "connect.ico",
            self.close
        )


        # App menu
        app_menu: QtWidgets.QMenu = bar.addMenu(_("Function"))

        all_apps: List[BaseApp] = self.main_engine.get_all_apps()
        for app in all_apps:
            ui_module: ModuleType = import_module(app.app_module + ".ui")
            widget_class: QtWidgets.QWidget = getattr(ui_module, app.widget_name)

            func: Callable = partial(self.open_widget, widget_class, app.app_name)

            self.add_action(app_menu, app.display_name, app.icon_name, func, True)


        # Global setting editor
        action: QtGui.QAction = QtWidgets.QAction(_("配置"), self)
        action.triggered.connect(self.edit_global_setting)
        bar.addAction(action)

        # Help menu
        help_menu: QtWidgets.QMenu = bar.addMenu(_("帮助"))

        self.add_action(
            help_menu,
            _("查询合约"),
            get_icon_path(__file__, "contract.ico"),
            partial(self.open_widget, ContractManager, "contract"),
            True
        )

        self.add_action(
            help_menu,
            _("Reload Module"),
            get_icon_path(__file__, "contract.ico"),
            self.reload_module,
            True
        )

        self.add_action(
            help_menu,
            _("Data Plot"),
            get_icon_path(__file__, "contract.ico"),
            self.data_plot,
            True
        )

        self.add_action(
            help_menu,
            _("还原窗口"),
            get_icon_path(__file__, "restore.ico"),
            self.restore_window_setting
        )

        self.add_action(
            help_menu,
            _("测试邮件"),
            get_icon_path(__file__, "email.ico"),
            self.send_test_email
        )

        self.add_action(
            help_menu,
            _("社区论坛"),
            get_icon_path(__file__, "forum.ico"),
            self.open_forum,
            True
        )

        self.add_action(
            help_menu,
            _("关于"),
            get_icon_path(__file__, "about.ico"),
            partial(self.open_widget, AboutDialog, "about"),
        )

    def init_toolbar(self) -> None:
        """"""
        self.toolbar: QtWidgets.QToolBar = QtWidgets.QToolBar(self)
        self.toolbar.setObjectName(_("工具栏"))
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)

        # Set button size
        w: int = 40
        size = QtCore.QSize(w, w)
        self.toolbar.setIconSize(size)

        # Set button spacing
        self.toolbar.layout().setSpacing(10)

        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbar)

    def add_action(
        self,
        menu: QtWidgets.QMenu,
        action_name: str,
        icon_name: str,
        func: Callable,
        toolbar: bool = False
    ) -> None:
        """"""
        icon: QtGui.QIcon = QtGui.QIcon(icon_name)

        action: QtGui.QAction = QtWidgets.QAction(action_name, self)
        action.triggered.connect(func)
        action.setIcon(icon)

        menu.addAction(action)

        if toolbar:
            self.toolbar.addAction(action)

    def create_dock(
        self,
        widget_class: QtWidgets.QWidget,
        name: str,
        area: int
    ) -> Tuple[QtWidgets.QWidget, QtWidgets.QDockWidget]:
        """
        Initialize a dock widget.
        """
        widget: QtWidgets.QWidget = widget_class(self.main_engine, self.event_engine)
        if isinstance(widget, BaseMonitor):
            self.monitors[name] = widget

        dock: QtWidgets.QDockWidget = QtWidgets.QDockWidget(name)
        dock.setWidget(widget)
        dock.setObjectName(name)
        dock.setFeatures(dock.DockWidgetFeature.DockWidgetFloatable | dock.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(area, dock)
        return widget, dock

    def connect(self, gateway_name: str) -> None:
        """
        Open connect dialog for gateway connection.
        """
        dialog: ConnectDialog = ConnectDialog(self.main_engine, gateway_name)
        dialog.exec()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Call main engine close function before exit.
        """
        reply = QtWidgets.QMessageBox.question(
            self,
            _("退出"),
            _("确认退出？"),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            for widget in self.widgets.values():
                widget.close()

            for monitor in self.monitors.values():
                monitor.save_setting()

            self.save_window_setting("custom")

            self.main_engine.close()

            event.accept()
        else:
            event.ignore()

    def open_widget(self, widget_class: QtWidgets.QWidget, name: str) -> None:
        """
        Open contract manager.
        """
        widget: QtWidgets.QWidget = self.widgets.get(name, None)
        if not widget:
            widget = widget_class(self.main_engine, self.event_engine)
            self.widgets[name] = widget

        if isinstance(widget, QtWidgets.QDialog):
            widget.exec()
        else:
            # tab:QtWidgets.QTabWidget = self.widgets[TAB_NAME]
            # tab.addTab(widget, name)
            self.add_tab(widget, name)
            # widget.show()

    def save_window_setting(self, name: str) -> None:
        """
        Save current window size and state by trader path and setting name.
        """
        settings: QtCore.QSettings = QtCore.QSettings(self.window_title, name)
        settings.setValue("state", self.saveState())
        settings.setValue("geometry", self.saveGeometry())

    def load_window_setting(self, name: str) -> None:
        """
        Load previous window size and state by trader path and setting name.
        """
        settings: QtCore.QSettings = QtCore.QSettings(self.window_title, name)
        state = settings.value("state")
        geometry = settings.value("geometry")

        if isinstance(state, QtCore.QByteArray):
            self.restoreState(state)
            self.restoreGeometry(geometry)

    def restore_window_setting(self) -> None:
        """
        Restore window to default setting.
        """
        self.load_window_setting("default")
        self.showMaximized()

    def send_test_email(self) -> None:
        """
        Sending a test email.
        """
        self.main_engine.send_email("quant trading", "testing")

    def open_forum(self) -> None:
        """
        """
        webbrowser.open("https://eagloo.co.uk")

    def edit_global_setting(self) -> None:
        """
        """
        dialog: GlobalDialog = GlobalDialog()
        dialog.exec()

    def reload_module(self) -> None:
        """
        """
        dialog: ReloadDialog = ReloadDialog()
        dialog.exec()

    def data_plot(self) -> None:
        """
        """
        if self.widgets.get(DATA_PLOT_NAME, None) is None:
            self.dataPlot = DataPlot(self.event_engine, 50)
        self.add_tab(self.dataPlot, DATA_PLOT_NAME)
        