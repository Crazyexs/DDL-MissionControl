from PyQt5.QtCore import QObject, QTimer
from datetime import datetime, timezone

class ClockUpdater(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.ui = parent.ui
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_global_time_label)

    def start_time_update_thread(self): self.timer.start()
    def update_global_time_label(self):
        t_utc = datetime.now(timezone.utc).strftime("%H:%M:%S")
        if hasattr(self.ui, "time_label"): self.ui.time_label.setText(f"{t_utc} UTC")
        if hasattr(self.ui, "lb_mission_time"): self.ui.lb_mission_time.setText(f"{t_utc} UTC")
