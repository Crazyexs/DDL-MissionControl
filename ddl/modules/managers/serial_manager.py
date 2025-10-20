# --- serial_manager.py (DROP-IN PATCH) ---
import os
import csv
import time
import winsound
import numpy as np
import serial
import serial.tools.list_ports
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QThread

REQUIRED_FIELDS = [
    "TEAM_ID","MISSION_TIME","PACKET_COUNT","MODE","STATE","ALTITUDE",
    "TEMPERATURE","PRESSURE","VOLTAGE",
    "GYRO_R","GYRO_P","GYRO_Y",
    "ACCEL_R","ACCEL_P","ACCEL_Y",
    "MAG_R","MAG_P","MAG_Y",
    "AUTO_GYRO_ROTATION_RATE",
    "GPS_TIME","GPS_ALTITUDE","GPS_LATITUDE","GPS_LONGITUDE","GPS_SATS",
    "CMD_ECHO"
]

class SerialManager(QObject):
    data_available = pyqtSignal(str)     # raw line
    update_graphs = pyqtSignal(dict)     # parsed dict for graphs/labels

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.ui = parent.ui
        self.terminal = parent.terminal
        self.config = parent.config

        # serial
        self.is_connected = False
        self.is_unplugged = False
        self.alarm = self.config.get("connection.alarm")
        self.ser = serial.Serial()
        self.ser.timeout = self.config.get("connection.time_out")

        # logs/CSV
        self.logs_path = self.config.get("application.settings.logs_folder")
        os.makedirs(self.logs_path, exist_ok=True)
        os.makedirs(f"{self.logs_path}/BlackBox", exist_ok=True)
        self.record_enabled = True
        self.team_id = str(self.config.get("application.settings.team_id"))
        self.csv_header = list(self.config.get("telemetry.csv.header"))
        self.file_pattern = self.config.get("telemetry.csv.filename_pattern")
        self.csv_file_path = os.path.join(
            self.logs_path,
            self.file_pattern.replace("${TEAM_ID}", self.team_id)
        )
        self.csv_file = None
        self.csv_writer = None
        self.csv_header_written = False

        # dummy
        self.dummy_enabled = False
        self.dummy_update_time = self.config.get("graphs.default_update_time")

        # serial settings
        self.baudratesDIC = self.config.get("connection.bauds_dic")
        self.filter_character = self.config.get("connection.filter_character")
        self.portList = []

        # messages (from messages.json)
        self.message_unplugged = self.config.get("serial.un_plugged", 2)
        self.message_replugged = self.config.get("serial.re_plugged", 2)

        # packet/loss tracking (G16)
        self.received_count = 0
        self.lost_count = 0
        self.last_packet_count = None

        # SIM guard
        self.sim_enabled = False
        self.sim_activated = False

        # last dummy values
        self.last_latitude = 42.842835
        self.last_longitude = -2.668065
        self.last_temperature = 15.0
        self.last_altitude = 0.0

    # ---------------- Ports ---------------- #
    def update_ports(self):
        try:
            self.portList = [p.device for p in serial.tools.list_ports.comports()]
        except Exception as e:
            self.parent.terminal.write(f"[-] Error Updating Ports - {e}")

    # ---------------- Connect/Disconnect ---------------- #
    def connect(self):
        try:
            # port/baud ควรถูกตั้งค่า self.ser.port, self.ser.baudrate ในส่วน UI ก่อนเรียก connect()
            self.ser.open()
            self._open_csv_if_needed()
            self.start_thread()
        except Exception as e:
            self.parent.terminal.write(f"[-] Error Connecting - {e}")
            try: self.ser.close()
            except: pass

    def disconnect(self):
        try:
            self.stop_thread()
            self._close_csv_if_needed()
            self.ser.close()
        except Exception as e:
            self.parent.terminal.write(f"[-] Error Disconnecting - {e}")

    # ---------------- CSV helpers ---------------- #
    def _open_csv_if_needed(self):
        if not self.record_enabled: return
        new_file = not os.path.exists(self.csv_file_path)
        self.csv_file = open(self.csv_file_path, "a", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.csv_file, delimiter=",")
        if new_file and self.config.get("telemetry.csv.include_header"):
            self.csv_writer.writerow(self.csv_header)
            self.csv_header_written = True

    def _close_csv_if_needed(self):
        if self.csv_file:
            try: self.csv_file.close()
            except: pass
        self.csv_file = None
        self.csv_writer = None
        self.csv_header_written = False

    # ---------------- Send Commands (G1,G11–G12,F3,F7) ---------------- #
    def send_data(self, data):
        try:
            self.ser.write(bytes(data, "utf-8"))
            self.terminal.write(self.config.get("commands.sent", 2).replace("$CMD", data))
        except Exception as e:
            self.terminal.write(f"[-] Error Sending Data - {e}")

    def cmd_cx(self, on=True):
        s = f"CMD,{self.team_id},CX,{'ON' if on else 'OFF'}\r\n"
        self.send_data(s)

    def cmd_st(self, timestr="GPS"):
        # timestr in "hh:mm:ss" or "GPS"
        s = f"CMD,{self.team_id},ST,{timestr}\r\n"
        self.send_data(s)

    def cmd_cal(self):
        s = f"CMD,{self.team_id},CAL\r\n"
        self.send_data(s)

    def cmd_sim(self, mode):  # mode in {"ENABLE","ACTIVATE","DISABLE"}
        s = f"CMD,{self.team_id},SIM,{mode}\r\n"
        self.send_data(s)
        if mode == "ENABLE":  self.sim_enabled = True
        if mode == "ACTIVATE": self.sim_activated = True
        if mode == "DISABLE":
            self.sim_enabled = False
            self.sim_activated = False

    def cmd_simp(self, pressure_pa: int):
        if not (self.sim_enabled and self.sim_activated):
            self.terminal.write(self.config.get("commands.guard_sim", 2))
            return
        s = f"CMD,{self.team_id},SIMP,{int(pressure_pa)}\r\n"
        self.send_data(s)

    def cmd_mec(self, device: str, on=True):
        s = f"CMD,{self.team_id},MEC,{device},{'ON' if on else 'OFF'}\r\n"
        self.send_data(s)

    # ---------------- Reader ---------------- #
    def read_serial(self):
        try:
            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                return

            # write raw log
            self.all_data.write(f"[{datetime.now()}]: {line}\n")

            # Allow optional leading filter char (backward-compat)
            if self.filter_character and line.startswith(self.filter_character):
                line = line.replace(self.filter_character, "", 1).strip()

            # CSV parse (comma)
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < len(REQUIRED_FIELDS):
                # not our telemetry line; just echo to terminal
                self.data_available.emit(line)
                return

            # Build dict
            data = dict(zip(REQUIRED_FIELDS, parts[:len(REQUIRED_FIELDS)]))

            # Update packet counters (G16)
            try:
                pkt = int(data["PACKET_COUNT"])
                if self.last_packet_count is None:
                    self.received_count = 1
                else:
                    step = pkt - self.last_packet_count
                    if step <= 0:
                        # processor reset? still count received
                        self.received_count += 1
                    else:
                        # if jump >1, lost = step-1
                        lost_inc = max(0, step - 1)
                        self.lost_count += lost_inc
                        self.received_count += 1
                self.last_packet_count = pkt
            except:
                pass

            # Update UI labels if present
            try:
                if hasattr(self.ui, "lb_recv"):
                    self.ui.lb_recv.setText(f"{self.received_count}")
                if hasattr(self.ui, "lb_lost"):
                    self.ui.lb_lost.setText(f"{self.lost_count}")
                if hasattr(self.ui, "lb_cmd_echo"):
                    self.ui.lb_cmd_echo.setText(data.get("CMD_ECHO", ""))
            except:
                pass

            # Export to CSV (G2)
            if self.record_enabled and self.csv_writer:
                self.csv_writer.writerow([data.get(h, "") for h in self.csv_header])

            # Push to graphs
            self.update_graphs.emit(data)
            self.data_available.emit(line)

        except Exception as e:
            try:
                self.all_data.write("[EXCEPTION]: " + str(e) + "\n")
            except:
                pass
            print("[EXCEPTION]: " + str(e))

    # ---------------- Dummy (for offline test @1Hz) ---------------- #
    def dummy_serial(self):
        # minimal synthetic line respecting required fields (not all used by graphs)
        pkt = (self.last_packet_count or 0) + 1
        self.last_packet_count = pkt
        self.received_count += 1

        self.last_latitude += np.random.uniform(0.00001, 0.000001)
        self.last_longitude += np.random.uniform(0.00001, 0.000001)
        self.last_altitude += np.random.uniform(0, 1.0)
        self.last_temperature += np.random.uniform(-0.05, 0.05)

        row = {
            "TEAM_ID": self.team_id,
            "MISSION_TIME": datetime.utcnow().strftime("%H:%M:%S"),
            "PACKET_COUNT": str(pkt),
            "MODE": "F",
            "STATE": "LAUNCH_PAD",
            "ALTITUDE": f"{self.last_altitude:.1f}",
            "TEMPERATURE": f"{self.last_temperature:.1f}",
            "PRESSURE": "101.3",
            "VOLTAGE": "12.3",
            "GYRO_R": "0.0", "GYRO_P": "0.0", "GYRO_Y": "0.0",
            "ACCEL_R": "0.0", "ACCEL_P": "0.0", "ACCEL_Y": "0.0",
            "MAG_R": "0.0", "MAG_P": "0.0", "MAG_Y": "0.0",
            "AUTO_GYRO_ROTATION_RATE": "0",
            "GPS_TIME": datetime.utcnow().strftime("%H:%M:%S"),
            "GPS_ALTITUDE": "10.0",
            "GPS_LATITUDE": f"{self.last_latitude:.5f}",
            "GPS_LONGITUDE": f"{self.last_longitude:.5f}",
            "GPS_SATS": "7",
            "CMD_ECHO": "CXON"
        }

        if self.record_enabled and self.csv_writer:
            self.csv_writer.writerow([row.get(h, "") for h in self.csv_header])

        self.update_graphs.emit(row)
        self.data_available.emit(",".join([row.get(h, "") for h in self.csv_header]))
        time.sleep(1.0)  # 1 Hz

    # ---------------- Worker Thread ---------------- #
    class WorkerThread(QThread):
        def __init__(self, parent): super().__init__(parent); self.parent = parent
        def run(self):
            if self.parent.dummy_enabled:
                while self.parent.dummy_enabled:
                    self.parent.dummy_serial()
            else:
                while self.parent.is_connected:
                    if self.parent.ser.isOpen():
                        while self.parent.ser.isOpen():
                            try:
                                self.parent.read_serial()
                            except serial.SerialException:
                                self.is_unplugged = True
                                try: self.parent.ser.close()
                                except: pass
                    else:
                        self.parent.parent.update_status_bar("// !! Unplugged !!")
                        self.parent.data_available.emit(self.parent.message_unplugged)
                        while not self.parent.ser.is_open:
                            try:
                                self.parent.ser.open()
                                self.parent.data_available.emit(self.parent.message_replugged)
                                self.parent.parent.update_status_bar(
                                    f"// #CONNECTED -> {self.parent.ser.portstr} <- {self.parent.ser.baudrate}")
                                self.is_unplugged = False
                                break
                            except:
                                if self.parent.alarm:
                                    winsound.Beep(575, 400)

    def start_thread(self):
        self.all_data = open(f"./{self.logs_path}/BlackBox/flight_data.txt", 'w', encoding="utf-8")
        self.all_data.write(f"[LATEST FLIGHT]: [{datetime.now()}] [CONNECTION: {self.ser.__dict__}]\n")
        self.worker = self.WorkerThread(self)
        self.worker.start()

    def stop_thread(self):
        try: self.worker.terminate()
        except: pass
        try: self.all_data.close()
        except: pass
