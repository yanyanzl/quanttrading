

import matplotlib as mp
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import ConciseDateFormatter
from matplotlib.colors import LogNorm
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from datetime import datetime as dt
from event import Event, EventEngine
from constant import EVENT_PLOT
from datatypes import PlotData
# import mplfinance as mf

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from PySide6 import QtWidgets

x = np.linspace(0, 2, 100)  # Sample data.

data1, data2, data3, data4 = np.random.randn(4, 100)


class DataPlot(object):
    """
    main chart window.
    Chart(PlotWidget) --> central Item is layout (GraphicsLayout) --> PlotItem (added by Layout.additem())
    """

    def __init__(self, eventEngine:EventEngine, dataSize:int = 500):

        self.eventEngine = eventEngine
        self.dataSize = dataSize
        # self.ani = None
        # self.ax:Axes = None
        # self.fig: Figure = None

        date = dt.now().strftime("%H:%M:%S.%f")
        self.origin_data_x: np.ndarray = np.array([date for _ in range(dataSize)], dtype=object)

        # print(f"{self.origin_data_x}")
        self.origin_data_y: np.ndarray = np.zeros((dataSize),dtype= float)

        self.count:int = 0
        self.inited:bool = False
        self.current_index:int = 0
        self.x_data:list = []
        self.y_data:list = []
        self.x_tick:list = []

        self.added_num:int = 0

        
        self._init_ui()
        self.plot = self.add_plot("plot")
        self.line: pg.PlotDataItem = self.add_line("first_line")

        self.register_event()

    def _init_ui(self) -> None:
        """
        Init the UI framework  of the chart
        """
        self.view = pg.GraphicsView()
        # self.setWindowTitle("Chart For Quant Trading")
        self._layout: pg.GraphicsLayout = pg.GraphicsLayout()
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(0)
        self._layout.setBorder(color='g', width=1)
        self._layout.setZValue(0)
        self.view.setCentralItem(self._layout)
        self.view.show()
        self.view.setWindowTitle("data plot")

    def add_plot(self, name:str="plot") -> pg.PlotItem:
        # a = pg.PlotWidget()
        plot: pg.PlotItem = self._layout.addPlot(title=name)
        # aaa = pg.PlotWidget(axisItems = {'bottom': pg.DateAxisItem()})
        # aaa.plotItem()
        plot.setMenuEnabled(False)
        plot.setClipToView(True)
        plot.hideAxis("left")
        plot.showAxis("right")
        plot.showAxis("bottom")
        plot.setDownsampling(mode="peak")
        plot.hideButtons()
        plot.setObjectName(name)
        self._layout.addItem(plot)
        return plot

    def add_line(self, name:str="first_line") -> pg.PlotDataItem:
        # pass
        return self.plot.plot([],[],name=name, symbol="o", symbolSize=15,symbolBrush='b')


    def register_event(self) -> None:
        """ register event to listen on"""
        self.eventEngine.register(EVENT_PLOT, self.process_plot_event)
    
    def process_plot_event(self, event:Event) -> None:
        """ process the plot event """
        if event:
            data:PlotData = event.data

            self.x_data.append(data['x_data'])
            self.y_data.append(data['y_data'])
            if len(self.x_data) > self.dataSize:
                self.x_data = self.x_data[-self.dataSize:]
                self.y_data = self.y_data[-self.dataSize:]
            self.line.setData(self.x_data, self.y_data)

            # if self.inited:
            #     self.origin_data_x[:-1] = self.origin_data_x[1:]
            #     self.origin_data_y[:-1] = self.origin_data_y[1:]

            #     self.origin_data_x[-1] = data['x_data']
            #     self.origin_data_y[-1] = data['y_data']

            #     self.added_num += 1
            # else:
            #     self.origin_data_x[self.count] = data['x_data']
            #     self.origin_data_y[self.count] = data['y_data']
            
            self.count += 1
            if self.count == self.dataSize:
                self.inited = True
            # print(f"leaving data {data=}")

    # def update_plot(self):
        
    #     if self.inited:
    #         pass
        

    # def update_data(self,frame) -> list:
    #     """ """
    #     # print(f".......... 1")
    #     if frame < self.size:
    #         if self.origin_data_y[frame]:
    #             self.x_data.append(self.origin_data_x[frame])
    #             self.y_data.append(self.origin_data_y[frame])
    #             # self.x_tick.append(frame)
                
    #     elif frame == self.size:
    #         if self.added_num > 0:
    #             offset = - self.added_num
    #             self.x_data.append(self.origin_data_x[offset])
    #             self.y_data.append(self.origin_data_y[offset])

    #             self.added_num -= 1
    #     if len(self.x_data) > self.size:
    #         self.x_data = self.x_data[-self.size:]
    #         self.y_data = self.y_data[-self.size:]

    #     # print(f".......... 2 {self.origin_data_x=}")
    #     # plt.xticks(range(0,len(self.x_data)), self.x_data)
    #     # self.ax.set_xticks(self.x_data)
    #     ticks = [t for t in range(0,self.size)]
    #     # self.ax.get_xticks()
    #     self.ax.set_xticks(ticks, self.origin_data_x)

    #     self.x_tick = [x for x in range(0, len(self.x_data))]
    #     self.line.set_data(self.x_tick, self.y_data)
    #     return (self.line, self.ax.xaxis)