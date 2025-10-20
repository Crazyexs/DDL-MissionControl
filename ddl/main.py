import os

from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QShortcut

# === UI ===
# NOTE: this expects your ui package to provide Ui_MainWindow
#       (the single-page version we generated earlier)
from ddl.ui import Ui_MainWindow

# === Managers ===
from ddl.modules.managers import (
    ConfigManager,
    WindowManager,
    TerminalManager,
    SerialManager,
    GraphManager,
    ButtonManager
)

# === Utility ===
from ddl.modules.utility import (
    ConnectionBuffer,
    ClockUpdater
)

# ===================================================================== #

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # -- Set up UI --
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # -- Managers --
        # ConfigManager is a class with static .get(...) access in your codebase
        self.config = ConfigManager

        self.window_manager = WindowManager(self)
        self.terminal       = TerminalManager(self)
        self.serial         = SerialManager(self)
        self.clock_updater  = ClockUpdater(self)
        self.button_manager = ButtonManager(self)
        self.graph_manager  = GraphManager(self)

        # -- Utility --
        self.connection_buffer = ConnectionBuffer(self)

        # Serial → Terminal passthrough (raw line echo)
        self.serial.data_available.connect(self.terminal.write)
        # Serial → Graph updates (parsed dict)
        self.serial.update_graphs.connect(self.graph_manager.update)

        # -- Window/UI setup --
        self.setup_window()
        self.setup_buttons()
        self.apply_config()

        # -- Start UTC clock --
        self.clock_updater.update_global_time_label()
        self.clock_updater.start_time_update_thread()

        # -- Boot message --
        self.terminal.boot_up_message()
        self.update_status_bar("// #Successfully Started")

        self.show()

    # ================================================================= #
    # Window setup
    def setup_window(self):
        # Window title/icon from config
        window_name = self.config.get("application.name")
        window_icon = self.config.get("application.icon_path")

        self.app_status  = self.config.get("version.status")
        self.app_version = self.config.get("version.version")

        # Baudrate selections
        bauds_dic      = self.config.get("connection.bauds_dic")  # dict of str->int
        bauds_default  = self.config.get("connection.bauds_default")

        # Use normal framed window for max sunlight readability
        self.setWindowTitle(window_name)
        if window_icon and os.path.exists(window_icon):
            self.setWindowIcon(QIcon(window_icon))

        # Fill baudrate combos (keys)
        if isinstance(bauds_dic, dict):
            self.ui.cb_bauds.addItems(list(bauds_dic.keys()))
        else:
            # fallback if config already returns list of keys
            self.ui.cb_bauds.addItems(bauds_dic)

        if bauds_default:
            self.ui.cb_bauds.setCurrentText(bauds_default)

        # Human-readable version info
        self.window_version = f"{self.app_status}-{self.app_version}"
        self.window_id      = f"{window_name} | v: {self.window_version}"

    # Buttons and shortcuts
    def setup_buttons(self):
        # Terminal input
        self.ui.terminal_input.returnPressed.connect(
            self.connection_buffer.send_data
        )
        self.ui.btn_send.clicked.connect(
            self.connection_buffer.send_data
        )

        # Serial buttons
        self.ui.btn_update_ports.clicked.connect(
            self.connection_buffer.update_ports
        )
        self.ui.btn_connect_serial.clicked.connect(
            self.connection_buffer.connect
        )

        # Recording toggle (uses SerialManager CSV writer Flight_<TEAM_ID>.csv)
        self.ui.btn_togle_log.clicked.connect(
            self.connection_buffer.toggle_recording
        )

        # Terminal clear
        self.ui.btn_clear.clicked.connect(
            self.terminal.clear
        )

        # Optional menu button (kept for parity with your UI)
        if hasattr(self.ui, "btn_togle_menu"):
            self.ui.btn_togle_menu.clicked.connect(
                self.window_manager.togle_menu
            )

        # Shortcuts (F11 fullscreen, Esc toggle menu if present)
        fs_shortcut = QShortcut(QKeySequence(Qt.Key_F11), self)
        fs_shortcut.activated.connect(self.window_manager.show_full_screen)

        if hasattr(self.ui, "btn_togle_menu"):
            menu_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
            menu_shortcut.activated.connect(self.window_manager.togle_menu)

    # Mouse press for (optional) drag handlers in WindowManager
    def mousePressEvent(self, e):
        if hasattr(self.window_manager, "clickPostion"):
            self.window_manager.clickPostion = e.globalPos()

    # Status bar helper
    def update_status_bar(self, msg: str):
        if not msg:
            self.ui.statusBar.showMessage(f"// {self.window_id}")
        else:
            self.ui.statusBar.showMessage(f"// {self.window_id}    -   {msg}")

    # Open logs folder
    def opn_logs(self):
        folder = self.serial.logs_path
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        os.startfile(os.path.realpath(folder))

    # Apply startup config switches
    def apply_config(self):
        update_ports_on_start = self.config.get("application.settings.on_start_port_update")
        maximized_on_start    = self.config.get("application.settings.on_start_maximized")

        if update_ports_on_start:
            # mark your (optional) checkbox if you have one
            if hasattr(self.ui, "btn_auto_update"):
                self.ui.btn_auto_update.setChecked(True)
            self.connection_buffer.update_ports(override_message=True)

        if maximized_on_start:
            if hasattr(self.ui, "btn_start_max"):
                self.ui.btn_start_max.setChecked(True)
            self.window_manager.maximize_app()

    def closeEvent(self, event):
        # graceful file handle close
        try:
            if hasattr(self.serial, "all_data") and self.serial.all_data:
                self.serial.all_data.close()
        except:
            pass
