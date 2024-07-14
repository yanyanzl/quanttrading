import sys

from PySide6.QtGui import Qt
from PySide6 import QtGui
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

import functools
def prettyPrint(printFunc):
    @functools.wraps(printFunc)
    def wrapper(*args, **kwargs):
        print(f"***"*20)
        printFunc(*args, **kwargs)
        print(f"***"*20)
    return wrapper

# globals()
# print(f"gloabls is {globals()}")
# print(f"gloabls attr is {getattr(globals(),"print")}")
# print(f"__builtins__ is {__builtins__}")

def wrapFunction(funcName:str):
    """
    wrap a function/method to a new one
    """
    # for m in ['setXRange', 'setYRange']:
    #     locals()[m] = _create_method(m)
    def _create_method(name):
        def method(self, *args, **kwargs):
            return getattr(self.vb, name)(*args, **kwargs)
        method.__name__ = name
        return method
    
    locals()[funcName] = _create_method(funcName)
    del _create_method

def wrapPrint():
    i = 3000
    from functools import partial
    printS = (partial(print,f"***"*20+"\n"))
    printS(f"hello printS is {i}")
    locals()["printS"] = printS

@prettyPrint
def findScreen():
    from PySide6.QtGui import QScreen
    application = QApplication()
    screen :QScreen = application.primaryScreen()
    print(f"screen.availableGeometry is {screen.availableGeometry()}")
    print(f"screen.availableSize is {screen.availableSize()}")
    print(f"screen.isLandscape is {screen.isLandscape(Qt.ScreenOrientation.LandscapeOrientation)}")

    print(f"screen.availableVirtualGeometry is {screen.availableVirtualGeometry()}")
    print(f"screen.availableVirtualSize is {screen.availableVirtualSize()}")
    print(f"screen.dumpObjectTree is {screen.dumpObjectTree()}")
    application.shutdown()


def findFonts():
    """
    find the fonts info 
    """
    font_families = QtGui.QFontDatabase.families()
    print(f"all font families supported are {'***' * 10} \n {font_families}")

    cn_families = QtGui.QFontDatabase.families(QtGui.QFontDatabase.WritingSystem.SimplifiedChinese)
    print(f"chinese supported font families supported are {'***' * 10} \n {cn_families}")



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