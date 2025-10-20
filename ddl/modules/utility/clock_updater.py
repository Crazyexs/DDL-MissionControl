# --- clock_updater.py (PATCH block: replace update_global_time_label) ---
from datetime import datetime, timezone

class ClockUpdater(QObject):
    # ... keep __init__ as-is ...

    def update_global_time_label(self):
        # show UTC explicitly for mission time
        t_utc = datetime.now(timezone.utc).strftime("%H:%M:%S")
        # ใช้ข้อความเรียบ ๆ สีเข้มบนพื้นสว่าง (อ่านกลางแดด)
        self.ui.time_label.setText(f"{t_utc} UTC")
