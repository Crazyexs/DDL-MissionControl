class ConnectionBuffer:
    def __init__(self, parent):
        self.parent = parent
        self.serial = parent.serial
        self.terminal = parent.terminal
        self.ui = parent.ui
        self.prefix = parent.config.get("application.settings.command_prefix") or "/"

    def send_data(self):
        text = self.ui.terminal_input.text().strip()
        if not text: return
        low = text.lower()
        # help
        if low == f"{self.prefix}help":
            self.terminal.write("(OK) Commands:")
            for cmd in ["/clear","/dummy.on","/dummy.off","/dummy.time <sec>",
                        "/cal","/cx.on","/cx.off","/st.gps","/st hh:mm:ss",
                        "/sim.enable","/sim.activate","/sim.disable",
                        "/simp <pressure_pa>","/mec.<device>.on","/mec.<device>.off"]:
                self.terminal.write(f" - {cmd}")
        elif low == f"{self.prefix}clear":
            self.terminal.clear()
        elif low == f"{self.prefix}dummy.on":
            self.serial.start_dummy()
        elif low == f"{self.prefix}dummy.off":
            self.serial.stop_dummy()
        elif low.startswith(f"{self.prefix}dummy.time"):
            try:
                sec = float(low.split()[-1]); self.serial.set_dummy_time(sec)
                self.terminal.write(f"(OK) Dummy time {sec}s")
            except: self.terminal.write("(!) Usage: /dummy.time <sec>")
        elif low == f"{self.prefix}cal":
            self.serial.cmd_cal()
        elif low == f"{self.prefix}cx.on":
            self.serial.cmd_cx(True)
        elif low == f"{self.prefix}cx.off":
            self.serial.cmd_cx(False)
        elif low == f"{self.prefix}st.gps":
            self.serial.cmd_st("GPS")
        elif low.startswith(f"{self.prefix}st "):
            self.serial.cmd_st(text[len(f"{self.prefix}st "):].strip())
        elif low == f"{self.prefix}sim.enable":
            self.serial.cmd_sim("ENABLE")
        elif low == f"{self.prefix}sim.activate":
            self.serial.cmd_sim("ACTIVATE")
        elif low == f"{self.prefix}sim.disable":
            self.serial.cmd_sim("DISABLE")
        elif low.startswith(f"{self.prefix}simp "):
            try: self.serial.cmd_simp(int(low.split()[-1]))
            except: self.terminal.write("(!) Usage: /simp <pressure_pa>")
        elif low.startswith(f"{self.prefix}mec."):
            try:
                tail = low.split("mec.",1)[1]
                device, action = tail.split(".")
                self.serial.cmd_mec(device.upper(), action=="on")
            except:
                self.terminal.write("(!) Usage: /mec.<device>.on|off")
        elif low == f"{self.prefix}sim.play":
            self.serial.sim_play()
        elif low == f"{self.prefix}sim.stop":
            self.serial.sim_stop()

        else:
            # raw send
            self.serial.send_data(text + ("\r\n" if not text.endswith("\n") else ""))
        self.ui.terminal_input.clear()

    def update_ports(self, override_message=False):
        self.serial.update_ports()
    def connect(self):
        if self.ui.btn_connect_serial.isChecked(): self.serial.connect()
        else: self.serial.disconnect()
    def toggle_recording(self):
        if self.ui.btn_togle_log.isChecked():
            self.serial.record_enabled=True
            self.terminal.write("(OK) Recording: ON (Flight_<TEAM_ID>.csv)")
            self.serial._open_csv_if_needed()
        else:
            self.serial.record_enabled=False
            try:
                if getattr(self.serial, "csv_file", None): self.serial.csv_file.flush()
            except: pass
            self.terminal.write("(OK) Recording: OFF")
