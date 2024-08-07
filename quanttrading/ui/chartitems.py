"""
define all the items used in the chart
"""
from dataclasses import dataclass
from abc import abstractmethod
from typing import Tuple, List, Dict
import pyqtgraph as pg
from pandas import DataFrame, Timestamp, concat
import pandas as pd
from .uiapp import QtGui, QtCore, QtWidgets
from setting import Aiconfig
from datetime import datetime
from ordermanagement import MainEngine
from data.finlib import Asset
from constant import (
    ChartInterval, 
    ChartPeriod,
)

import logging

logger = logging.getLogger(__name__)

class DataManager():
    """
    Provides chart data management system function.
    all chart related data will be requested by gateway(app)
    and received by gateway(app). then gateway will sent
    those data wrapped in an Event to eventengine.
    ChartDataManagement will retrieve the data from 
    the eventengine, process those data and update the chart
    """
    MIN_BAR_COUNT = Aiconfig.get("MIN_BAR_COUNT")

    def __init__(self, assetName: str = None) -> None:
        self._data: DataFrame = None
        # self._data.reset_index(inplace=True)
        # self._mainEngine = mainEngine
        self._initXRange()
        self._assetName: str = assetName
        self._chartInterval = Aiconfig.get("DEFAULT_CHART_INTERVAL")
        self._yMarginPercent:int = int(Aiconfig.get("DEFAULT_Y_MARGIN"))/100

        # if assetName is not None:
        #     self.setAsset(assetName)

        # self.register_event()

    def _initXRange(self) -> None:
        if self.isEmpty():
            self._xMax = self.MIN_BAR_COUNT  # the max visible data's index x
            self._xMin = 0      # the min visible data's index x
        else:
            self._xMax = self.lastIndex()
            # self._xMin = max(0, self._xMax - self.MIN_BAR_COUNT)
            self._xMin = self._data.first_valid_index

    def setAsset(self, assetName: str = None, 
                    chartInterval: ChartInterval = None,
                    period: ChartPeriod = ChartPeriod.Y1
                    ) -> bool:
        return True

    def _setAsset(self, assetName: str = None, 
                 chartInterval: ChartInterval = None,
                 period: ChartPeriod = ChartPeriod.Y1
                 ) -> bool:
        """
        set the asset to the name given. 
        this will change all the data hold by the Datamanager
        interval for the chart candles:
        1m,2m,5m,15m,30m,1h,1d,5d,1wk Intraday data cannot extend last 60 days
        the interval will be same as last asset if not given.
        the period for the chart candles.
        Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd, max Either Use period parameter or use start and end
        """
        try:

            if not assetName and not chartInterval:
                return False
            
            if not assetName:
                if not self._assetName:
                    return False
                else:
                    assetName = self._assetName
            
            if not chartInterval:
                self._chartInterval = ChartInterval.D1
                chartInterval = ChartInterval.D1
            else:
                self._chartInterval = chartInterval

            if period is None:
                period = ChartPeriod.Y1
            
            if chartInterval.value in ["1s", "1m", "5m", "15m", "30m", "1h"]:
                if period.value in ["1d", "5d", "1mo"]:
                    pass
                else:
                    period = ChartPeriod.M1

            if isinstance(assetName, str):
                self._assetName = assetName
                # if 
                asset = Asset(assetName)
                logger.debug(f"DataManager:: setAsset() :: assetName is {assetName}")

                self._data = asset.getMarketData(chartInterval, period)
                # print(f"self._data is {self._data}")
                self._formatData()
                self._initXRange()
                
                return True
            else:
                return False
        except Exception as e:
            logger.info(f"DataManager: setAsset(): failed to setAsset for {assetName}, interval {chartInterval}, period: {period}")
            return False


    def _formatData(self, data:DataFrame = None) -> DataFrame:
        if data is None:
            if self.isEmpty():
                return None
            self._data.reset_index(inplace=True)
            self._data.rename(columns={"Datetime":"Date"}, inplace=True)
        else:
            data.rename(columns={"Datetime":"Date"}, inplace=True)
            return data
        
    def setInterval(self, interval: ChartInterval = None) -> bool:
        """
        set the interval of the data for the chart/candlestick
        this will trigger the action to get data for the new Interval.
        """
        
        if interval is not None and isinstance(interval, ChartInterval):

            self._interval = interval

            return True
        return False

    def getDateTime(self, index: int) -> datetime:
        """
        get the datetime value for index=index in datas (DataFrame)
        return a datetime object
        """
        if index is None:
            return None
        index = int(index)

        if self._data is None or self._data.empty or index not in self._data.index:
            return None
        else:
            date = self._data.loc[index]['Date']
            if isinstance(date, Timestamp):
                date = datetime.fromtimestamp(date.timestamp())
            # date: datetime = datetime.strptime(self._data.loc[index]['Date'], "%Y%m%d %H:%M:%S")
            return date
        
    def getData(self) -> DataFrame:
        return self._data
    
    def setData(self, data: DataFrame = None) -> bool:
        """
        change the data to a new specified DataFrame
        """
        if data is not None and isinstance(data, DataFrame):
            self._data = data
            self._formatData()
            return True
        return False
            
        pass

    def update_history(self, data: DataFrame) -> None:
        """
        Update a list of bar data.
        """
        if isinstance(data, DataFrame) and not data.empty:
            self.update_bar(data)

    def update_bar(self, data: DataFrame) -> None:
        """
        Update one single bar data.
        """
        logger.debug(f"here in DataManager:: update_bar:: {len(data)}")
        if isinstance(data, DataFrame) and not data.empty:
            data = self._formatData(data)
            self._data = pd.concat([self._data, data], ignore_index=True)
            self._data.drop_duplicates(subset='Date', keep= "last", inplace= True)

            logger.debug(f"DataManager:: update_bar ...... \n {self._data['Date']}")
            self._data.sort_values(by=['Date'], inplace= True)
            self._data.reset_index(inplace=True, drop=True)
            self._assetName = data.at[data.first_valid_index(),'Symbol']

            self._initXRange()
            logger.debug(f"DataManager:: update_bar update finished.")

    def append(self, data: DataFrame) -> bool:

        if isinstance(data, DataFrame) and not data.empty:
            data = self._formatData(data)
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

    def get_index(self, bar: DataFrame) -> int|None:
        """ get index by a bar data (Dataframe). get the index by the datetime."""
        if bar is not None and isinstance(bar, DataFrame) and not bar.empty:
            try:

                index = self._data[self._data['Date'] == bar.at[bar.first_valid_index(), 'Date']].first_valid_index()

                return index
            except Exception as e:
                return None
            
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
        
        if self._data is not None and isinstance(max, int) and max < len(self._data.index):
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
        if self._data is not None and isinstance(min, int) and (0 <= min < len(self._data.index)):
            self._xMin = min
            return True
        else:
            return False

    def getYRange(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        get the min and max Y within the index of min_ix to max_ix
        return the whole range of price Y if none of the min_ix and max_ix provided
        return 0,1 if there is no data in the datamanager.
        """
        # print(f"min_ix is {min_ix} \n")
        # print(f"max_ix is {max_ix} \n")
        if self.isEmpty():
            return 0, 1
        logger.debug(f"Datamanager:: getYRange:: =====================\n"+
                    f"{min_ix=} and {max_ix=}")
        if not min_ix or not max_ix:
            min_ix: int = 0
            max_ix: int = self.getTotalDataNum() - 1
        else:
            min_ix: int = int(min_ix)
            max_ix: int = int(max_ix)
            max_ix = min(max_ix, self.getTotalDataNum())
        if min_ix > max_ix:
            i = min_ix
            min_ix = max_ix
            max_ix = i
        
        if min_ix in self._data.index and max_ix in self._data.index:
            # print(self._data)
            data = self._data[min_ix:max_ix]
            miny = data['Low'].min()

            maxy = data['High'].max()
            margin = (maxy - miny) * (self._yMarginPercent)
            miny -= margin
            maxy += margin

            return (miny, maxy)

    def getVolumeRange(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        get the min and max Volume within the index of min_ix to max_ix
        return the whole range of volume if none of the min_ix and max_ix provided
        return 0,1 if there is no data in the datamanager.
        """
        # print(f"min_ix is {min_ix} \n")
        # print(f"max_ix is {max_ix} \n")
        if self.isEmpty():
            return 0, 1

        if not min_ix or max_ix:
            min_ix: int = 0
            max_ix: int = self.getTotalDataNum() - 1
        else:
            min_ix: int = int(min_ix)
            max_ix: int = int(max_ix)
            max_ix = min(max_ix, self.getTotalDataNum())

        if min_ix > max_ix:
            i = min_ix
            min_ix = max_ix
            max_ix = i

        if min_ix in self._data.index and max_ix in self._data.index:
            data = self._data[min_ix:max_ix]
            # print(data)
            min = data['Volume'].min()
            max = data['Volume'].max() 

            return (min, max)

    def lastIndex(self) -> int:
        """
        return the last element's index in the data list (DataFrame)
        """
        if not self.isEmpty():
            return self._data.last_valid_index()
        
        return None
    
    def getPriceRange() -> Tuple[float, float]:

        return (50.0, 50.0)

    def getTotalDataNum(self) -> int:
        """
        return the total rows (records) in the Dataframe.
        return 0 if the data is empty now.
        """
        if not self.isEmpty():
            return len(self._data.index)
        else:
            return 0

    def clearAll(self) -> None:
        """
        drop all _data in the dataframe
        """
        if not self.isEmpty():
            self._data.drop(self._data.index, inplace=True)
        self.setXMax(0)
        self.setXMin(0)

    def isEmpty(self) -> bool:
        """
        return True if the _data is None or is empty
        """
        if self._data is None or self._data.empty:
            return True

        return False
    

class ChartBase(pg.GraphicsObject):
    """
    base class for chart related Graphics Items. 
    """
    def __init__(self, dataManager: DataManager = None):
        pg.GraphicsObject.__init__(self)
        # data must be a DataFrame include time, open
        # close, high, low
        self._dataManager: DataManager = dataManager
        self.picture = QtGui.QPicture()

        self._bar_picutures: Dict[int, QtGui.QPicture] = {}
        self._initBarPictures()

        self._item_picuture: QtGui.QPicture = None

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

        self._rect_area: Tuple[float, float] = None

        # Very important! Only redraw the visible part and improve speed a lot.
        self.setFlag(self.GraphicsItemFlag.ItemUsesExtendedStyleOption)

        # Force update during the next paint
        self._to_update: bool = False

    def _initBarPictures(self):
        barNum = 100
        if not self._dataManager or self._dataManager.isEmpty():
            pass
        else:
            barNum = max(barNum, self._dataManager.getTotalDataNum())

        if self._bar_picutures is not None and len(self._bar_picutures) > 0:
            print(f"{self._bar_picutures=} and {len(self._bar_picutures)=}")
            barNum = max(barNum, len(self._bar_picutures))

        self._bar_picutures = {n:None for n in range(barNum)}

    def generate_picture(self):
        """
        pre-computing a QPicture object allows paint() to run much more quickly,
        rather than re-drawing the shapes every time.
        """
        pass

    def update_history(self, history: DataFrame) -> None:
        """
        Update a list of bar data.
        """
        logger.debug(f"in chartbase:: update_history:: now......")
        self._bar_picutures.clear()

        bars = self._dataManager.getTotalDataNum()
        logger.debug(f"in chartbase:: update_history:: {bars=} ......")
        for ix in range(bars):
            self._bar_picutures[ix] = None

        # min_x = 0
        # max_x = bars-1
        # logger.info(f"in chartbase:: update_history:: {min_x=} and {max_x=} ......")
        # if max_x > min_x:
        #     self._drawItemPicture(min_x, max_x)

        self.update()

    def update_bar(self, bar: DataFrame) -> None:
        """
        Update single bar data.
        """
        if bar is not None and isinstance(bar, DataFrame) and not bar.empty:
            ix: int = self._dataManager.get_index(bar)

            self._bar_picutures[ix] = None

            self.update()

    def update(self):
        """
        only update the drawing for the changed part of the data
        """
        logger.debug(f"entered update ..............")
        if self.scene():
            self._to_update = True
            self.scene().update()
        logger.debug(f" update completed ..............")

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

    def clearAll(self):
        """
        clear all data and pictures.
        """
        self._item_picuture = None
        self._bar_picutures.clear()
        logger.debug(f"chartbase:clearAll:: self.bar_pictures is {self._bar_picutures}")
        self.update()

    def setAsset(self, dataManager:DataManager) -> bool:
            self._dataManager: DataManager = dataManager
            self.picture = QtGui.QPicture()

            self._bar_picutures: Dict[int, QtGui.QPicture] = {}
            self._initBarPictures()

            self._item_picuture: QtGui.QPicture = None
            logger.info(f"ChartBase:: setAsset :: --init-- picture: {len(self._bar_picutures)}")
            self._rect_area: Tuple[float, float] = None
            # Force update during the next paint
            self._to_update: bool = False

            if not dataManager.isEmpty():
                self.generate_picture()
                logger.info(f"ChartBase:: setAsset :: --init-- picture: {self.picture}")
                return True
            return False

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

    def paint(self,
              painter: QtGui.QPainter,
              opt: QtWidgets.QStyleOptionGraphicsItem,
              w: QtWidgets.QWidget
              ):
        # **********************************************
        # print(f"chartbase: paint: picture.size. {self.picture.boundingRect()}")
        """
        print(f"chartbase: paint: picture.. {self.picture}")
        painter.drawPicture(0, 0, self.picture)
        """ 
        rect:QtWidgets.QStyleOptionGraphicsItem = opt.exposedRect

        min_ix: int = int(rect.left())
        max_ix: int = int(rect.right())
        max_ix: int = min(max_ix, len(self._bar_picutures))
        logger.debug(f"ChartBase::Paint:: min_ix = {min_ix} and max_ix = {max_ix}")
        rect_area: tuple = (min_ix, max_ix)
        if (
            self._to_update
            or rect_area != self._rect_area
            or not self._item_picuture
        ):
            self._to_update = False
            self._rect_area = rect_area
            self._drawItemPicture(min_ix, max_ix)

        self._item_picuture.play(painter)

    def _drawItemPicture(self, min_ix: int, max_ix: int) -> None:
        """
        Draw the picture of item in specific range.
        """
        logger.debug(f"entered into chartbase:: _drawItemPicture:: {min_ix} and {max_ix}")

        self._item_picuture = QtGui.QPicture()
        painter: QtGui.QPainter = QtGui.QPainter(self._item_picuture)

        for ix in range(min_ix, max_ix):
            # logger.info(f"chartbase:: _drawItemPicture:: enter for loop {len(self._bar_picutures)}")
            bar_picture: QtGui.QPicture = self._bar_picutures[ix]
            
            if bar_picture is None:
                # bar:DataFrame  = self._dataManager.getByIndex(ix)
                # logger.info(f"chartbase:: _drawItemPicture:: before _drawBarPicture ")
                bar_picture = self._drawBarPicture(ix)
                self._bar_picutures[ix] = bar_picture

            bar_picture.play(painter)

        painter.end()        

    @abstractmethod
    def _drawBarPicture(self, ix: int) -> QtGui.QPicture:
        """
        Draw picture for specific bar.
        """
        pass

    @abstractmethod
    def boundingRect(self):
        """ 
        boundingRect _must_ indicate the entire area that will be drawn on
        or else we will get artifacts and possibly crashing.
        (in this case, QPicture does all the work of computing the bouning rect for us)
        """
        pass

@dataclass
class Candlestick:
    """
    single candlestick item on the chart.
    """
    volume:int
    open:float
    high:float
    low:float
    close:float
    _index_x:int
    def __init__(self, dataManager: DataManager = None, index: int = None):
        # super().__init__(dataManager)
        self._dataManager = dataManager
        self._index_x: int = index
        self.dateTime = self._dataManager.getDateTime(index)
        data = self._dataManager.getByIndex(index)
        if data is not None:
            self.open = data.at[index, 'Open']
            self.close = data.at[index, 'Close']
            self.high = data.at[index, 'High']
            self.low = data.at[index, 'Low']
            self.volume = data.at[index, 'Volume']


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
        # self._candles: List[CandlestickItem] = None
        if not dataManager.isEmpty():
            # self._candles = [CandlestickItem(dataManager, index) for index in dataManager._data.index]
            self.generate_picture()
            logger.debug(f"candlstickitems --init-- picture: {self.picture}")

    def generate_picture(self):
        """
        pre-computing a QPicture object allows paint() to run much more quickly, 
        rather than re-drawing the shapes every time.
        """
        data_len = self._dataManager.getTotalDataNum()
        logger.debug(f"data_len in Candlestickitems is {data_len}")
        min_x = 0
        max_x = data_len-1

        self._drawItemPicture(min_x, max_x)

        # candle_num = 0
        # if data_len > self.max_candle:
        #     candle_num = data_len - self.max_candle
        # self._dataManager.setXMin(candle_num)
        # self._dataManager.setXMax(self._dataManager.lastIndex())

    def boundingRect(self) -> QtCore.QRectF:
        """
        reimplement boundingRect method which set the size of the graph
        
        min_x = self._dataManager.getXMin()
        max_x = self._dataManager.getXMax()

        min_price, max_price = self._dataManager.getYRange(min_x, max_x)
        rect: QtCore.QRectF = QtCore.QRectF(
            0,
            min_price,
            max_x - min_x,
            max_price - min_price
        )
        """
        # print(f"candlestickItems: boundingRect: {len(self._bar_picutures)}")
        # min_price, max_price = self._dataManager.getYRange()
        min_x = self._dataManager.getXMin()
        max_x = self._dataManager.getXMax()
        min_price, max_price = self._dataManager.getYRange(min_x, max_x)
        # min_x = min(min_x, max_x)
        # x_range = max_x - min_x
        logger.debug(f"Candlestickitems:: boundingRect:: min_x is {min_x} and max_x is {max_x}, min_price is {min_price} and max price is {max_price}")

        rect: QtCore.QRectF = QtCore.QRectF(
            0,
            min_price,
            len(self._bar_picutures)+10,
            # x_range +10,
            max_price - min_price
        )
        logger.debug(f"Candlestickitems:: boundingRect:: rect is {rect}")
        return rect

        """
        # **********************************************
        print(f" Candlestickitems: bounding rect: rect is {rect}")
        print(f" Candlestickitems: bounding rect: self.picture.rect is {self.picture.boundingRect()}")
        return self.picture.boundingRect()
        """

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        Get range of y-axis with given x-axis range.

        If min_ix and max_ix not specified, then return range with whole data set.
        """
        return self._dataManager.getYRange(min_ix, max_ix)
    

    def _drawBarPicture(self, index_x: int) -> QtGui.QPicture:
        """
        Draw picture for specific bar.
        """
        # Create candle picture's object
        candle_picture: QtGui.QPicture = QtGui.QPicture()
        p: QtGui.QPainter = QtGui.QPainter(candle_picture)

        data = self._dataManager.getByIndex(index_x)
        logger.debug(f"candlestickitems:: _drawBarpictures:: {data=}")
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
            logger.debug(f"no data find in the datamanager index is {index_x}")
        
        # Finish
        p.end()
        return candle_picture
    
    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show by cursor.
        """
        # data: DataFrame = self._dataManager.getByIndex(ix)
        if not isinstance(ix, int):
            if isinstance(ix, float):
                ix = int(ix)
            else:
                logger.info(f"ix in get_info_text is invalid. with value {ix}")
                return ""

        candle: Candlestick = Candlestick(self._dataManager, ix)

        if candle is None or candle._index_x is None or candle.dateTime is None:
            candle = Candlestick(self._dataManager, self._dataManager.lastIndex())

        if candle is not None and candle._index_x is not None and candle.dateTime is not None:
            # print(f"candle is {candle}")
            # print(f"candle.dateTime is {candle.dateTime}")
            words: list = [
                # "Date",
                # candle.dateTime.strftime("%Y-%m-%d"),
                # "",
                # "Time",
                # candle.dateTime.strftime("%H:%M"),
                # "",
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
            logger.info(f"no candle exist, index is {ix}")
            text: str = ""

        return text


class VolumeItem(ChartBase):
    """
    the graph item show the Volume
    """
    BAR_WIDTH = Aiconfig.get("BAR_WIDTH")

    def __init__(self, dataManager: DataManager) -> None:
        """"""
        super().__init__(dataManager)
        

    def _drawBarPicture(self, ix: int) -> QtGui.QPicture:
        """
        draw a single Bar picture for the Volume
        """
        # Create objects
        volume_picture: QtGui.QPicture = QtGui.QPicture()
        painter: QtGui.QPainter = QtGui.QPainter(volume_picture)

        # data = self._dataManager.getByIndex(ix)
        bar = Candlestick(self._dataManager, ix)
        logger.debug(f"entered VolumeItem:: _drawBarPicture:: {ix=} ......")
        if bar is not None and bar.dateTime is not None:

            # Set painter color
            if bar.close >= bar.open:
                painter.setPen(self._up_pen)
                painter.setBrush(self._up_brush)
            else:
                painter.setPen(self._down_pen)
                painter.setBrush(self._down_brush)

            # Draw volume body
            rect: QtCore.QRectF = QtCore.QRectF(
                ix - self.BAR_WIDTH,
                0,
                self.BAR_WIDTH * 2,
                bar.volume
            )
            painter.drawRect(rect)
        
        else:
            logger.debug(f"VolumeItem: _drawBarPicture: no data find in the datamanager index is {ix}")

        # Finish
        painter.end()
        return volume_picture

    def boundingRect(self) -> QtCore.QRectF:
        """
        reimplement the method to return the size of the graph.
        """
        min_volume, max_volume = self._dataManager.getVolumeRange()
        rect: QtCore.QRectF = QtCore.QRectF(
            0,
            min_volume,
            len(self._bar_picutures),
            max_volume - min_volume
        )
        return rect

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        Get range of y-axis with given x-axis range.

        If min_ix and max_ix not specified, then return range with whole data set.
        """
        min_volume, max_volume = self._dataManager.getVolumeRange(min_ix, max_ix)
        return min_volume, max_volume

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

        candle: Candlestick = Candlestick(self._dataManager, ix)

        if candle is not None and candle._index_x is not None and candle.dateTime is not None:
            # print(f"candle is {candle}")
            # print(f"candle.dateTime is {candle.dateTime}")
            text = f"Volume: {candle.volume}"
        else:
            print(f"no candle exist, index is {ix}")
            text: str = ""

        return text


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
        # logger.info("entering DatetimeAxis:: tickStrings:: ")
        if spacing < 1 or self._manager is None:
            return ["" for i in values]

        strings: list = []

        for ix in values:

            dt: datetime = self._manager.getDateTime(ix)
            # logger.info(f"entering DatetimeAxis:: tickStrings:: {dt=} ")
            if not dt:
                s: str = ""
            elif dt.hour:
                # s: str = dt.strftime("%Y-%m-%d\n%H:%M:%S")
                
                s: str = dt.strftime("%H:%M:%S")
                # logger.info(f"entering DatetimeAxis:: tickStrings:: {dt.hour=} and  {s}")
            else:
                s: str = dt.strftime("%Y-%m-%d")

            strings.append(s)
        # logger.info(f"entering DatetimeAxis:: tickStrings:: {strings}")
        return strings


class Ticker(QtWidgets.QComboBox):
    """
    ComboBox for choosing asset/ticker.
    """
    def __init__(self, tickers: List[str] = None):
        super().__init__()

        self.setMinimumSize(80,50)
        self.setEditable(True)

        if tickers is not None and len(tickers) > 0:
            self.addItems(tickers)
        # self.validator = Validator(self)
        self.lineEdit().setValidator(Validator(self))

class Validator(QtGui.QValidator):
    def validate(self, string, pos):
        return QtGui.QValidator.Acceptable, string.upper(), pos
        # for old code still using QString, use this instead
        # string.replace(0, string.count(), string.toUpper())
        # return QtGui.QValidator.Acceptable, pos


class IntervalBox(QtWidgets.QComboBox):
    """
    Combobox for choosing interval for displaying in the chart
    1m,2m,5m,15m,30m,60m,90m,1h,1d,1wk
    """
    def __init__(self):
        super().__init__()
        intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "1wk"]
        self.addItems(intervals)
        self.setCurrentText("1d")
        self.setEditable(False)
        self.setMinimumSize(80,50)
        
