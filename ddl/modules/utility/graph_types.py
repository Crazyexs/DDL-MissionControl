# --- graph_types.py (REPLACE WHOLE FILE) ---
import pyqtgraph as pg
import numpy as np
from PyQt5.QtGui import QColor, QBrush

# ================================================================= #
def _mk_pen(color_hex, width=3.5):
    return pg.mkPen(color_hex, width=width)

AXIS_PEN = pg.mkPen('#333', width=2)   # แกนเข้มอ่านกลางแดด
GRID_COLOR = (120,120,120,80)

class MonoAxisPlotWidget(pg.PlotItem):
    def __init__(self, parent=None, labels={'bottom': 'T(s)'}, title=None,
                 color: str = "#0A5", enableMenu=False, linspace_x=120, **kargs):
        super().__init__(parent=parent, labels=labels, title=title,
                         enableMenu=enableMenu, **kargs)

        x_vals = np.linspace(0.0, (linspace_x-1)/linspace_x, linspace_x)
        self.graph_plot = self.plot(
            x=x_vals,
            pen=_mk_pen(color),
            antialias=True, connect='finite')
        self.graph_plot.pxMode = False

        fill_color = QColor(color); fill_color.setAlpha(24)
        self.graph_plot.setFillBrush(QBrush(fill_color))
        self.graph_plot.setFillLevel(0)
        self.graph_plot.setDownsampling(auto=False)

        self.graph_data = np.zeros(linspace_x, dtype=float)
        self.window_size = 5
        self.weights = np.ones(self.window_size)/self.window_size
        self.ptr1 = 0.0

        self.showGrid(x=True, y=True, alpha=0.25)
        self.getAxis('bottom').setPen(AXIS_PEN)
        self.getAxis('left').setPen(AXIS_PEN)
        self.getAxis('bottom').setTextPen('#111')
        self.getAxis('left').setTextPen('#111')

        self.getViewBox().disableAutoRange(axis="x")
        self.hideButtons()
        self.getViewBox().setMouseEnabled(x=False, y=False)

    def update(self, value, elapsed_time):
        value = float(value)
        self.graph_data[:-1] = self.graph_data[1:]
        self.graph_data[-1] = value

        y = np.convolve(self.graph_data, self.weights, mode='valid')
        x = np.linspace(self.ptr1, self.ptr1 + elapsed_time, len(y))
        self.ptr1 += float(elapsed_time)

        self.setXRange(self.ptr1 - max(1.0, elapsed_time*120), self.ptr1, padding=0.01)
        self.graph_plot.setData(x=x, y=y)

# ================================================================= #
class RPYPlotWidget(pg.PlotItem):
    """ กราฟ 3 เส้นในแกนเดียว: Roll/Pitch/Yaw """
    def __init__(self, parent=None, labels={'bottom': 'T(s)'}, title=None,
                 colors=("#0A5", "#06C", "#C60"), enableMenu=False, linspace_x=120, **kargs):
        super().__init__(parent=parent, labels=labels, title=title,
                         enableMenu=enableMenu, **kargs)

        self.linspace_x = linspace_x
        x_vals = np.linspace(0.0, (linspace_x-1)/linspace_x, linspace_x)

        self.curves = []
        for c in colors:
            curve = self.plot(x=x_vals, pen=_mk_pen(c), antialias=True, connect='finite')
            curve.pxMode = False
            self.curves.append(curve)

        self.data = [np.zeros(linspace_x, dtype=float) for _ in range(3)]
        self.ptr1 = 0.0

        self.showGrid(x=True, y=True, alpha=0.25)
        self.getAxis('bottom').setPen(AXIS_PEN)
        self.getAxis('left').setPen(AXIS_PEN)
        self.getAxis('bottom').setTextPen('#111')
        self.getAxis('left').setTextPen('#111')
        self.getViewBox().disableAutoRange(axis="x")
        self.hideButtons()
        self.getViewBox().setMouseEnabled(x=False, y=False)

    def update(self, values3, elapsed_time):
        r, p, y = [float(v) for v in values3]
        for i, v in enumerate([r,p,y]):
            self.data[i][:-1] = self.data[i][1:]
            self.data[i][-1] = v

        x_vals = np.linspace(self.ptr1, self.ptr1 + elapsed_time, self.linspace_x)
        self.ptr1 += float(elapsed_time)
        self.setXRange(self.ptr1 - max(1.0, elapsed_time*120), self.ptr1, padding=0.01)

        for i in range(3):
            self.curves[i].setData(x=x_vals, y=self.data[i])

# ================================================================= #
class GpsPlotWidget(pg.PlotItem):
    def __init__(self, parent=None, labels={'bottom': 'Longitude', 'left': 'Latitude'}, title=None,
                 color: str = "#333", enableMenu=False, **kargs):
        super().__init__(parent=parent, labels=labels, title=title,
                         enableMenu=enableMenu, **kargs)

        self.graph_data = {'x': [], 'y': []}
        self.last_point = {'x': [], 'y': []}

        self.graph_plot = self.plot(
            pen=_mk_pen(color, 2.5),
            antialias=True, connect='finite', symbol=None)
        self.graph_plot.setDownsampling(auto=True)
        self.graph_plot.pxMode = False

        self.scatter_plot = pg.ScatterPlotItem(symbol='x', size=9, brush=pg.mkBrush("#111"))
        self.addItem(self.scatter_plot)

        self.showGrid(x=True, y=True, alpha=0.25)
        self.getAxis('bottom').setPen(AXIS_PEN); self.getAxis('left').setPen(AXIS_PEN)
        self.getAxis('bottom').setTextPen('#111'); self.getAxis('left').setTextPen('#111')
        self.hideButtons()
        self.getViewBox().setMouseEnabled(x=False, y=False)

    def update(self, latitude, longitude):
        lon = float(longitude); lat = float(latitude)
        self.graph_data['x'].append(lon); self.graph_data['y'].append(lat)
        if len(self.graph_data['x']) > 200:
            self.graph_data['x'].pop(0); self.graph_data['y'].pop(0)

        self.last_point = {'x': [lon], 'y': [lat]}
        self.graph_plot.setData(self.graph_data['x'], self.graph_data['y'])
        self.scatter_plot.setData(self.last_point['x'], self.last_point['y'], symbol='x', connect='finite')

        x_range = (min(self.graph_data['x']) - 0.0004, max(self.graph_data['x']) + 0.0004)
        y_range = (min(self.graph_data['y']) - 0.0004, max(self.graph_data['y']) + 0.0004)
        self.setRange(xRange=x_range, yRange=y_range)
