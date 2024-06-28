"""
This is the module for chart displaying and interactive
support real time data and data from files
"""

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

from pathlib import Path  # if you haven't already done so
from sys import path as pt
file = Path(__file__).resolve()
print(str(file.parents[1]))
pt.append(str(file.parents[1]))

from data.finlib import Asset

## Create a subclass of GraphicsObject.
## The only required methods are paint() and boundingRect() 
## (see QGraphicsItem documentation)
class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data  ## data must have fields: time, open, close, min, max
        self.generatePicture()
    
    def generatePicture(self):
        ## pre-computing a QPicture object allows paint() to run much more quickly, 
        ## rather than re-drawing the shapes every time.
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('w'))
        w = 1.0 / 3.
        print(f"w is {w}")
        data = self.data
        for dt in data.index:
            print(dt, " ", data['Open'][dt])
            p.drawLine(QtCore.QPointF(dt, data['Low'][dt]), QtCore.QPointF(dt, data['High'][dt]))
            if data['Open'][dt] > data['Close'][dt]:
                p.setBrush(pg.mkBrush('r'))
            else:
                p.setBrush(pg.mkBrush('g'))

            p.drawRect(QtCore.QRectF(dt-w, data['Open'][dt], w * 2, data['Close'][dt] - data['Open'][dt]))
        p.end()
    
    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        ## boundingRect _must_ indicate the entire area that will be drawn on
        ## or else we will get artifacts and possibly crashing.
        ## (in this case, QPicture does all the work of computing the bouning rect for us)
        return QtCore.QRectF(self.picture.boundingRect())


# data1 = Asset("AAPL").fetch_his_price(period=5)
# data1 = data1.reset_index()


# item = CandlestickItem(data1)
# plt = pg.plot()
# plt.addItem(item)
# plt.setWindowTitle('Customer chart for ')


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    print("i am here..................")
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QGuiApplication.instance().exec()
    # QtGui.QGuiApplication.instance .QApplication.instance().exec_()

