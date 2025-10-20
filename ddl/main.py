import os
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QShortcut

from ddl.ui import Ui_MainWindow

from ddl.modules.managers.configuration_manager import ConfigManager
from ddl.modules.managers.window_manager import WindowManager
from ddl.modules.managers.terminal_manager import TerminalManager
from ddl.modules.managers.serial_manager import SerialManager
from ddl.modules.managers.graph_manager import GraphManager
from ddl.modules.managers.button_manager import ButtonManager

from ddl.modules.utility.connection_buffer import ConnectionBuffer
from ddl.modules.utility.clock_updater import ClockUpdater


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # -- UI --
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # -- Managers / Config --
        self.config         = ConfigManager
        self.window_manager = WindowManager(self)
        self.terminal       = TerminalManager(self)
        self.serial         = SerialManager(self)
        self.clock_updater  = ClockUpdater(self)
        self.button_manager = ButtonManager(self)
        self.graph_manager  = GraphManager(self)

        # -- Utility --
        self.connection_buffer = ConnectionBuffer(self)

        # Wiring: serial -> terminal (raw), serial -> graphs (dict)
        self.serial.data_available.connect(self.terminal.write)
        self.serial.update_graphs.connect(self.graph_manager.update)

        # Window/UI setup
        self._setup_window()
        self._setup_buttons()
        self._apply_config()

        # Start UTC clock & boot message
        self.clock_updater.update_global_time_label()
        self.clock_updater.start_time_update_thread()
        self.terminal.boot_up_message()
        self.update_status_bar("// #Successfully Started")
        self.show()

    # ---------- window ----------
    def _setup_window(self):
        window_name = self.config.get("application.name")
        window_icon = self.config.get("application.icon_path")
        self.app_status  = self.config.get("version.status")
        self.app_version = self.config.get("version.version")

        bauds_dic     = self.config.get("connection.bauds_dic")
        bauds_default = self.config.get("connection.bauds_default")

        self.setWindowTitle(window_name)
        if window_icon and os.path.exists(window_icon):
            self.setWindowIcon(QIcon(window_icon))

        if isinstance(bauds_dic, dict):
            self.ui.cb_bauds.addItems(list(bauds_dic.keys()))
        else:
            self.ui.cb_bauds.addItems(bauds_dic or [])

        if bauds_default:
            self.ui.cb_bauds.setCurrentText(bauds_default)

        self.window_version = f"{self.app_status}-{self.app_version}"
        self.window_id      = f"{window_name} | v: {self.window_version}"

    # ---------- buttons & shortcuts ----------
    def _setup_buttons(self):
        # Terminal input
        self.ui.terminal_input.returnPressed.connect(self.connection_buffer.send_data)
        self.ui.btn_send.clicked.connect(self.connection_buffer.send_data)

        # Serial buttons
        self.ui.btn_update_ports.clicked.connect(self.connection_buffer.update_ports)
        self.ui.btn_connect_serial.clicked.connect(self.connection_buffer.connect)

        # Recording toggle
        self.ui.btn_togle_log.clicked.connect(self.connection_buffer.toggle_recording)

        # Clear terminal
        self.ui.btn_clear.clicked.connect(self.terminal.clear)

        # NEW: Open saves, Clear all (guard if absent)
        if hasattr(self.ui, "btn_open_saves"):
            self.ui.btn_open_saves.clicked.connect(self.opn_logs)
        if hasattr(self.ui, "btn_clear_all"):
            self.ui.btn_clear_all.clicked.connect(self.clear_all)

        # Optional menu button
        if hasattr(self.ui, "btn_togle_menu"):
            self.ui.btn_togle_menu.clicked.connect(self.window_manager.togle_menu)

        # Shortcuts
        fs_shortcut = QShortcut(QKeySequence(Qt.Key_F11), self)
        fs_shortcut.activated.connect(self.window_manager.show_full_screen)

    # ---------- helpers ----------
    def clear_all(self):
        """Clear terminal, counters, and all graphs; keep app running."""
        # terminal
        try:
            self.terminal.clear()
        except Exception:
            pass

        # serial runtime counters / blackbox
        try:
            if hasattr(self.serial, "clear_runtime"):
                self.serial.clear_runtime()
            else:
                self.serial.received_count = 0
                self.serial.lost_count = 0
                self.serial.last_packet_count = None
        except Exception:
            pass

        # graphs
        try:
            if hasattr(self.graph_manager, "clear"):
                self.graph_manager.clear()
        except Exception:
            pass

        # reset labels
        if hasattr(self.ui, "lb_recv"): self.ui.lb_recv.setText("recv: 0")
        if hasattr(self.ui, "lb_lost"): self.ui.lb_lost.setText("lost: 0")
        if hasattr(self.ui, "lb_cmd_echo"): self.ui.lb_cmd_echo.setText("CMD_ECHO")
        if hasattr(self.ui, "lb_state"): self.ui.lb_state.setText("LAUNCH_PAD")

        self.update_status_bar("// cleared all")

    def update_status_bar(self, msg: str):
        if not msg:
            self.ui.statusBar.showMessage(f"// {self.window_id}")
        else:
            self.ui.statusBar.showMessage(f"// {self.window_id}    -   {msg}")

    def opn_logs(self):
        folder = self.serial.logs_path
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        # open folder in OS file explorer
        try:
            os.startfile(os.path.realpath(folder))  # Windows
        except AttributeError:
            # POSIX fallback
            import subprocess, sys
            if sys.platform.startswith("darwin"):
                subprocess.call(["open", folder])
            else:
                subprocess.call(["xdg-open", folder])

    def _apply_config(self):
        if self.config.get("application.settings.on_start_port_update"):
            self.connection_buffer.update_ports(override_message=True)
        if self.config.get("application.settings.on_start_maximized"):
            self.window_manager.maximize_app()

    def mousePressEvent(self, e):
        if hasattr(self.window_manager, "clickPostion"):
            self.window_manager.clickPostion = e.globalPos()

    def closeEvent(self, event):
        try:
            if hasattr(self.serial, "all_data") and self.serial.all_data:
                self.serial.all_data.close()
        except Exception:
            pass
