import pyqtgraph as pg
from PyQt5.QtCore import QObject, QDateTime
from PyQt5.QtGui import QPainter
from ddl.modules.utility import MonoAxisPlotWidget, RPYPlotWidget, GpsPlotWidget

class GraphManager(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.config = parent.config
        self.ui = parent.ui
        self._set_config(); self._set_layout(); self._set_graphs()
        self.last_update_time = QDateTime.currentDateTime()
        self.total_time = 0.0  # seconds since start (mission-time axis)

    # PUBLIC
    def clear(self):
        self.total_time = 0.0
        self.graph_alt.reset()
        self.graph_batt.reset()
        self.graph_accel.reset()
        self.graph_gyro.reset()
        self.graph_gps.reset()

    # UPDATE
    def update(self, data: dict):
        try:
            now = QDateTime.currentDateTime()
            dt_s = max(0.0, self.last_update_time.msecsTo(now) / 1000.0)
            self.total_time += dt_s

            # labels
            self._update_labels(data, int(dt_s * 1000))

            # plots
            self.graph_alt.update(float(data.get("ALTITUDE", 0.0)), self.total_time)
            self.graph_batt.update(float(data.get("VOLTAGE", 0.0)), self.total_time)
            self.graph_accel.update([
                float(data.get("ACCEL_R", 0.0)),
                float(data.get("ACCEL_P", 0.0)),
                float(data.get("ACCEL_Y", 0.0))
            ], self.total_time)
            self.graph_gyro.update([
                float(data.get("GYRO_R", 0.0)),
                float(data.get("GYRO_P", 0.0)),
                float(data.get("GYRO_Y", 0.0))
            ], self.total_time)
            lat = float(data.get("GPS_LATITUDE", 0.0))
            lon = float(data.get("GPS_LONGITUDE", 0.0))
            self.graph_gps.update(lat, lon)

            self.last_update_time = now

        except Exception as e:
            print(f"[WARNING] UPDATE GRAPHS - {e}")

    def _update_labels(self, d, ping):
        if hasattr(self.ui, "lb_mission_time"):
            self.ui.lb_mission_time.setText(str(d.get("MISSION_TIME","--:--:--")) + " UTC")
        if hasattr(self.ui, "lb_state"): self.ui.lb_state.setText(d.get("STATE", ""))
        if hasattr(self.ui, "lb_temp"):
            try: self.ui.lb_temp.setText(f"{float(d.get('TEMPERATURE',0.0)):.1f} °C")
            except: self.ui.lb_temp.setText("--.- °C")
        if hasattr(self.ui, "lb_gps"):
            gps = f"{d.get('GPS_LATITUDE','0')}, {d.get('GPS_LONGITUDE','0')} | alt {d.get('GPS_ALTITUDE','0')} m | sats {d.get('GPS_SATS','0')}"
            self.ui.lb_gps.setText(gps)
        if hasattr(self.ui, "lb_cmd_echo"): self.ui.lb_cmd_echo.setText(d.get("CMD_ECHO",""))
        if hasattr(self.ui, "lb_ping"): self.ui.lb_ping.setText(f"{ping} ms")

    # SETUP
    def _set_graphs(self):
        # NASA-ish: bold axes, clear grid, SI titles
        self.graph_alt  = MonoAxisPlotWidget(title="Altitude (m)",          mission_time_axis=True)
        self.graph_batt = MonoAxisPlotWidget(title="Battery Voltage (V)",   mission_time_axis=True)
        self.graph_accel = RPYPlotWidget(title="Accel (R/P/Y)", mission_time_axis=True)
        self.graph_gyro  = RPYPlotWidget(title="Gyro (R/P/Y)",  mission_time_axis=True)
        self.graph_gps   = GpsPlotWidget(title="GPS Track (lat, lon)")

        self.graphs_top.addItem(self.graph_alt);  self.graphs_top.addItem(self.graph_batt)
        self.graphs_mid.addItem(self.graph_accel); self.graphs_mid.addItem(self.graph_gyro)
        self.graphs_bot.addItem(self.graph_gps)

    def _set_config(self):
        pg.setConfigOption("background", (250,250,250))
        pg.setConfigOption("foreground", (17,17,17))
        pg.setConfigOption("antialias", self.config.get("graphs.settings.antialias"))
        pg.setConfigOption("exitCleanup", True)
        pg.setConfigOption("useOpenGL", self.config.get("graphs.settings.opengl"))
        pg.setConfigOption("useCupy", self.config.get("graphs.settings.cupy"))
        pg.setConfigOption("useNumba", self.config.get("graphs.settings.numba"))
        pg.setConfigOption("segmentedLineMode", self.config.get("graphs.settings.segmentedLineMode"))

    def _set_layout(self):
        self.layout = pg.GraphicsLayoutWidget()
        self.layout.setAntialiasing(True)
        self.layout.setRenderHints(QPainter.Antialiasing)
        container = self.layout.addLayout(colspan=1, rowspan=1)
        self.graphs_top = container.addLayout(rowspan=1, colspan=1); container.nextRow()
        self.graphs_mid = container.addLayout(rowspan=1, colspan=1); container.nextRow()
        self.graphs_bot = container.addLayout(rowspan=1, colspan=1)
        self.ui.telemetry_graphs.addWidget(self.layout)
