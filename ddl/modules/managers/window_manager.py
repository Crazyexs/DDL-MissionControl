# ddl/modules/managers/window_manager.py  (DROP-IN)
from PyQt5.QtWidgets import QWidget

class WindowManager:
    """
    Safe, UI-agnostic window controller.
    - Works even if the UI has no side menu frame (fr_menu).
    - Provides toggles for menu, fullscreen, maximize.
    """

    def __init__(self, parent):
        self.parent = parent
        self.ui = parent.ui
        self.clickPostion = None

        # Optional menu container (some UIs don't have it)
        # If your UI later adds a QWidget named 'fr_menu', this will pick it up.
        self.menu_frame: QWidget | None = getattr(self.ui, "fr_menu", None)

        # Optional menu toggle button label sync
        self.menu_button = getattr(self.ui, "btn_togle_menu", None)

    # --------- Menu handling (optional) ---------
    def togle_menu(self):
        """Toggle an optional side/menu frame if present; else no-op."""
        if self.menu_frame is None:
            # No menu frame in this UI; just ignore gracefully
            return

        is_visible = self.menu_frame.isVisible()
        self.menu_frame.setVisible(not is_visible)

        # If there is a toggle button, update its text to reflect state
        if self.menu_button is not None:
            try:
                self.menu_button.setText("≡" if not is_visible else "×")
            except Exception:
                pass

    # --------- Window state helpers ---------
    def show_full_screen(self):
        w = self.parent
        if w.isFullScreen():
            w.showNormal()
        else:
            w.showFullScreen()

    def maximize_app(self):
        self.parent.showMaximized()