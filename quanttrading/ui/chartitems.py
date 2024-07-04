"""
define all the items used in the chart
"""
from abc import abstractmethod
from typing import Tuple, List
import pyqtgraph as pg
from pandas import DataFrame, Timestamp, concat
from .uiapp import QtGui, QtCore
from setting import Aiconfig
from datetime import datetime
from data.finlib import Asset


class DataManager():

    def __init__(self, data: DataFrame = None) -> None:
        self._data: DataFrame = data
        self._data.reset_index(inplace=True)
        self._xMax = 300  # the max visible data's index x
        self._xMin = 0      # the min visible data's index x

    def getDateTime(self, index: int) -> datetime:
        """
        get the datetime value for index=index in datas (DataFrame)
        return a datetime object
        """
        if self._data is None or self._data.empty or index not in self._data.index:
            return None
        else:
            date: Timestamp = self._data.loc[index]['Date']
            return date.to_pydatetime()
        
    def getData(self) -> DataFrame:
        return self._data
    
    def setData(self, data: DataFrame = None) -> bool:
        if isinstance(data, DataFrame):
            self._data = data
            self._data.reset_index(inplace=True)
            return True
        else:
            return False
        
    def append(self, data: DataFrame) -> bool:

        if isinstance(data, DataFrame) and not data.empty:
            self._data = concat([self._data, data], ignore_index=True)
            return True
        return False

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

    def getByIndex(self, index:int) -> DataFrame:
        """
        get a record in the DataFrame by it's index
        """
        if isinstance(index, int) and self._data is not None and index in self._data.index:
            data = self._data.iloc[[index]]
            # data = data.reindex(index=[index])
            return data
        else:
            return None

    def getXMax(self) -> int:
        """
        get the max x index in the current visible scope
        """
        return self._xMax

    def setXMax(self, max) -> bool:
        
        if isinstance(max, int) and max < len(self._data.index):
            self._xMax = max
            return True
        else:
            return False

    def getXMin(self) -> int:
        """
        the min visible data's index x
        """
        return self._xMin

    def setXMin(self, min) -> bool:
        """
        the min visible data's index x
        """
        if isinstance(min, int) and (0 <= min < len(self._data.index)):
            self._xMin = min
            return True
        else:
            return False

    def getYRange(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        get the min and max Y within the index of min_ix to max_ix
        """
        # print(f"min_ix is {min_ix} \n")
        # print(f"max_ix is {max_ix} \n")
        if isinstance(min_ix, int) and isinstance(max_ix, int) and min_ix < max_ix:
            if min_ix in self._data.index and max_ix in self._data.index:
                # print(self._data)
                data = self._data[min_ix:max_ix]
                # print(data)
                # data = self._data.iloc[min_ix, max_ix]
                min = data['Low'].min()
                max = data['High'].max()
                return (min, max)
        return None

    def lastIndex(self) -> int:
        """
        return the last element's index in the data list (DataFrame)
        """
        if self._data is not None and not self._data.empty:
            return self._data.last_valid_index()
        
        return None

    def getTotalDataNum(self) -> int:
        """
        return the total rows (records) in the Dataframe.
        """
        if not self.isEmpty():
            return len(self._data.index)

    def clearAll(self) -> None:
        self._data.drop(self._data.index, inplace=True)

    def isEmpty(self) -> bool:
        if self._data is None or self._data.empty:
            return True

        return False
    

class ChartBase(pg.GraphicsObject):
    """
    base class for chart related Item. 
    """
    def __init__(self, dataManager: DataManager = None):
        pg.GraphicsObject.__init__(self)
        # data must be a DataFrame include time, open
        # close, high, low
        self._dataManager: DataManager = dataManager
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

    def append(self, data: DataFrame) -> bool:
        """
        add one record (one Candle) data to the dataframe.
        """
        pass
        # self.update(self)

    def remove(self, data=None, Head=True) -> bool:
        """
        remove one candle's data from the dataframe.
        default (data=None and Head = True), remove the first candle
        data = None and head = False, remove the last candle
        """
        pass

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

    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show.
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
    """
    single candlestick item on the chart.
    """
    def __init__(self, dataManager: DataManager = None, index: int = None):
        super().__init__(dataManager)
        self._index_x: int = index
        self.dateTime = self._dataManager.getDateTime(index)

        data = self._dataManager.getByIndex(index)
        if data is not None:
            self.open = data.at[index, 'Open']
            self.close = data.at[index, 'Close']
            self.high = data.at[index, 'High']
            self.low = data.at[index, 'Low']

    def draw_candle(self, painter: QtGui.QPainter = None, index_x: int = None) -> None:
        """
        draw candle with provided painter
        """
        p = painter
        if p is None:
            self.picture = QtGui.QPicture()
            p = QtGui.QPainter(self.picture)

        data = None

        if index_x is None:
            index_x = self._index_x

        data = self._dataManager.getByIndex(index_x)
        if data is not None and not data.empty:
            w = self._candle_width

            if data.at[index_x, 'Open'] > data.at[index_x, 'Close']:
                p.setBrush(self._down_brush)
                p.setPen(self._down_pen)
            else:
                p.setBrush(self._up_brush)
                p.setPen(self._up_pen)

            p.drawLine(QtCore.QPointF(index_x, data.at[index_x, 'Low']), QtCore.QPointF(index_x, data.at[index_x, 'High']))
            p.drawRect(QtCore.QRectF(index_x-w, data.at[index_x, 'Open'], w * 2, data.at[index_x, 'Close'] - data.at[index_x, 'Open']))
        else:
            print(f"no data find in the datamanager index is {index_x}")


class CandlestickItems(ChartBase):
    """
    candlesticks object for the chart
    Create a subclass of GraphicsObject.
    The only required methods are paint() and boundingRect() 
    (see QGraphicsItem documentation)
    """
    def __init__(self, dataManager: DataManager):
        super().__init__(dataManager)

        self.max_candle = Aiconfig.get("MAX_NUM_CANDLE")

        # candlesticks list corresponding to the dataManager's data
        self._candles: List[CandlestickItem] = [CandlestickItem(dataManager, index) for index in dataManager._data.index]

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
        data_len = len(self._dataManager.getData().index)
        print(f"data_len in Candlestickitems is {data_len}")

        if data_len > self.max_candle:
            candle_num = data_len - self.max_candle
        self._dataManager.setXMin(candle_num)
        self._dataManager.setXMax(self._dataManager.lastIndex())

        # data: DataFrame = self._data[candle_num:]
        # candle_num = len(data.index)

        # i = candle_num
        i = candle_num
        max = self._dataManager.getXMax()
        while i < max:
            # candle = CandlestickItem(data.iloc[[i]])
            # candle = CandlestickItem(self._dataManager, i)
            # print(f"candlestickitems i is {i}")
            self._candles[i].draw_candle(p)
            # candle.draw_candle(p)
            i += 1

        p.end()

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        Get range of y-axis with given x-axis range.

        If min_ix and max_ix not specified, then return range with whole data set.
        """
        return self._dataManager.getYRange(min_ix, max_ix)
    

    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show by cursor.
        """
        # data: DataFrame = self._dataManager.getByIndex(ix)
        if not isinstance(ix, int):
            if isinstance(ix, float):
                ix = int(ix)
            else:
                print(f"ix in get_info_text is invalid. with value {ix}")
                return ""

        candle: CandlestickItem = CandlestickItem(self._dataManager, ix)

        if candle is not None and candle._index_x is not None and candle.dateTime is not None:
            # print(f"candle is {candle}")
            # print(f"candle.dateTime is {candle.dateTime}")
            words: list = [
                "Date",
                candle.dateTime.strftime("%Y-%m-%d"),
                "",
                "Time",
                candle.dateTime.strftime("%H:%M"),
                "",
                "Open",
                str(candle.open),
                "",
                "High",
                str(candle.high),
                "",
                "Low",
                str(candle.low),
                "",
                "Close",
                str(candle.close)
            ]
            text: str = "\n".join(words)
        else:
            print(f"no candle exist, index is {ix}")
            text: str = ""

        return text

    def update():

        pass


class DatetimeAxis(pg.AxisItem):
    """
    Datetime Axis for the X-Axis
    """
    # pg.DateAxisItem() to check whether this object could meet the requirements.

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
            dt: datetime = self._manager.getDateTime(ix)

            if not dt:
                s: str = ""
            elif dt.hour:
                s: str = dt.strftime("%Y-%m-%d\n%H:%M:%S")
            else:
                s: str = dt.strftime("%Y-%m-%d")

            strings.append(s)

        return strings



