"""
This is the module for chart displaying and interactive
support real time data and data from files
"""

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from PySide6 import QtWidgets
from pandas import DataFrame
# from abc import ABC


from pathlib import Path  # if you haven't already done so
from sys import path as pt
file = Path(__file__).resolve()
print(str(file.parents[1]))
pt.append(str(file.parents[1]))


pg.setConfigOptions(antialias=True)





class Chart(pg.PlotWidget):
    
    def __init__(self, parent: QtWidgets.QWidget=None, show=False, size=None, title=None, **kargs):
        super().__init__(parent, show, size, title, **kargs)

        self._init_ui()


    def _init_ui(self) -> None:
        """
        Init the UI framework  of the chart
        """
        self.setWindowTitle("Chart For Quant Trading")

        self._layout: pg.GraphicsLayout = pg.GraphicsLayout()
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(0)
        self._layout.setBorder(color='g', width=0.8)
        self._layout.setZValue(0)
        self.setCentralItem(self._layout)


# Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    print("i am here..................")
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QGuiApplication.instance().exec()
    # QtGui.QGuiApplication.instance .QApplication.instance().exec_()

