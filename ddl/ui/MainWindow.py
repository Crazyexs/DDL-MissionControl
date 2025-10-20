from PyQt5 import QtCore, QtGui, QtWidgets

LIGHT_BG = "#FAFAFA"; DARK_TEXT = "#111111"; PANEL_BG = "#FFFFFF"; BORDER = "#E5E5E5"
MONO = "Consolas"

def _font(pt: int, bold=False):
    f = QtGui.QFont(MONO, pt)
    f.setBold(bold)
    return f

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 800)
        MainWindow.setStyleSheet(f"""
            QMainWindow, QWidget, QFrame {{ background:{LIGHT_BG}; color:{DARK_TEXT}; font:14pt "{MONO}"; }}
            QStatusBar {{ background:#F2F2F2; color:#333; border-top:1px solid {BORDER}; font:12pt "{MONO}"; }}
            QLabel#topBadge {{ background:#F3F8F5; border:1px solid #D6E8DC; border-radius:6px; padding:4px 8px; font:14pt "{MONO}"; }}
            QGroupBox {{ background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:10px; margin-top:12px; font:bold 16pt "{MONO}"; }}
            QGroupBox::title {{ left:12px; top:2px; padding:2px 4px; color:#333; }}
            QLineEdit, QComboBox, QTextBrowser {{ background:#FFF; border:1px solid {BORDER}; border-radius:8px; padding:6px 8px; font:14pt "{MONO}"; }}
            QPushButton {{ background:#FFF; border:1px solid {BORDER}; border-radius:10px; padding:8px 14px; font:bold 14pt "{MONO}"; }}
            QPushButton:hover {{ background:#F6F6F6; }} QPushButton:pressed {{ background:#EFEFEF; }}
        """)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        self.master = QtWidgets.QVBoxLayout(self.centralwidget)
        self.master.setContentsMargins(10,10,6,6); self.master.setSpacing(10)

        # Top badges
        self.topBar = QtWidgets.QHBoxLayout(); self.topBar.setSpacing(8)
        self.btn_togle_menu = QtWidgets.QPushButton("≡"); self.btn_togle_menu.setFixedSize(40,40)
        self.topBar.addWidget(self.btn_togle_menu)

        self.time_label = QtWidgets.QLabel("00:00:00 UTC"); self.time_label.setObjectName("time_label")
        self.time_label.setFont(_font(16,True)); self.time_label.setAlignment(QtCore.Qt.AlignCenter)
        self.time_label.setMinimumWidth(160); self.time_label.setObjectName("topBadge")
        self.topBar.addWidget(self.time_label)

        self.lb_state = QtWidgets.QLabel("LAUNCH_PAD"); self.lb_state.setObjectName("lb_state")
        self.lb_state.setFont(_font(16,True)); self.lb_state.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_state.setMinimumWidth(160); self.lb_state.setObjectName("topBadge")
        self.topBar.addWidget(self.lb_state)

        self.lb_ping = QtWidgets.QLabel("0 ms"); self.lb_ping.setObjectName("lb_ping")
        self.lb_ping.setAlignment(QtCore.Qt.AlignCenter); self.lb_ping.setMinimumWidth(100)
        self.lb_ping.setObjectName("topBadge"); self.topBar.addWidget(self.lb_ping)

        self.topBar.addStretch(1)

        self.lb_recv = QtWidgets.QLabel("recv: 0"); self.lb_recv.setObjectName("lb_recv")
        self.lb_recv.setAlignment(QtCore.Qt.AlignCenter); self.lb_recv.setMinimumWidth(110)
        self.lb_recv.setObjectName("topBadge"); self.topBar.addWidget(self.lb_recv)

        self.lb_lost = QtWidgets.QLabel("lost: 0"); self.lb_lost.setObjectName("lb_lost")
        self.lb_lost.setAlignment(QtCore.Qt.AlignCenter); self.lb_lost.setMinimumWidth(110)
        self.lb_lost.setObjectName("topBadge"); self.topBar.addWidget(self.lb_lost)

        self.lb_cmd_echo = QtWidgets.QLabel("CMD_ECHO"); self.lb_cmd_echo.setObjectName("lb_cmd_echo")
        self.lb_cmd_echo.setAlignment(QtCore.Qt.AlignCenter); self.lb_cmd_echo.setMinimumWidth(160)
        self.lb_cmd_echo.setObjectName("topBadge"); self.topBar.addWidget(self.lb_cmd_echo)

        self.master.addLayout(self.topBar)

        # Middle area (left controls, right graphs/terminal)
        self.mid = QtWidgets.QHBoxLayout(); self.mid.setSpacing(10)

        # Left column
        self.leftCol = QtWidgets.QVBoxLayout(); self.leftCol.setSpacing(10)

        # LINK
        self.grpConn = QtWidgets.QGroupBox("LINK"); self.grpConn.setFont(_font(16,True))
        self.grpConnLayout = QtWidgets.QGridLayout(self.grpConn); self.grpConnLayout.setContentsMargins(10,20,10,10)
        self.lb_Ports = QtWidgets.QLabel("PORT:"); self.grpConnLayout.addWidget(self.lb_Ports,0,0)
        self.cb_ports = QtWidgets.QComboBox(); self.cb_ports.setObjectName("cb_ports"); self.grpConnLayout.addWidget(self.cb_ports,0,1)
        self.lb_Baudrate = QtWidgets.QLabel("BAUDRATE:"); self.grpConnLayout.addWidget(self.lb_Baudrate,1,0)
        self.cb_bauds = QtWidgets.QComboBox(); self.cb_bauds.setObjectName("cb_bauds"); self.grpConnLayout.addWidget(self.cb_bauds,1,1)
        self.btn_connect_serial = QtWidgets.QPushButton("disconnected"); self.btn_connect_serial.setCheckable(True)
        self.btn_connect_serial.setObjectName("btn_connect_serial"); self.grpConnLayout.addWidget(self.btn_connect_serial,2,0,1,2)
        self.btn_update_ports = QtWidgets.QPushButton("Update"); self.btn_update_ports.setObjectName("btn_update_ports")
        self.grpConnLayout.addWidget(self.btn_update_ports,3,0,1,2)
        self.leftCol.addWidget(self.grpConn)

        # UTILS
        self.grpUtil = QtWidgets.QGroupBox("UTILS"); self.grpUtil.setFont(_font(16, True))
        self.utilLayout = QtWidgets.QGridLayout(self.grpUtil)
        self.utilLayout.setContentsMargins(10, 20, 10, 10)
        self.utilLayout.setHorizontalSpacing(8); self.utilLayout.setVerticalSpacing(6)
        self.btn_togle_log = QtWidgets.QPushButton("RECORD"); self.btn_togle_log.setCheckable(True)
        self.btn_togle_log.setObjectName("btn_togle_log"); self.utilLayout.addWidget(self.btn_togle_log, 0, 0)
        self.btn_open_saves = QtWidgets.QPushButton("Open Saves"); self.btn_open_saves.setObjectName("btn_open_saves")
        self.utilLayout.addWidget(self.btn_open_saves, 0, 1)
        self.btn_clear_all = QtWidgets.QPushButton("Clear All"); self.btn_clear_all.setObjectName("btn_clear_all")
        self.utilLayout.addWidget(self.btn_clear_all, 1, 0)
        self.btn_clear = QtWidgets.QPushButton("Clear Terminal"); self.btn_clear.setObjectName("btn_clear")
        self.utilLayout.addWidget(self.btn_clear, 1, 1)
        self.leftCol.addWidget(self.grpUtil)

        # MISSION INFO
        self.grpInfo = QtWidgets.QGroupBox("MISSION INFO"); self.grpInfo.setFont(_font(16,True))
        self.infoLayout = QtWidgets.QFormLayout(self.grpInfo); self.infoLayout.setContentsMargins(10,20,10,10)

        self.lb_mission_time = QtWidgets.QLabel("--:--:-- UTC"); self.lb_mission_time.setObjectName("lb_mission_time")
        self.lb_temp = QtWidgets.QLabel("--.- °C"); self.lb_temp.setObjectName("lb_temp")
        self.lb_gps = QtWidgets.QLabel("0.0000, 0.0000 | alt 0.0 m | sats 0"); self.lb_gps.setObjectName("lb_gps")

        self.lb_map_link = QtWidgets.QLabel(""); self.lb_map_link.setOpenExternalLinks(True)
        self.lb_map_link.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.lb_map_link.setWordWrap(True); self.lb_map_link.setObjectName("lb_map_link")

        self.tb_last_telemetry = QtWidgets.QTextBrowser(); self.tb_last_telemetry.setObjectName("tb_last_telemetry")
        self.tb_last_telemetry.setMinimumHeight(110)
        self.tb_last_telemetry.setStyleSheet("QTextBrowser { font: 12pt \"" + MONO + "\"; }")
        self.tb_last_telemetry.setReadOnly(True)

        self.infoLayout.addRow("Mission Time:", self.lb_mission_time)
        self.infoLayout.addRow("Temperature:", self.lb_temp)
        self.infoLayout.addRow("GPS:", self.lb_gps)
        self.infoLayout.addRow("Map (on LANDED):", self.lb_map_link)
        self.infoLayout.addRow("Last telemetry:", self.tb_last_telemetry)

        self.leftCol.addWidget(self.grpInfo)
        self.leftCol.addStretch(1)

        # Right column (graphs bigger than left)
        self.rightCol = QtWidgets.QVBoxLayout(); self.rightCol.setSpacing(10)

        self.TelemetryGroup = QtWidgets.QGroupBox("FLY TELEMETRY"); self.TelemetryGroup.setFont(_font(16,True))
        self.telemetryGroupLayout = QtWidgets.QVBoxLayout(self.TelemetryGroup)
        self.telemetry_graphs = QtWidgets.QVBoxLayout(); self.telemetry_graphs.setObjectName("telemetry_graphs")
        self.telemetryGroupLayout.addLayout(self.telemetry_graphs, 1)
        self.rightCol.addWidget(self.TelemetryGroup, 5)

        self.grpTerminal = QtWidgets.QGroupBox("TERMINAL"); self.grpTerminal.setFont(_font(16,True))
        self.termLayout = QtWidgets.QVBoxLayout(self.grpTerminal)
        self.terminal = QtWidgets.QTextBrowser(); self.terminal.setObjectName("terminal"); self.terminal.setMinimumHeight(140)
        self.terminal.setFont(_font(14)); self.termLayout.addWidget(self.terminal)
        self.cmdRow = QtWidgets.QHBoxLayout(); self.terminal_input = QtWidgets.QLineEdit()
        self.terminal_input.setObjectName("terminal_input"); self.terminal_input.setPlaceholderText(">_")
        self.btn_send = QtWidgets.QPushButton(">>"); self.btn_send.setObjectName("btn_send"); self.btn_send.setFixedWidth(64)
        self.cmdRow.addWidget(self.terminal_input, 1); self.cmdRow.addWidget(self.btn_send, 0)
        self.termLayout.addLayout(self.cmdRow)
        self.rightCol.addWidget(self.grpTerminal, 2)

        # Add both columns to the middle layout with stretch factors (left=1, right=5)
        self.mid.addLayout(self.leftCol, 1)
        self.mid.addLayout(self.rightCol, 5)

        # Finish
        self.master.addLayout(self.mid)
        self.statusBar = QtWidgets.QStatusBar(MainWindow); MainWindow.setStatusBar(self.statusBar)
        MainWindow.setWindowTitle("CanSat Ground Station")
