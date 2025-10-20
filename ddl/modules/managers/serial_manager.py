import os, csv, time
import serial, serial.tools.list_ports
from datetime import datetime
import numpy as np
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
    data_available = pyqtSignal(str)
    update_graphs = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent; self.ui = parent.ui; self.terminal = parent.terminal; self.config = parent.config
        self.is_connected = False; self.is_unplugged=False
        self.alarm = self.config.get("connection.alarm")
        self.ser = serial.Serial(); self.ser.timeout = self.config.get("connection.time_out")
        self.logs_path = self.config.get("application.settings.logs_folder"); os.makedirs(self.logs_path, exist_ok=True)
        os.makedirs(f"{self.logs_path}/BlackBox", exist_ok=True)
        self.sim_playing = False
        self.sim_thread = None
        self.record_enabled = True
        self.team_id = str(self.config.get("application.settings.team_id"))
        self.csv_header = list(self.config.get("telemetry.csv.header"))
        self.file_pattern = self.config.get("telemetry.csv.filename_pattern")
        self.csv_file_path = os.path.join(self.logs_path, self.file_pattern.replace("${TEAM_ID}", self.team_id))
        self.csv_file = None; self.csv_writer=None; self.csv_header_written=False
        self.dummy_enabled=False; self.dummy_update_time = self.config.get("graphs.default_update_time")
        self.baudratesDIC = self.config.get("connection.bauds_dic")
        self.filter_character = self.config.get("connection.filter_character")
        self.portList = []
        self.received_count=0; self.lost_count=0; self.last_packet_count=None
        self.sim_enabled=False; self.sim_activated=False
        self.last_latitude=42.842835; self.last_longitude=-2.668065; self.last_temperature=15.0; self.last_altitude=0.0

    def update_ports(self):
        try:
            self.portList = [p.device for p in serial.tools.list_ports.comports()]
            self.parent.terminal.write(f"(OK) [Available Ports]: {self.portList}")
            self.ui.cb_ports.clear(); self.ui.cb_ports.addItems(self.portList)
        except Exception as e:
            self.parent.terminal.write(f"[-] Error Updating Ports - {e}")

    def connect(self):
        try:
            self.ser.port = self.ui.cb_ports.currentText()
            baud_key = self.ui.cb_bauds.currentText()
            self.ser.baudrate = int(self.baudratesDIC.get(baud_key, 115200))
            self.ser.open(); self.is_connected=True
            self._open_csv_if_needed(); self.start_thread()
            self.parent.terminal.write("(OK) [CONNECTED]")
            self.ui.btn_connect_serial.setText("connected")
        except Exception as e:
            self.parent.terminal.write(f"[-] Error Connecting - {e}")
            try: self.ser.close()
            except: pass

    def disconnect(self):
        try:
            self.is_connected=False; self.stop_thread()
            self._close_csv_if_needed(); self.ser.close()
            self.ui.btn_connect_serial.setText("disconnected")
            self.parent.terminal.write("(OK) [DISCONNECTED]")
        except Exception as e:
            self.parent.terminal.write(f"[-] Error Disconnecting - {e}")

    def _open_csv_if_needed(self):
        if not self.record_enabled: return
        new_file = not os.path.exists(self.csv_file_path)
        self.csv_file = open(self.csv_file_path, "a", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.csv_file, delimiter=",")
        if new_file and self.config.get("telemetry.csv.include_header"):
            self.csv_writer.writerow(self.csv_header); self.csv_header_written=True

    def _close_csv_if_needed(self):
        if self.csv_file:
            try: self.csv_file.close()
            except: pass
        self.csv_file=None; self.csv_writer=None; self.csv_header_written=False

    # Commands
    def send_data(self, data):
        try:
            self.ser.write(bytes(data, "utf-8"))
            self.terminal.write(self.config.get("commands.sent", 2).replace("$CMD", data))
        except Exception as e:
            self.terminal.write(f"[-] Error Sending Data - {e}")

    def cmd_cx(self, on=True): self.send_data(f"CMD,{self.team_id},CX,{'ON' if on else 'OFF'}\r\n")
    def cmd_st(self, timestr="GPS"): self.send_data(f"CMD,{self.team_id},ST,{timestr}\r\n")
    def cmd_cal(self): self.send_data(f"CMD,{self.team_id},CAL\r\n")
    def cmd_sim(self, mode):
        self.send_data(f"CMD,{self.team_id},SIM,{mode}\r\n")
        if mode=="ENABLE": self.sim_enabled=True
        if mode=="ACTIVATE": self.sim_activated=True
        if mode=="DISABLE": self.sim_enabled=False; self.sim_activated=False
    def cmd_simp(self, pressure_pa:int):
        if not (self.sim_enabled and self.sim_activated):
            self.terminal.write(self.config.get("commands.guard_sim", 2)); return
        self.send_data(f"CMD,{self.team_id},SIMP,{int(pressure_pa)}\r\n")
    def cmd_mec(self, device:str, on=True): self.send_data(f"CMD,{self.team_id},MEC,{device},{'ON' if on else 'OFF'}\r\n")

    # Reader
    def read_serial(self):
        try:
            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
            if not line: return
            self.all_data.write(f"[{datetime.now()}]: {line}\n")
            if self.filter_character and line.startswith(self.filter_character):
                line = line.replace(self.filter_character, "", 1).strip()
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < len(REQUIRED_FIELDS):
                self.data_available.emit(line); return
            data = dict(zip(REQUIRED_FIELDS, parts[:len(REQUIRED_FIELDS)]))
            try:
                pkt = int(data["PACKET_COUNT"])
                if self.last_packet_count is None:
                    self.received_count = 1
                else:
                    step = pkt - self.last_packet_count
                    if step <= 0: self.received_count += 1
                    else:
                        self.lost_count += max(0, step-1); self.received_count += 1
                self.last_packet_count = pkt
            except: pass
            try:
                if hasattr(self.ui, "lb_recv"): self.ui.lb_recv.setText(f"recv: {self.received_count}")
                if hasattr(self.ui, "lb_lost"): self.ui.lb_lost.setText(f"lost: {self.lost_count}")
                if hasattr(self.ui, "lb_cmd_echo"): self.ui.lb_cmd_echo.setText(data.get("CMD_ECHO",""))
            except: pass
            if self.record_enabled and self.csv_writer:
                self.csv_writer.writerow([data.get(h,"") for h in self.csv_header])
            self.update_graphs.emit(data); self.data_available.emit(line)
        except Exception as e:
            try: self.all_data.write("[EXCEPTION]: " + str(e) + "\n")
            except: pass
            print("[EXCEPTION]:", e)

    # Dummy generator
    def dummy_serial(self):
        pkt = (self.last_packet_count or 0) + 1; self.last_packet_count = pkt; self.received_count += 1
        self.last_latitude += np.random.uniform(0.00001, 0.000001)
        self.last_longitude += np.random.uniform(0.00001, 0.000001)
        self.last_altitude += np.random.uniform(0, 1.0); self.last_temperature += np.random.uniform(-0.05, 0.05)
        row = {
            "TEAM_ID": self.team_id, "MISSION_TIME": datetime.utcnow().strftime("%H:%M:%S"),
            "PACKET_COUNT": str(pkt),"MODE":"F","STATE":"LAUNCH_PAD","ALTITUDE":f"{self.last_altitude:.1f}",
            "TEMPERATURE": f"{self.last_temperature:.1f}","PRESSURE":"101.3","VOLTAGE":"12.3",
            "GYRO_R":"0.0","GYRO_P":"0.0","GYRO_Y":"0.0","ACCEL_R":"0.0","ACCEL_P":"0.0","ACCEL_Y":"0.0",
            "MAG_R":"0.0","MAG_P":"0.0","MAG_Y":"0.0","AUTO_GYRO_ROTATION_RATE":"0",
            "GPS_TIME": datetime.utcnow().strftime("%H:%M:%S"), "GPS_ALTITUDE":"10.0",
            "GPS_LATITUDE": f"{self.last_latitude:.5f}", "GPS_LONGITUDE": f"{self.last_longitude:.5f}",
            "GPS_SATS":"7","CMD_ECHO":"CXON"
        }
        if self.record_enabled and self.csv_writer:
            self.csv_writer.writerow([row.get(h,"") for h in self.csv_header])
        self.update_graphs.emit(row)
        self.data_available.emit(",".join([row.get(h,"") for h in self.csv_header]))
        time.sleep(1.0)

    class WorkerThread(QThread):
        def __init__(self, parent): super().__init__(parent); self.parent = parent
        def run(self):
            if self.parent.dummy_enabled:
                while self.parent.dummy_enabled: self.parent.dummy_serial()
            else:
                self.parent.is_connected=True
                while self.parent.is_connected:
                    if self.parent.ser.isOpen():
                        while self.parent.ser.isOpen():
                            self.parent.read_serial()

    def start_thread(self):
        self.all_data = open(f"./{self.logs_path}/BlackBox/flight_data.txt", 'w', encoding="utf-8")
        self.worker = self.WorkerThread(self); self.worker.start()

    def stop_thread(self):
        try: self.is_connected=False; self.worker.terminate()
        except: pass
        try: self.all_data.close()
        except: pass

    # API for ConnectionBuffer
    def start_dummy(self): self.dummy_enabled=True; self._open_csv_if_needed(); self.start_thread()
    def stop_dummy(self): self.dummy_enabled=False; self.stop_thread()
    def set_dummy_time(self, sec: float): self.dummy_update_time = float(sec)

    def clear_runtime(self):
        """Reset runtime counters and close/reopen CSV if recording."""
        self.received_count = 0
        self.lost_count = 0
        self.last_packet_count = None
        # reset blackbox file too
        try:
            if getattr(self, "all_data", None):
                self.all_data.close()
        except:
            pass
        self.all_data = open(f"./{self.logs_path}/BlackBox/flight_data.txt", 'w', encoding="utf-8")
        # keep the CSV file, but write a separator for clarity
        if self.record_enabled and self.csv_writer:
            try:
                self.csv_writer.writerow(["# --- CLEAR ALL ---"])
            except:
                pass
    def sim_play(self):
        if self.sim_playing:
            self.terminal.write("(!) SIM already playing.")
            return
        if not (self.sim_enabled and self.sim_activated):
            self.terminal.write("(!) Enable+Activate SIM first: /sim.enable then /sim.activate")
            return
        self.sim_playing = True
        self.sim_thread = self.SimProfileThread(self)
        self.sim_thread.start()

    def sim_stop(self):
        if self.sim_thread and self.sim_playing:
            self.sim_thread.stop()
        self.sim_playing = False
        
    def clear_runtime(self):
        self.received_count = 0
        self.lost_count = 0
        self.last_packet_count = None
        try:
            if getattr(self, "all_data", None):
                self.all_data.close()
        except:
            pass
        self.all_data = open(f"./{self.logs_path}/BlackBox/flight_data.txt", 'w', encoding="utf-8")
        if self.record_enabled and self.csv_writer:
            try: self.csv_writer.writerow(["# --- CLEAR ALL ---"])
            except: pass
