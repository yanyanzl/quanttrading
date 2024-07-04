"""
This is the module for chart displaying and interactive
support real time data and data from files
"""

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from PySide6 import QtWidgets
from typing import Dict, List
from pandas import DataFrame
from datetime import datetime
# from abc import ABC


from pathlib import Path  # if you haven't already done so
from sys import path as pt
file = Path(__file__).resolve()
# print(str(file.parents[1]))
pt.append(str(file.parents[1]))

from .chartitems import Asset, CandlestickItems, ChartBase, DataManager, DatetimeAxis

CURSOR_COLOR = 'g'
BLACK_COLOR = 'm'
NORMAL_FONT = 'Arial'
MIN_BAR_COUNT = 100
CANDLE_PLOT_NAME = "Candle_Plot"


pg.setConfigOptions(antialias=True)


class Chart(pg.PlotWidget):
    """
    main chart window.
    Chart(PlotWidget) --> central Item is layout (GraphicsLayout) --> PlotItem (added by Layout.additem())
    """
        
    def __init__(self, data: DataFrame = None, parent: QtWidgets.QWidget = None, show=False, size=None, title=None, **kargs):
        super().__init__(parent, plotItem= None, **kargs)

        self._dataManager: DataManager = DataManager(data)
        self._plots: Dict[str, pg.PlotItem] = {}
        self._items: Dict[str, ChartBase] = {}
        self._item_plot_map: Dict[ChartBase, pg.PlotItem] = {}

        self._first_plot: pg.PlotItem = None

        self.MIN_BAR_COUNT = MIN_BAR_COUNT
        self._right_ix: int = 0                     # Index of most right data
        self._bar_count: int = MIN_BAR_COUNT   # Total bar visible in chart

        self._init_ui()
        self._cursor = ChartCursor(self, self._dataManager, self._plots, self._item_plot_map)
        self._initData()

    def _initData(self) -> None:
        manager = self._dataManager 
        if manager is not None and manager.getData() is not None:
            # set the visible range related parameters.
            pass



    def _init_ui(self) -> None:
        """
        Init the UI framework  of the chart
        """
        # self.setWindowTitle("Chart For Quant Trading")

        self._layout: pg.GraphicsLayout = pg.GraphicsLayout()
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(0)
        self._layout.setBorder(color='g', width=0.8)
        self._layout.setZValue(0)
        self.setCentralItem(self._layout)

        # create self._first_plot which is candle_plot
        self.add_plot(CANDLE_PLOT_NAME)

    def add_plot(
        self,
        plot_name: str,
        minimum_height: int = 80,
        maximum_height: int = None,
        hide_x_axis: bool = False
    ) -> None:
        """
        Add plot area.
        """
        # Create plot object
        plot: pg.PlotItem = pg.PlotItem(axisItems={"bottom": self._get_new_x_axis()})
        plot.setMenuEnabled(False)
        plot.setClipToView(True)
        plot.hideAxis("left")
        plot.showAxis("right")
        plot.setDownsampling(mode="peak")
        # plot.setRange(xRange=(0, 1), yRange=(0, 1))
        plot.hideButtons()
        plot.setMinimumHeight(minimum_height)
        plot.setObjectName(plot_name)

        if maximum_height:
            plot.setMaximumHeight(maximum_height)

        if hide_x_axis:
            plot.hideAxis("bottom")

        if not self._first_plot:
            self._first_plot = plot

        # Connect view change signal to update y range function
        view: pg.ViewBox = plot.getViewBox()
        view.sigXRangeChanged.connect(self._update_y_range)
        view.setMouseEnabled(x=True, y=False)

        # Set right axis
        right_axis: pg.AxisItem = plot.getAxis("right")
        right_axis.setWidth(60)

        # Connect x-axis link
        if self._plots:
            first_plot: pg.PlotItem = list(self._plots.values())[0]
            plot.setXLink(first_plot)

        # Store plot object in dict
        self._plots[plot_name] = plot

        # Add plot onto the layout
        self._layout.nextRow()
        self._layout.addItem(plot)

    def set_data(self, data: DataFrame = None) ->bool:
        if isinstance(data, DataFrame):
            self._dataManager.setData(data)
            return True
        else:
            return False
        
    def _get_new_x_axis(self) -> DatetimeAxis:
        # return pg.DateAxisItem()
        return DatetimeAxis(self._dataManager, orientation="bottom")

    def add_cursor(self) -> None:
        """"""
        if not self._cursor:
            self._cursor = ChartCursor(
                self, self._dataManager.getData(), self._plots, self._item_plot_map)

    def add_item(self, item: ChartBase, item_name: str,
                 plot_name: str) -> None:
        """
        Add chart item.
        """
        self._items[item_name] = item

        plot: pg.PlotItem = self._plots.get(plot_name)
        plot.addItem(item)

        self._item_plot_map[item] = plot

    def get_plot(self, plot_name: str) -> pg.PlotItem:
        """
        Get specific plot with its name.
        """
        return self._plots.get(plot_name, None)

    def get_all_plots(self) -> List[pg.PlotItem]:
        """
        Get all plot objects.
        """
        return self._plots.values()

    def clear_all(self) -> None:
        """
        Clear all data.
        """
        self._dataManager.clearAll()

        for item in self._items.values():
            item.clear_all()

        if self._cursor:
            self._cursor.clear_all()

    def update_bar(self, barData: DataFrame = None) -> None:
        """
        Update single bar data.
        """
        """ 
        self._manager.update_bar(barData)

        for item in self._items.values():
            item.update_bar(bar)

        self._update_plot_limits()

        if self._right_ix >= (self._manager.get_count() - self._bar_count / 2):
            self.move_to_right()
        """
        pass

    def _update_plot_limits(self) -> None:
        """
        Update the limit of plots.
        """
        for item, plot in self._item_plot_map.items():
            min_value, max_value = item.get_y_range()

            plot.setLimits(
                xMin=-1,
                xMax=self._dataManager.getXMax(),
                yMin=min_value,
                yMax=max_value
            )

    def _update_x_range(self) -> None:
        """
        Update the x-axis range of plots.
        """
        max_ix: int = self._right_ix
        min_ix: int = self._right_ix - self._bar_count

        for plot in self._plots.values():
            plot.setRange(xRange=(min_ix, max_ix), padding=0)

    def _update_y_range(self) -> None:
        """
        Update the y-axis range of plots.
        """
        view: pg.ViewBox = self._first_plot.getViewBox()

        # Return a the view's visible range as a list: [[xmin, xmax], [ymin, ymax]]
        view_range: list = view.viewRange()

        min_ix: int = max(0, int(view_range[0][0]))
        # print(f"view_range is {view_range}")
        max_ix: int = min(self._dataManager.getXMax(), int(view_range[0][1]))

        # Update limit for y-axis
        for item, plot in self._item_plot_map.items():
            y_range: tuple = item.get_y_range(min_ix, max_ix)
            plot.setRange(yRange=y_range)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """
        Reimplement this method of parent to update current max_ix value.
        """
        view: pg.ViewBox = self._first_plot.getViewBox()
        # Return a the view's visible range as a list: [[xmin, xmax], [ymin, ymax]]
        view_range: list = view.viewRange()
        self._right_ix = max(0, view_range[0][1])

        super().paintEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Reimplement this method of parent to move chart horizontally and zoom in/out.
        """
        if event.key() == QtCore.Qt.Key.Key_Left:
            self._on_key_left()
        elif event.key() == QtCore.Qt.Key.Key_Right:
            self._on_key_right()
        elif event.key() == QtCore.Qt.Key.Key_Up:
            self._on_key_up()
        elif event.key() == QtCore.Qt.Key.Key_Down:
            self._on_key_down()

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """
        Reimplement this method of parent to zoom in/out.
        """
        delta: QtCore.QPoint = event.angleDelta()

        if delta.y() > 0:
            self._on_key_up()
        elif delta.y() < 0:
            self._on_key_down()

    def _on_key_left(self) -> None:
        """
        Move chart to left.
        """
        self._right_ix -= 1
        self._right_ix = max(self._right_ix, self._bar_count)

        self._update_x_range()
        self._cursor.move_left()
        self._cursor.update_info()

    def _on_key_right(self) -> None:
        """
        Move chart to right.
        """
        self._right_ix += 1
        self._right_ix = min(self._right_ix, self._dataManager.getXMax())

        self._update_x_range()
        self._cursor.move_right()
        self._cursor.update_info()

    def _on_key_down(self) -> None:
        """
        Zoom out the chart.
        """
        # candle_num = self._dataManager.getXMax() - self._dataManager.getXMin()
        self._bar_count *= 1.2
        self._bar_count = min(int(self._bar_count), self._dataManager.getTotalDataNum())

        self._update_x_range()
        self._cursor.update_info()

    def _on_key_up(self) -> None:
        """
        Zoom in the chart.
        """
        self._bar_count /= 1.2
        self._bar_count = max(int(self._bar_count), self.MIN_BAR_COUNT)

        self._update_x_range()
        self._cursor.update_info()

    def move_to_right(self) -> None:
        """
        Move chart to the most right.
        """
        self._right_ix = self._dataManager.lastIndex()
        self._update_x_range()
        self._cursor.update_info()


class ChartCursor(QtCore.QObject):
    """"""

    def __init__(
        self,
        widget: Chart,
        dataManager: DataManager,
        plots: Dict[str, pg.GraphicsObject],
        item_plot_map: Dict[ChartBase, pg.GraphicsObject]
    ) -> None:
        """"""
        super().__init__()

        self._widget: Chart = widget
        self._dataManager: DataManager = dataManager
        # print(f"chartcursor, data is \n {self._dataManager.getData()}")
        self._plots: Dict[str, pg.GraphicsObject] = plots
        self._item_plot_map: Dict[ChartBase, pg.GraphicsObject] = item_plot_map

        self._x: int = 0
        self._y: int = 0
        self._plot_name: str = ""

        self._init_ui()
        self._connect_signal()

    def _init_ui(self) -> None:
        """"""
        self._init_line()
        self._init_label()
        self._init_info()

    def _init_line(self) -> None:
        """
        Create line objects.
        """
        self._v_lines: Dict[str, pg.InfiniteLine] = {}
        self._h_lines: Dict[str, pg.InfiniteLine] = {}
        self._views: Dict[str, pg.ViewBox] = {}

        # one of: r, g, b, c, m, y, k, w 
        pen: QtGui.QPen = pg.mkPen('w')

        for plot_name, plot in self._plots.items():
            v_line: pg.InfiniteLine = pg.InfiniteLine(angle=90, movable=False, pen=pen)
            h_line: pg.InfiniteLine = pg.InfiniteLine(angle=0, movable=False, pen=pen)
            view: pg.ViewBox = plot.getViewBox()

            for line in [v_line, h_line]:
                line.setZValue(0)
                line.hide()
                view.addItem(line)

            self._v_lines[plot_name] = v_line
            self._h_lines[plot_name] = h_line
            self._views[plot_name] = view

    def _init_label(self) -> None:
        """
        Create label objects on axis.
        """
        self._y_labels: Dict[str, pg.TextItem] = {}
        for plot_name, plot in self._plots.items():
            label: pg.TextItem = pg.TextItem(
                plot_name, fill=CURSOR_COLOR, color=BLACK_COLOR)
            label.hide()
            label.setZValue(2)
            label.setFont(NORMAL_FONT)
            plot.addItem(label, ignoreBounds=True)
            self._y_labels[plot_name] = label

        self._x_label: pg.TextItem = pg.TextItem(
            "datetime", fill=CURSOR_COLOR, color=BLACK_COLOR)
        self._x_label.hide()
        self._x_label.setZValue(2)
        self._x_label.setFont(NORMAL_FONT)
        # plot.addItem(self._x_label, ignoreBounds=True)
        list(self._plots.values())[0].addItem(self._x_label, ignoreBounds=True)

    def _init_info(self) -> None:
        """
        """
        self._infos: Dict[str, pg.TextItem] = {}
        for plot_name, plot in self._plots.items():
            info: pg.TextItem = pg.TextItem(
                "info",
                color=CURSOR_COLOR,
                border=CURSOR_COLOR,
                # fill=BLACK_COLOR
                fill="w"
            )
            info.hide()
            info.setZValue(2)
            info.setOpacity(0.01)
            # info.setFont(NORMAL_FONT)
            plot.addItem(info)  # , ignoreBounds=True)
            self._infos[plot_name] = info

    def _connect_signal(self) -> None:
        """
        Connect mouse move signal to update function.
        """
        self._widget.scene().sigMouseMoved.connect(self._mouse_moved)

    def _mouse_moved(self, evt: tuple) -> None:
        """
        Callback function when mouse is moved.
        """
        if self._dataManager.isEmpty():
            return

        # First get current mouse point
        pos: tuple = evt

        for plot_name, view in self._views.items():
            rect = view.sceneBoundingRect()

            if rect.contains(pos):
                mouse_point = view.mapSceneToView(pos)
                # print(f"mouse_point is {mouse_point}")

                self._x = mouse_point.x()
                # print(f"mouse_point.x() is {mouse_point.x()}")
                self._y = mouse_point.y()

                self._plot_name = plot_name
                break

        # Then update cursor component
        self._update_line()
        self._update_label()
        self.update_info()

    def _update_line(self) -> None:
        """"""
        for v_line in self._v_lines.values():
            v_line.setPos(self._x)
            v_line.show()

        for plot_name, h_line in self._h_lines.items():
            if plot_name == self._plot_name:
                h_line.setPos(self._y)
                h_line.show()
            else:
                h_line.hide()

    def _update_label(self) -> None:
        """"""
        bottom_plot: pg.PlotItem = list(self._plots.values())[-1]
        axis_width = bottom_plot.getAxis("right").width()
        axis_height = bottom_plot.getAxis("bottom").height()
        axis_offset: QtCore.QPointF = QtCore.QPointF(axis_width, axis_height)

        bottom_view: pg.ViewBox = list(self._views.values())[-1]
        bottom_right = bottom_view.mapSceneToView(
            bottom_view.sceneBoundingRect().bottomRight() - axis_offset
        )

        for plot_name, label in self._y_labels.items():
            if plot_name == self._plot_name:
                label.setText(str(self._y))
                label.show()
                label.setPos(bottom_right.x(), self._y)
            else:
                label.hide()

        # dt: datetime = self._data.iloc[self._x]
        dt: datetime = self._dataManager.getDateTime(self._x)
        if dt:
            self._x_label.setText(dt.strftime("%Y-%m-%d %H:%M:%S"))
            self._x_label.show()
            self._x_label.setPos(self._x, bottom_right.y())
            self._x_label.setAnchor((0, 0))

    def update_info(self) -> None:
        """
        
        """
        buf: dict = {}

        for item, plot in self._item_plot_map.items():
            item_info_text: str = item.get_info_text(self._x)
            # print(f"item_info_text is {item_info_text}")

            if plot not in buf:
                buf[plot] = item_info_text
            else:
                if item_info_text:
                    buf[plot] += ("\n" + item_info_text)
         
        for plot_name, plot in self._plots.items():
            plot_info_text: str = buf[plot]
            # print(f"polot_info_text is {plot_info_text}")
            info: pg.TextItem = self._infos[plot_name]
            # print(f"info is {info}")
            info.setText(plot_info_text)
            # print(f"info is {info}")
            info.setOpacity(0.5)
            info.show()
            info.setPos(self._x, self._y)
        
            # view: pg.ViewBox = self._views[plot_name]
            # top_left = view.mapSceneToView(view.sceneBoundingRect().topLeft())
            # info.setPos(top_left)

    def move_right(self) -> None:
        """
        Move cursor index to right by 1.
        """
        # if self._x == len(self._data.index) - 1:
        if self._x == self._dataManager.getXMax():
            return
        self._x += 1

        self._update_after_move()

    def move_left(self) -> None:
        """
        Move cursor index to left by 1.
        """
        if self._x == 0:
            return
        self._x -= 1

        self._update_after_move()

    def _update_after_move(self) -> None:
        """
        Update cursor after moved by left/right.
        """

        # bar = self._data.iloc[self._x]
        print(f"chartcursor, self._x is {self._x}")
        bar: DataFrame = self._dataManager.getByIndex(self._x)
        if bar:
            self._y = bar.at[bar.first_valid_index(), 'Close']

        self._update_line()
        self._update_label()

    def clear_all(self) -> None:
        """
        Clear all data.
        """
        self._x = 0
        self._y = 0
        self._plot_name = ""

        for line in list(self._v_lines.values()) + list(self._h_lines.values()):
            line.hide()

        for label in list(self._y_labels.values()) + [self._x_label]:
            label.hide()


# Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    print("i am here..................")
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QGuiApplication.instance().exec()
    # QtGui.QGuiApplication.instance .QApplication.instance().exec_()

