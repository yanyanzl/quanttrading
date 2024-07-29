

from event import EventEngine
from ordermanagement import MainEngine
from ui.uiapp import QtWidgets, QtCore
from constant import RiskLevel

from ..engine import APP_NAME, RiskEngine


class RiskManager(QtWidgets.QDialog):
    """"""

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        self.rm_engine: RiskEngine = main_engine.get_engine(APP_NAME)

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle("Risk Management")

        # Create widgets
        self.active_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.active_combo.setMinimumWidth(80)
        self.active_combo.addItems(["Stop", "Start"])

        self.flow_limit_spin: RiskManagerSpinBox = RiskManagerSpinBox()
        self.flow_clear_spin: RiskManagerSpinBox = RiskManagerSpinBox()
        self.size_limit_spin: RiskManagerSpinBox = RiskManagerSpinBox()
        self.trade_limit_spin: RiskManagerSpinBox = RiskManagerSpinBox()
        self.active_limit_spin: RiskManagerSpinBox = RiskManagerSpinBox()
        self.cancel_limit_spin: RiskManagerSpinBox = RiskManagerSpinBox()

        # PnL limits
        self.total_profit_limit_spin: RiskManagerSpinBox = RiskManagerSpinBox()
        self.realised_profit_limit_spin: RiskManagerSpinBox = RiskManagerSpinBox()
        self.total_loss_limit_spin: RiskManagerSpinBox = RiskManagerSpinBox()
        self.realised_loss_limit_spin: RiskManagerSpinBox = RiskManagerSpinBox()
        self.total_loss_limit_spin.setMinimum(-1000)
        self.total_loss_limit_spin.setMaximum(-10)
        self.realised_loss_limit_spin.setMinimum(-1000)
        self.realised_loss_limit_spin.setMaximum(-10)

        # freeze trading level: 
        self.freeze_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.freeze_combo.setMinimumWidth(80)
        self.freeze_combo.addItems(["No", "Freeze"])

        save_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(self.save_setting)


        # Form layout
        form: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        form.addRow("Risk mgmt status", self.active_combo)
        form.addRow("委托流控上限（笔）", self.flow_limit_spin)
        form.addRow("委托流控清空（秒）", self.flow_clear_spin)
        form.addRow("单笔委托上限（数量）", self.size_limit_spin)
        form.addRow("总成交上限（笔）", self.trade_limit_spin)
        form.addRow("活动委托上限（笔）", self.active_limit_spin)
        form.addRow("合约撤单上限（笔）", self.cancel_limit_spin)

        # PnL limits
        form.addRow("Total Profit Limit: ", self.total_profit_limit_spin)
        form.addRow("Realised Profit Limit: ", self.realised_profit_limit_spin)
        form.addRow("Total Loss Limit: ", self.total_loss_limit_spin)
        form.addRow("Realised Loss Limit: ", self.realised_loss_limit_spin)

        # freeze trading level: 
        form.addRow("Freeze trade when PnL limits reached: ", self.freeze_combo)

        form.addRow(save_button)

        self.setLayout(form)

        # Set Fix Size
        hint: QtCore.QSize = self.sizeHint()
        self.setFixedSize(int(hint.width() * 1.2), hint.height())

    def save_setting(self) -> None:
        """"""
        active_text: str = self.active_combo.currentText()
        if active_text == "Start":
            active: bool = True
        else:
            active: bool = False

        freeze_text: str = self.freeze_combo.currentText()
        if freeze_text == "Freeze":
            freeze: bool = True
        else:
            freeze: bool = False

        setting: dict = {
            "active": active,
            "order_flow_limit": self.flow_limit_spin.value(),
            "order_flow_clear": self.flow_clear_spin.value(),
            "order_size_limit": self.size_limit_spin.value(),
            "trade_limit": self.trade_limit_spin.value(),
            "active_order_limit": self.active_limit_spin.value(),
            "order_cancel_limit": self.cancel_limit_spin.value(),

            "total_profit_limit": self.total_profit_limit_spin.value(),
            "realised_profit_limit": self.realised_profit_limit_spin.value(),
            "total_loss_limit": self.total_loss_limit_spin.value(),
            "realised_loss_limit": self.realised_loss_limit_spin.value(),

            "freeze": freeze,
        }

        self.rm_engine.update_setting(setting)
        self.rm_engine.save_setting()

        self.close()

    def update_setting(self) -> None:
        """
        update the UI fields numbers based on the current setting
        """
        setting: dict = self.rm_engine.get_setting()
        if setting["active"]:
            self.active_combo.setCurrentIndex(1)
        else:
            self.active_combo.setCurrentIndex(0)

        if setting["freeze"]:
            self.freeze_combo.setCurrentIndex(1)
        else:
            self.freeze_combo.setCurrentIndex(0)

        self.flow_limit_spin.setValue(setting["order_flow_limit"])
        self.flow_clear_spin.setValue(setting["order_flow_clear"])
        self.size_limit_spin.setValue(setting["order_size_limit"])
        self.trade_limit_spin.setValue(setting["trade_limit"])
        self.active_limit_spin.setValue(setting["active_order_limit"])
        self.cancel_limit_spin.setValue(setting["order_cancel_limit"])

        self.total_profit_limit_spin.setValue(setting["order_flow_limit"]),
        self.realised_profit_limit_spin.setValue(setting["realised_profit_limit"]),
        self.total_loss_limit_spin.setValue(setting["total_loss_limit"]),
        self.realised_loss_limit_spin.setValue(setting["realised_loss_limit"])

    def exec(self) -> None:
        """"""
        self.update_setting()
        super().exec()


class RiskManagerSpinBox(QtWidgets.QSpinBox):
    """"""

    def __init__(self, value: int = 0) -> None:
        """"""
        super().__init__()

        self.setMinimum(0)
        self.setMaximum(1_000_000_000)
        self.setValue(value)
