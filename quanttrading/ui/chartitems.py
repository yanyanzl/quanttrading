"""
define all the items used in the chart
"""

import pyqtgraph as pg
from pandas import DataFrame
from .uiapp import QtGui, QtCore
from setting import Aiconfig
from data.finlib import Asset


class ChartBase(pg.GraphicsObject):
    """
    base class for chart related Item. 
    """
    def __init__(self, data: DataFrame = None):
        pg.GraphicsObject.__init__(self)
        # data must be a DataFrame include time, open
        # close, high, low
        self._data: DataFrame = data
        self.picture = QtGui.QPicture()

        self._up_pen: QtGui.QPen = pg.mkPen(
            color=Aiconfig.get("UP_COLOR"), 
            width=Aiconfig.get("PEN_WIDTH")
        )
        self._up_brush: QtGui.QBrush = pg.mkBrush(color=Aiconfig.get("UP_COLOR"))

        self._down_pen: QtGui.QPen = pg.mkPen(
            color=Aiconfig.get("DOWN_COLOR"),
            width=Aiconfig.get("PEN_WIDTH")
        )
        self._down_brush: QtGui.QBrush = pg.mkBrush(color=Aiconfig.get("DOWN_COLOR"))
        self._candle_width = Aiconfig.get("CANDLE_WIDTH")

    def generate_picture(self):
        """
        pre-computing a QPicture object allows paint() to run much more quickly,
        rather than re-drawing the shapes every time.
        """
        pass

    def update(self):
        """
        only update the drawing for the changed part of the data
        """
        pass

    def update_all(self):
        """
        update the whole drawing
        """
        self.generate_picture()

    def append(self, data) -> bool:
        """
        add one record (one Candle) data to the dataframe.
        """
        self._data.apend(data)
        self.update(self)
        pass

    def remove(self, data=None, Head=True) -> bool:
        """
        remove one candle's data from the dataframe.
        default (data=None and Head = True), remove the first candle
        data = None and head = False, remove the last candle
        """
        if data is None:
            if Head:
                self._data = self._data.drop([0])
            else:
                self._data = self._data.drop([self._data.last_valid_index()])
        else:
            # if self.data.isin(data):
            #     self.data.drop()
            pass

        self.update(self)

    def paint(self, painter: QtGui.QPainter, *args):
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        """ 
        boundingRect _must_ indicate the entire area that will be drawn on
        or else we will get artifacts and possibly crashing.
        (in this case, QPicture does all the work of computing the bouning rect for us)
        """
        return QtCore.QRectF(self.picture.boundingRect())


class CandlestickItem(ChartBase):
    def __init__(self, data: DataFrame = None):
        super().__init__(data)
    
    def draw_candle(self, index_x: int, painter: QtGui.QPainter = None) -> None:
        """
        draw candle with provided painter
        """
        p = painter
        if p is None:
            self.picture = QtGui.QPicture()
            p = QtGui.QPainter(self.picture)
        data = self._data
        w = self._candle_width
        # print(f"data is {data}")
        # print(f"data['Open'] is {data['Open'].values}")
        # print(f"data['Open'] is {data['Open'].values[0]}")
        # print(f"data is {data.values}")
        # print(f"data is {data.values[0]}")
        print(f"data['Open'] is {data.iloc[0]['Open']}")
        # print(f"data['Open'] is {data['Open'][1]}")
        # if data[['Open']] > data['Close']:
        #     p.setBrush(self._down_brush)
        #     p.setPen(self._down_pen)
        # else:
        #     p.setBrush(self._up_brush)
        #     p.setPen(self._up_pen)

        # p.drawLine(QtCore.QPointF(index_x, data['Low']), QtCore.QPointF(index_x, data['High']))
        # p.drawRect(QtCore.QRectF(index_x-w, data['Open'], w * 2, data['Close'] - data['Open']))


class CandlestickItems(ChartBase):
    """
    candlesticks object for the chart
    Create a subclass of GraphicsObject.
    The only required methods are paint() and boundingRect() 
    (see QGraphicsItem documentation)
    """
    def __init__(self, data):
        super().__init__(data)

        self.max_candle = Aiconfig.get("MAX_NUM_CANDLE")

        # self.data: DataFrame = data
        self.generate_picture()

    def generate_picture(self):
        """
        pre-computing a QPicture object allows paint() to run much more quickly, 
        rather than re-drawing the shapes every time.
        """
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('w'))
        # print(f"self._data is {self._data}")

        data: DataFrame = self._data[:self.max_candle]
        # print(f"data is {data.iloc[0:3]}")
        # print(f"last_valid_index is {data.iloc[[3]]}")

        i = 0
        while i < 5:
            print(i)
            candle = CandlestickItem(data.iloc[[i]])
            candle.draw_candle(i, p)
            i += 1

        p.end()

    def update():

        pass