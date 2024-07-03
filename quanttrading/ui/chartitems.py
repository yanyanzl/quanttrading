"""
define all the items used in the chart
"""
from abc import abstractmethod
from typing import Tuple, List
import pyqtgraph as pg
from pandas import DataFrame
from .uiapp import QtGui, QtCore
from setting import Aiconfig
from datetime import datetime
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

    def clear_all():
        """
        clear all data and pictures.
        """
        pass

    @abstractmethod
    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        Get range of y-axis with given x-axis range.

        If min_ix and max_ix not specified, then return range with whole data set.
        """
        pass

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
        # self._index_x:int = -1
    
    def draw_candle(self, painter: QtGui.QPainter = None, index_x: int = None) -> None:
        """
        draw candle with provided painter
        """
        p = painter
        if p is None:
            self.picture = QtGui.QPicture()
            p = QtGui.QPainter(self.picture)

        data = self._data

        if index_x is None:
            index_x = data.first_valid_index()

        w = self._candle_width

        # print(f"data.iloc[0]['Open'] is {data.iloc[0]['Open']}")
        # print(f"data.first_valid_index is {index_x}")
        # print(f"data.at[data.first_valid_index,'Open'] is {data.at[index_x, 'Open']}")
        # print(f"data.iat[0,0] is {data.iat[0,0]}")
        # print(f"data.iat[0,1] is {data.iat[0,1]}")
        # print(f"data['Open'].values[0] is {data['Open'].values[0]}")

        if data.at[index_x, 'Open'] > data.at[index_x, 'Close']:
            p.setBrush(self._down_brush)
            p.setPen(self._down_pen)
        else:
            p.setBrush(self._up_brush)
            p.setPen(self._up_pen)

        p.drawLine(QtCore.QPointF(index_x, data.at[index_x, 'Low']), QtCore.QPointF(index_x, data.at[index_x, 'High']))
        p.drawRect(QtCore.QRectF(index_x-w, data.at[index_x, 'Open'], w * 2, data.at[index_x, 'Close'] - data.at[index_x, 'Open']))


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

        candle_num = 0
        data_len = len(self._data.index)
        if data_len > self.max_candle:
            candle_num = data_len - self.max_candle

        data: DataFrame = self._data[candle_num:]
        candle_num = len(data.index)

        i = 0
        while i < candle_num:
            candle = CandlestickItem(data.iloc[[i]])
            candle.draw_candle(p)
            i += 1

        p.end()

    def update():

        pass

class DataManager():

    def __init__(self, data: DataFrame = None):
        self._data = data



    pass

class DatetimeAxis(pg.AxisItem):
    """
    Datetime Axis for the X-Axis
    """
    pg.DateAxisItem
    def __init__(self, datamanager: DataManager, *args, **kwargs) -> None:
        """"""
        super().__init__(*args, **kwargs)

        self._manager: DataManager = datamanager

        self.setPen(width= Aiconfig.get('AXIS_WIDTH'))
        self.tickFont: QtGui.QFont = Aiconfig.get('NORMAL_FONT')

    def tickStrings(self, values: List[int], scale: float, spacing: int) -> list:
        """
        Convert original index to datetime string.
        """
        # Show no axis string if spacing smaller than 1
        if spacing < 1:
            return ["" for i in values]

        strings: list = []

        for ix in values:
            dt: datetime = self._manager.get_datetime(ix)

            if not dt:
                s: str = ""
            elif dt.hour:
                s: str = dt.strftime("%Y-%m-%d\n%H:%M:%S")
            else:
                s: str = dt.strftime("%Y-%m-%d")

            strings.append(s)

        return strings



