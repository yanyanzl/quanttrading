

# import matplotlib as mp
# import matplotlib.pyplot as plt
# import numpy as np
# from matplotlib.dates import ConciseDateFormatter
# from matplotlib.colors import LogNorm
# import matplotlib.animation as animation
# from matplotlib import style
# from matplotlib.figure import Figure
# from matplotlib.axes import Axes
# from matplotlib.lines import Line2D
# from datetime import datetime as dt
from event import Event, EventEngine
from constant import EVENT_PLOT
from datatypes import PlotData

import pyqtgraph as pg
from pyqtgraph import DateAxisItem
from datetime import datetime
from PySide6 import QtCore, QtWidgets

# class DataPlot(QtCore.QObject):
class DataPlot(QtWidgets.QWidget):
    """
    main chart window.
    Chart(PlotWidget) --> central Item is layout (GraphicsLayout) --> PlotItem (added by Layout.additem())
    """
    
    signal_tick: QtCore.Signal = QtCore.Signal(Event, name="signaltick")

    def __init__(self, eventEngine:EventEngine, dataSize:int = 500):
        super().__init__()

        self.eventEngine = eventEngine
        self.dataSize = dataSize

        self.count:int = 0
        self.inited:bool = False
        # self.current_index:int = 0

        self.x_data:dict[str,list] = {}
        self.y_data:dict[str,list] = {}

        self.is_plot:bool = True
        
        self._init_ui()
        self.plot:dict[str, pg.PlotItem] = {}
        self.lines: dict[str, pg.PlotDataItem] = {}

        self.register_event()

    def _init_ui(self) -> None:
        """
        Init the UI framework  of the chart
        """
        self.view = pg.GraphicsView()
        self._layout: pg.GraphicsLayout = pg.GraphicsLayout()
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(0)
        self._layout.setBorder(color='g', width=1)
        self._layout.setZValue(0)
        self.view.setCentralItem(self._layout)
        # self.view.show()
        self.view.setWindowTitle("data plot")

    def add_plot(self, name:str="plot") -> pg.PlotItem:
        plot: pg.PlotItem = self._layout.addPlot(title=name)

        plot.setMenuEnabled(False)
        plot.setClipToView(True)
        plot.hideAxis("left")
        plot.showAxis("right")
        plot.showAxis("bottom")
        plot.setDownsampling(mode="peak")
        plot.hideButtons()
        plot.setObjectName(name)
        plot.addLegend()
        self._layout.addItem(plot)
        self._layout.nextRow()
        return plot

    def add_line(self, name:str="first_line", plotName:str=None) -> pg.PlotDataItem:
        # pass
        plot = self.plot.get(plotName, None)
        if plot:
            return plot.plot([],[],name=name, symbol="o", symbolSize=15,symbolBrush='b')
        return None


    def register_event(self) -> None:
        """ register event to listen on"""

        # This kind of different-thread problems happen all the
        #  time with Qt when you use multiple threads. 
        # The canonical way to solve this problem is to use signals and slots.
        # self.event_engine.register(EVENT_HISDATA, self.process_history_event)

        self.eventEngine.register(EVENT_PLOT, self.signal_tick.emit)
        self.signal_tick.connect(self.process_plot_event)


    def process_plot_event(self, event:Event) -> None:
        """ process the plot event """
        if event:
            data:PlotData = event.data
            if data["desc"] not in self.lines:
                plot = self.plot[data["desc"]] = self.add_plot(data["desc"])
                if type(data["x_data"]) is datetime:
                    axis = DateAxisItem()
                    plot.setAxisItems({'bottom':axis})

                self.lines[data['desc']] = self.add_line(data["desc"],data["desc"])
                self.x_data.update({data["desc"]:[data['x_data']]})
                self.y_data.update({data["desc"]:[data['y_data']]})
            else:
                self.x_data.get(data["desc"]).append(data['x_data'])
                self.y_data.get(data["desc"]).append(data['y_data'])

            line = self.lines[data["desc"]]
            data_x = self.x_data.get(data["desc"])
            data_y = self.y_data.get(data["desc"])
            if len(data_x) > self.dataSize:
                data_x = data_x[-self.dataSize:]
                data_y = data_y[-self.dataSize:]
            
            line.setData(data_x, data_y)
            
            self.count += 1
            if self.count == self.dataSize:
                self.inited = True
