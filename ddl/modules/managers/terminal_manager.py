# --- terminal_manager.py (PATCH) ---
# ... imports & class init as-is ...

def handle_command(self, raw_data):
        data = raw_data.strip()
        low = data.lower()

        if low == f"{self.command_prefix}help":
            self.write("<b style='color:#8cb854;'>(OK)</b> Available Commands:")
            self.ui.terminal.append(f"- <b>{self.command_prefix}clear</b>")
            self.ui.terminal.append(f"- <b>{self.command_prefix}reload</b>")
            self.ui.terminal.append(f"- <b>{self.command_prefix}saves</b>")
            self.ui.terminal.append(f"- <b>{self.command_prefix}dummy.on/off</b>")
            self.ui.terminal.append(f"- <b>{self.command_prefix}dummy.time [sec]</b>")
            self.ui.terminal.append(f"- <b>{self.command_prefix}cal</b>  (zero altitude)")
            self.ui.terminal.append(f"- <b>{self.command_prefix}cx.on / cx.off</b>")
            self.ui.terminal.append(f"- <b>{self.command_prefix}st.gps</b> or <b>{self.command_prefix}st hh:mm:ss</b>")
            self.ui.terminal.append(f"- <b>{self.command_prefix}sim.enable / sim.activate / sim.disable</b>")
            self.ui.terminal.append(f"- <b>{self.command_prefix}mec.&lt;device&gt;.on|off</b>")
            self.ui.terminal.append(f"- <b>{self.command_prefix}simp &lt;pressure_pa&gt;</b>")
            return

        # existing handlers...
        if low == f"{self.command_prefix}clear":
            self.clear(); return
        if low == f"{self.command_prefix}saves":
            self.parent.opn_logs(); return
        if low == f"{self.command_prefix}reload":
            self.parent.window_manager.reload_window(); return
        if low == f"{self.command_prefix}dummy.on":
            self.parent.serial.start_dummy(); return
        if low == f"{self.command_prefix}dummy.off":
            self.parent.serial.stop_dummy(); return

        if low.startswith(f"{self.command_prefix}dummy.time"):
            if self.parent.serial.dummy_enabled:
                try:
                    sec = float(low.split()[-1])
                    self.parent.serial.set_dummy_time(sec)
                except:
                    self.write("<b style='color:#a8002a;'>(!) INVALID time</b>")
            else:
                self.write("<b style='color:#a8002a;'>(!) Dummy is Disabled</b>")
            return

        # --- Mission commands ---
        if low == f"{self.command_prefix}cal":
            self.parent.serial.cmd_cal(); return
        if low == f"{self.command_prefix}cx.on":
            self.parent.serial.cmd_cx(True); return
        if low == f"{self.command_prefix}cx.off":
            self.parent.serial.cmd_cx(False); return
        if low == f"{self.command_prefix}st.gps":
            self.parent.serial.cmd_st("GPS"); return
        if low.startswith(f"{self.command_prefix}st "):
            t = data[len(f"{self.command_prefix}st "):].strip()
            self.parent.serial.cmd_st(t); return
        if low == f"{self.command_prefix}sim.enable":
            self.parent.serial.cmd_sim("ENABLE"); return
        if low == f"{self.command_prefix}sim.activate":
            self.parent.serial.cmd_sim("ACTIVATE"); return
        if low == f"{self.command_prefix}sim.disable":
            self.parent.serial.cmd_sim("DISABLE"); return
        if low.startswith(f"{self.command_prefix}mec."):
            try:
                _, tail = low.split("mec.", 1)
                device, action = tail.split(".")
                self.parent.serial.cmd_mec(device.upper(), action == "on")
            except:
                self.write("<b style='color:#a8002a;'>(!) MEC usage: /mec.<device>.on|off</b>")
            return
        if low.startswith(f"{self.command_prefix}simp "):
            try:
                pa = int(low.split()[-1])
                self.parent.serial.cmd_simp(pa)
            except:
                self.write("<b style='color:#a8002a;'>(!) SIMP usage: /simp <pressure_pa></b>")
            return

        self.write(f"<b style='color:#a8002a;'>(!) Unknown command '{data}' - try /help</b>")
