# -*- coding: utf-8 -*-
# Single-page, bright-sunlight UI for CanSat Ground Station (G14, G15)
# Creates a placeholder `telemetry_graphs` layout for GraphManager.
# Keeps legacy objectNames where useful to avoid breaking your managers.

from PyQt5 import QtCore, QtGui, QtWidgets

LIGHT_BG = "#FAFAFA"
DARK_TEXT = "#111111"
PANEL_BG = "#FFFFFF"
ACCENT = "#0A5"
BORDER = "#E5E5E5"
MONO = "Arame Mono"  # keep your original font family

def _font(pt: int, bold=False):
    f = QtGui.QFont()
    f.setFamily(MONO)
    f.setPointSize(pt)
    f.setBold(bold)
    return f

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 800)
        MainWindow.setMinimumSize(QtCore.QSize(1024, 700))

        # ---------- Global, bright-sunlight stylesheet (G14) ----------
        MainWindow.setStyleSheet(f"""
            QMainWindow, QWidget, QFrame {{
                background: {LIGHT_BG};
                color: {DARK_TEXT};
                font: 14pt "{MONO}";
            }}
            QStatusBar {{
                background: #F2F2F2;
                color: #333;
                border-top: 1px solid {BORDER};
                font: 12pt "{MONO}";
            }}
            QLabel#topBadge {{
                background: #F3F8F5;
                border: 1px solid #D6E8DC;
                border-radius: 6px;
                padding: 4px 8px;
                font: 14pt "{MONO}";
            }}
            QGroupBox {{
                background: {PANEL_BG};
                border: 1px solid {BORDER};
                border-radius: 10px;
                margin-top: 12px;
                font: bold 16pt "{MONO}";
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                top: 2px;
                padding: 2px 4px;
                color: #333;
            }}
            QLineEdit, QComboBox, QTextBrowser {{
                background: #FFFFFF;
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 6px 8px;
                font: 14pt "{MONO}";
            }}
            QPushButton {{
                background: #FFFFFF;
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 8px 14px;
                font: bold 14pt "{MONO}";
            }}
            QPushButton:hover {{ background: #F6F6F6; }}
            QPushButton:pressed {{ background: #EFEFEF; }}
            QPushButton#danger {{ border-color: #DDAAAA; }}
            QPushButton#danger:hover {{ background:#FFF5F5; }}
            QScrollBar:vertical {{
                background: #F2F2F2; width: 12px; margin: 14px 0 14px 0; border: none;
            }}
            QScrollBar::handle:vertical {{
                background: #CFCFCF; min-height: 30px; border-radius: 6px;
            }}
        """)

        # ---------- Central widget & master layout ----------
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        self.master = QtWidgets.QVBoxLayout(self.centralwidget)
        self.master.setContentsMargins(10, 10, 10, 6)
        self.master.setSpacing(10)

        # ---------- Top bar (mission time, state, ping, recv/lost, CMD_ECHO) ----------
        self.topBar = QtWidgets.QHBoxLayout()
        self.topBar.setSpacing(8)

        # left: menu button placeholders (optional)
        self.btn_togle_menu = QtWidgets.QPushButton("≡")
        self.btn_togle_menu.setFixedSize(40, 40)
        self.btn_togle_menu.setToolTip("Menu")
        self.topBar.addWidget(self.btn_togle_menu)

        self.time_label = QtWidgets.QLabel("00:00:00 UTC")
        self.time_label.setObjectName("time_label")
        self.time_label.setFont(_font(16, True))
        self.time_label.setAlignment(QtCore.Qt.AlignCenter)
        self.time_label.setMinimumWidth(160)
        self.time_label.setProperty("class", "badge")
        self.time_label.setObjectName("topBadge")
        self.topBar.addWidget(self.time_label)

        self.lb_state = QtWidgets.QLabel("LAUNCH_PAD")
        self.lb_state.setObjectName("lb_state")
        self.lb_state.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_state.setFont(_font(16, True))
        self.lb_state.setMinimumWidth(160)
        self.lb_state.setObjectName("topBadge")
        self.topBar.addWidget(self.lb_state)

        self.lb_ping = QtWidgets.QLabel("0 ms")
        self.lb_ping.setObjectName("lb_ping")
        self.lb_ping.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_ping.setMinimumWidth(100)
        self.lb_ping.setObjectName("topBadge")
        self.topBar.addWidget(self.lb_ping)

        # middle stretch
        self.topBar.addStretch(1)

        # right: new compliance labels (G8, G16)
        self.lb_recv = QtWidgets.QLabel("recv: 0")
        self.lb_recv.setObjectName("lb_recv")
        self.lb_recv.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_recv.setMinimumWidth(110)
        self.lb_recv.setObjectName("topBadge")
        self.topBar.addWidget(self.lb_recv)

        self.lb_lost = QtWidgets.QLabel("lost: 0")
        self.lb_lost.setObjectName("lb_lost")
        self.lb_lost.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_lost.setMinimumWidth(110)
        self.lb_lost.setObjectName("topBadge")
        self.topBar.addWidget(self.lb_lost)

        self.lb_cmd_echo = QtWidgets.QLabel("CMD_ECHO")
        self.lb_cmd_echo.setObjectName("lb_cmd_echo")
        self.lb_cmd_echo.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_cmd_echo.setMinimumWidth(160)
        self.lb_cmd_echo.setObjectName("topBadge")
        self.topBar.addWidget(self.lb_cmd_echo)

        self.master.addLayout(self.topBar)

        # ---------- Mid area: left control panel + right telemetry area (single-page, G15) ----------
        self.mid = QtWidgets.QHBoxLayout()
        self.mid.setSpacing(10)

        # Left column (connection & quick controls)
        self.leftCol = QtWidgets.QVBoxLayout()
        self.leftCol.setSpacing(10)

        # Connection group
        self.grpConn = QtWidgets.QGroupBox("LINK")
        self.grpConn.setFont(_font(16, True))
        self.grpConnLayout = QtWidgets.QGridLayout(self.grpConn)
        self.grpConnLayout.setContentsMargins(10, 20, 10, 10)
        self.grpConnLayout.setHorizontalSpacing(8)
        self.grpConnLayout.setVerticalSpacing(6)

        self.lb_Ports = QtWidgets.QLabel("PORT:")
        self.lb_Ports.setObjectName("lb_Ports")
        self.grpConnLayout.addWidget(self.lb_Ports, 0, 0)
        self.cb_ports = QtWidgets.QComboBox()
        self.cb_ports.setObjectName("cb_ports")
        self.grpConnLayout.addWidget(self.cb_ports, 0, 1)

        self.lb_Baudrate = QtWidgets.QLabel("BAUDRATE:")
        self.lb_Baudrate.setObjectName("lb_Baudrate")
        self.grpConnLayout.addWidget(self.lb_Baudrate, 1, 0)
        self.cb_bauds = QtWidgets.QComboBox()
        self.cb_bauds.setObjectName("cb_bauds")
        self.grpConnLayout.addWidget(self.cb_bauds, 1, 1)

        self.btn_connect_serial = QtWidgets.QPushButton("disconnected")
        self.btn_connect_serial.setCheckable(True)
        self.btn_connect_serial.setObjectName("btn_connect_serial")
        self.grpConnLayout.addWidget(self.btn_connect_serial, 2, 0, 1, 2)

        self.btn_update_ports = QtWidgets.QPushButton("Update")
        self.btn_update_ports.setObjectName("btn_update_ports")
        self.grpConnLayout.addWidget(self.btn_update_ports, 3, 0, 1, 2)

        self.leftCol.addWidget(self.grpConn)

        # Utilities group (record & clear)
        self.grpUtil = QtWidgets.QGroupBox("UTILS")
        self.grpUtil.setFont(_font(16, True))
        self.utilLayout = QtWidgets.QHBoxLayout(self.grpUtil)
        self.utilLayout.setContentsMargins(10, 20, 10, 10)
        self.btn_togle_log = QtWidgets.QPushButton("RECORD")
        self.btn_togle_log.setCheckable(True)
        self.btn_togle_log.setObjectName("btn_togle_log")
        self.btn_clear = QtWidgets.QPushButton("Clear")
        self.btn_clear.setObjectName("btn_clear")
        self.utilLayout.addWidget(self.btn_togle_log)
        self.utilLayout.addWidget(self.btn_clear)
        self.leftCol.addWidget(self.grpUtil)

        # Mission info group (text labels required by spec)
        self.grpInfo = QtWidgets.QGroupBox("MISSION INFO")
        self.grpInfo.setFont(_font(16, True))
        self.infoLayout = QtWidgets.QFormLayout(self.grpInfo)
        self.infoLayout.setContentsMargins(10, 20, 10, 10)
        self.infoLayout.setHorizontalSpacing(12)
        self.infoLayout.setVerticalSpacing(8)

        self.lb_mission_time = QtWidgets.QLabel("--:--:-- UTC")
        self.lb_mission_time.setObjectName("lb_mission_time")
        self.lb_temp = QtWidgets.QLabel("--.- °C")
        self.lb_temp.setObjectName("lb_temp")
        self.lb_gps = QtWidgets.QLabel("0.0000, 0.0000 | alt 0.0 m | sats 0")
        self.lb_gps.setObjectName("lb_gps")

        self.infoLayout.addRow("Mission Time:", self.lb_mission_time)
        self.infoLayout.addRow("Temperature:", self.lb_temp)
        self.infoLayout.addRow("GPS:", self.lb_gps)

        self.leftCol.addWidget(self.grpInfo)
        self.leftCol.addStretch(1)

        self.mid.addLayout(self.leftCol, 1)  # left column weight

        # Right column (Telemetry graphs + Terminal — same page)
        self.rightCol = QtWidgets.QVBoxLayout()
        self.rightCol.setSpacing(10)

        # Telemetry group (graphs placeholder)
        self.TelemetryGroup = QtWidgets.QGroupBox("FLY TELEMETRY")
        self.TelemetryGroup.setObjectName("TelemetryGroup")
        self.TelemetryGroup.setFont(_font(16, True))
        self.telemetryGroupLayout = QtWidgets.QVBoxLayout(self.TelemetryGroup)
        self.telemetryGroupLayout.setContentsMargins(10, 26, 10, 10)
        self.telemetryGroupLayout.setSpacing(8)

        # Placeholder layout where GraphManager will add its GraphicsLayoutWidget
        self.telemetry_graphs = QtWidgets.QVBoxLayout()
        self.telemetry_graphs.setObjectName("telemetry_graphs")
        self.telemetry_graphs.setContentsMargins(0, 0, 0, 0)
        self.telemetry_graphs.setSpacing(0)
        self.telemetryGroupLayout.addLayout(self.telemetry_graphs, 1)

        self.rightCol.addWidget(self.TelemetryGroup, 5)

        # Terminal (always visible, same page → complies with G15)
        self.grpTerminal = QtWidgets.QGroupBox("TERMINAL")
        self.grpTerminal.setFont(_font(16, True))
        self.termLayout = QtWidgets.QVBoxLayout(self.grpTerminal)
        self.termLayout.setContentsMargins(10, 20, 10, 10)

        self.terminal = QtWidgets.QTextBrowser()
        self.terminal.setObjectName("terminal")
        self.terminal.setMinimumHeight(140)
        self.terminal.setFont(_font(14))
        self.termLayout.addWidget(self.terminal)

        self.cmdRow = QtWidgets.QHBoxLayout()
        self.terminal_input = QtWidgets.QLineEdit()
        self.terminal_input.setObjectName("terminal_input")
        self.terminal_input.setPlaceholderText(">_")
        self.btn_send = QtWidgets.QPushButton(">>")
        self.btn_send.setObjectName("btn_send")
        self.btn_send.setFixedWidth(64)
        self.cmdRow.addWidget(self.terminal_input, 1)
        self.cmdRow.addWidget(self.btn_send, 0)
        self.termLayout.addLayout(self.cmdRow)

        self.rightCol.addWidget(self.grpTerminal, 2)

        self.mid.addLayout(self.rightCol, 3)  # right column weight

        self.master.addLayout(self.mid)

        # ---------- Status bar ----------
        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusBar)

        # ---------- Retranslations ----------
        self._retranslateUi(MainWindow)

        # focus defaults
        self.terminal_input.setFocus()

        # connect slots by name (optional if you wire up in your Window class)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def _retranslateUi(self, MainWindow):
        _ = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_("MainWindow", "CanSat Ground Station"))
        # button texts already set; keep here if you want i18n later
