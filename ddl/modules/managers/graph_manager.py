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
        self._last_state = None
        self._landed_popup_done = False
        self._last_data_cache = {}

    # PUBLIC
    def clear(self):
        self.total_time = 0.0
        self._last_state = None
        self._landed_popup_done = False
        self._last_data_cache = {}
        self.graph_alt.reset()
        self.graph_batt.reset()
        self.graph_accel.reset()
        self.graph_gyro.reset()
        self.graph_gps.reset()
        if hasattr(self.ui, "lb_map_link"):
            self.ui.lb_map_link.setText("")

    # UPDATE
    def update(self, data: dict):
        try:
            now = QDateTime.currentDateTime()
            dt_s = max(0.0, self.last_update_time.msecsTo(now) / 1000.0)
            self.total_time += dt_s

            # labels + last-telemetry pretty block + landing check
            self._update_labels_and_state(data, int(dt_s * 1000))

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

    def _pretty_last_packet(self, d: dict) -> str:
        # Minimal pretty format; show key fields first then the rest
        keys_first = [
            "TEAM_ID","MISSION_TIME","PACKET_COUNT","MODE","STATE",
            "ALTITUDE","TEMPERATURE","PRESSURE","VOLTAGE",
            "GYRO_R","GYRO_P","GYRO_Y","ACCEL_R","ACCEL_P","ACCEL_Y",
            "MAG_R","MAG_P","MAG_Y",
            "GPS_TIME","GPS_ALTITUDE","GPS_LATITUDE","GPS_LONGITUDE","GPS_SATS",
            "CMD_ECHO"
        ]
        lines = []
        for k in keys_first:
            if k in d:
                lines.append(f"{k}: {d.get(k,'')}")
        # If any extra optional fields exist, append them
        for k, v in d.items():
            if k not in keys_first:
                lines.append(f"{k}: {v}")
        return "\n".join(lines)

    def _update_labels_and_state(self, d, ping_ms):
        # Mission time
        if hasattr(self.ui, "lb_mission_time"):
            self.ui.lb_mission_time.setText(str(d.get("MISSION_TIME","--:--:--")) + " UTC")
        # State
        state = d.get("STATE", "")
        if hasattr(self.ui, "lb_state"):
            self.ui.lb_state.setText(state)
        # Temperature
        if hasattr(self.ui, "lb_temp"):
            try: self.ui.lb_temp.setText(f"{float(d.get('TEMPERATURE',0.0)):.1f} °C")
            except: self.ui.lb_temp.setText("--.- °C")
        # GPS compact line
        if hasattr(self.ui, "lb_gps"):
            gps = f"{d.get('GPS_LATITUDE','0')}, {d.get('GPS_LONGITUDE','0')} | alt {d.get('GPS_ALTITUDE','0')} m | sats {d.get('GPS_SATS','0')}"
            self.ui.lb_gps.setText(gps)
        # Ping (optional)
        if hasattr(self.ui, "lb_ping"):
            self.ui.lb_ping.setText(f"{ping_ms} ms")
        # Last telemetry pretty block
        if hasattr(self.ui, "tb_last_telemetry"):
            try:
                # cache and render only if changed
                if d != self._last_data_cache:
                    self._last_data_cache = dict(d)
                    self.ui.tb_last_telemetry.setPlainText(self._pretty_last_packet(d))
            except Exception:
                pass

        # Landing detection → show maps
        try:
            if state == "LANDED" and not self._landed_popup_done:
                lat = float(d.get("GPS_LATITUDE", 0.0))
                lon = float(d.get("GPS_LONGITUDE", 0.0))
                # Only if coordinates look valid
                if abs(lat) > 0.0001 or abs(lon) > 0.0001:
                    self._landed_popup_done = True
                    # Hand off to MainWindow helper (opens browser and sets link label)
                    if hasattr(self.parent, "show_landed_map"):
                        self.parent.show_landed_map(lat, lon)
        except Exception as e:
            print("[LANDING MAP ERROR]:", e)

    # SETUP
    def _set_graphs(self):
        # Mission-time X axis graphs, SI titles
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
