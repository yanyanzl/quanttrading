import sys

from PySide6.QtGui import Qt
# from PySide6.Qt import AlignmentFlag
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFontComboBox,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
    QFrame,
    QBoxLayout,
    QHBoxLayout,
    QGridLayout,
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Widgets App")

        layout = QGridLayout()
        # QBoxLayout(QBoxLayout.Direction.TopToBottom)
        # layout1 = QHBoxLayout()
        # layout2 = QHBoxLayout()
        # layout.add
        widgets = [

            QCheckBox,
            QComboBox,
            QDateEdit,
            QDateTimeEdit,
            QDial,
            QDoubleSpinBox,
            QFontComboBox,
            QLCDNumber,
            QLabel,
            QLineEdit,
            QProgressBar,
            QPushButton,
            QRadioButton,
            QSlider,
            QSpinBox,
            QTimeEdit,
            QFrame,
        ]

        # for widget in widgets:
        #     layout.addWidget(widget())
        # layout.addWidget(QCheckBox())
        # central_widget = QWidget()
        layout = QGridLayout()
        layout.addWidget(QFrame(), 0, 0, 2, 1,alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QComboBox(), 1, 0,Qt.AlignmentFlag.AlignLeft)
        central_widget = QFrame()
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()