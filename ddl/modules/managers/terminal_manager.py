# ddl/modules/managers/terminal_manager.py
class TerminalManager:
    """
    Minimal terminal adapter:
    - ui.terminal is a QTextBrowser
    - provides write(), clear(), boot_up_message()
    """
    def __init__(self, parent):
        self.parent = parent
        self.ui = parent.ui
        # prefix from config if needed
        self.prefix = parent.config.get("application.settings.command_prefix") or "/"

    def write(self, msg: str):
        # Accept both plain text and preformatted HTML
        try:
            if hasattr(self.ui, "terminal"):
                self.ui.terminal.append(str(msg))
        except Exception:
            pass

    def clear(self):
        try:
            if hasattr(self.ui, "terminal"):
                self.ui.terminal.clear()
        except Exception:
            pass

    def boot_up_message(self):
        self.write("(OK) Ground Station ready. Type /help")
