import pyqtgraph as pg
import numpy as np
from PyQt5.QtGui import QColor, QBrush

def _mk_pen(color_hex, width=3.5): return pg.mkPen(color_hex, width=width)
AXIS_PEN = pg.mkPen('#222', width=2)
GRID_ALPHA = 0.30

class MonoAxisPlotWidget(pg.PlotItem):
    def __init__(self, parent=None, labels=None, title=None,
                 color: str = "#0A5", enableMenu=False, mission_time_axis=False, **kargs):
        if labels is None: labels = {'bottom': 'Mission Time (s)'}
        super().__init__(parent=parent, labels=labels, title=title, enableMenu=enableMenu, **kargs)
        self.mission_time_axis = mission_time_axis
        self.x = []; self.y = []
        self.curve = self.plot(pen=_mk_pen(color), antialias=True, connect='finite')
        self.curve.pxMode = False
        fill_color = QColor(color); fill_color.setAlpha(24)
        self.curve.setFillBrush(QBrush(fill_color)); self.curve.setFillLevel(0)
        self.showGrid(x=True, y=True, alpha=GRID_ALPHA)
        self.getAxis('bottom').setPen(AXIS_PEN); self.getAxis('left').setPen(AXIS_PEN)
        self.getAxis('bottom').setTextPen('#111'); self.getAxis('left').setTextPen('#111')
        self.getViewBox().disableAutoRange(axis=None)  # manual control
        self.hideButtons(); self.getViewBox().setMouseEnabled(x=False, y=False)

    def reset(self):
        self.x.clear(); self.y.clear()
        self.curve.setData([], [])
        self.setXRange(0, 10, padding=0.01)  # initial

    def update(self, value, mission_time_s: float):
        v = float(value)
        self.x.append(max(0.0, float(mission_time_s)))
        self.y.append(v)
        self.curve.setData(self.x, self.y)
        # X axis 0..now (auto based on data)
        xmin = 0.0
        xmax = max(10.0, self.x[-1])
        self.setXRange(xmin, xmax, padding=0.02)
        # Y range with margin
        ymin = min(self.y) if self.y else -1
        ymax = max(self.y) if self.y else 1
        if ymin == ymax:
            ymin -= 1; ymax += 1
        yr = (ymax - ymin) * 0.10
        self.setYRange(ymin - yr, ymax + yr, padding=0.02)

class RPYPlotWidget(pg.PlotItem):
    def __init__(self, parent=None, labels=None, title=None,
                 colors=("#0A5","#06C","#C60"), enableMenu=False, mission_time_axis=False, **kargs):
        if labels is None: labels = {'bottom': 'Mission Time (s)'}
        super().__init__(parent=parent, labels=labels, title=title, enableMenu=enableMenu, **kargs)
        self.colors = colors
        self.x = []
        self.y = [[],[],[]]
        self.curves = [self.plot(pen=_mk_pen(c), antialias=True, connect='finite') for c in colors]
        for c in self.curves: c.pxMode=False
        self.showGrid(x=True, y=True, alpha=GRID_ALPHA)
        self.getAxis('bottom').setPen(AXIS_PEN); self.getAxis('left').setPen(AXIS_PEN)
        self.getAxis('bottom').setTextPen('#111'); self.getAxis('left').setTextPen('#111')
        self.getViewBox().disableAutoRange(axis=None)
        self.hideButtons(); self.getViewBox().setMouseEnabled(x=False, y=False)

    def reset(self):
        self.x.clear()
        for i in range(3): self.y[i].clear()
        for c in self.curves: c.setData([], [])
        self.setXRange(0, 10, padding=0.01)

    def update(self, values3, mission_time_s: float):
        r, p, y = [float(v) for v in values3]
        t = max(0.0, float(mission_time_s))
        self.x.append(t)
        self.y[0].append(r); self.y[1].append(p); self.y[2].append(y)
        for i in range(3): self.curves[i].setData(self.x, self.y[i])
        xmin = 0.0; xmax = max(10.0, self.x[-1])
        self.setXRange(xmin, xmax, padding=0.02)
        all_y = self.y[0] + self.y[1] + self.y[2]
        if all_y:
            ymin = min(all_y); ymax = max(all_y)
            if ymin == ymax: ymin -= 1; ymax += 1
            yr = (ymax - ymin) * 0.10
            self.setYRange(ymin - yr, ymax + yr, padding=0.02)

class GpsPlotWidget(pg.PlotItem):
    def __init__(self, parent=None, labels=None, title=None, color: str="#222", enableMenu=False, **kargs):
        if labels is None: labels={'bottom':'Longitude','left':'Latitude'}
        super().__init__(parent=parent, labels=labels, title=title, enableMenu=enableMenu, **kargs)
        self.x = []; self.y = []
        self.track = self.plot(pen=_mk_pen(color, 2.5), antialias=True, connect='finite', symbol=None)
        self.track.pxMode=False
        self.scatter = pg.ScatterPlotItem(symbol='x', size=9, brush=pg.mkBrush("#111")); self.addItem(self.scatter)
        self.showGrid(x=True, y=True, alpha=GRID_ALPHA)
        self.getAxis('bottom').setPen(AXIS_PEN); self.getAxis('left').setPen(AXIS_PEN)
        self.getAxis('bottom').setTextPen('#111'); self.getAxis('left').setTextPen('#111')
        self.hideButtons(); self.getViewBox().setMouseEnabled(x=False, y=False)

    def reset(self):
        self.x.clear(); self.y.clear()
        self.track.setData([], []); self.scatter.setData([], [])

    def update(self, latitude, longitude):
        lon = float(longitude); lat = float(latitude)
        self.x.append(lon); self.y.append(lat)
        self.track.setData(self.x, self.y)
        self.scatter.setData([lon], [lat], symbol='x')
        if self.x and self.y:
            x_range = (min(self.x) - 0.0004, max(self.x) + 0.0004)
            y_range = (min(self.y) - 0.0004, max(self.y) + 0.0004)
            self.setRange(xRange=x_range, yRange=y_range)
