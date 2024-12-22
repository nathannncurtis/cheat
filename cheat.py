import sys
import json
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QLineEdit
from PyQt6.QtGui import QFont, QColor, QPalette, QCursor
from PyQt6.QtCore import Qt
import os

if sys.platform == "darwin":
    from AppKit import NSEvent
elif sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

class BlurredBackground(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 150);")  # Semi-transparent background

        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)
        self.show()

class ShortcutOverlay(QWidget):
    def __init__(self, config_file):
        super().__init__()

        print(f"Detected platform: {sys.platform}")
        # Load configuration from JSON
        self.shortcuts = self.load_config(config_file)

        # Get the monitor with the cursor
        self.set_screen_geometry()

        # Set up the UI
        self.init_ui()

        # Force focus on Windows
        if sys.platform == "win32":
            self.force_focus_windows()

    def load_config(self, config_file):
        try:
            with open(config_file, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Config file '{config_file}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Config file '{config_file}' contains invalid JSON.")
            sys.exit(1)

    def set_screen_geometry(self):
        screens = QApplication.screens()
        cursor_position = QCursor.pos()

        for screen in screens:
            if screen.geometry().contains(cursor_position):
                screen_geometry = screen.geometry()
                self.screen_width = int(screen_geometry.width() * 0.9)
                self.screen_height = int(screen_geometry.height() * 0.9)
                self.screen_x = screen_geometry.x() + (screen_geometry.width() - self.screen_width) // 2
                self.screen_y = screen_geometry.y() + (screen_geometry.height() - self.screen_height) // 2
                return

        # Fallback to primary screen if no match is found
        print("No monitor found for cursor position, defaulting to primary screen.")
        primary_screen = QApplication.primaryScreen().geometry()
        self.screen_width = int(primary_screen.width() * 0.9)
        self.screen_height = int(primary_screen.height() * 0.9)
        self.screen_x = (primary_screen.width() - self.screen_width) // 2
        self.screen_y = (primary_screen.height() - self.screen_height) // 2

    def init_ui(self):
        self.setWindowTitle("Shortcut Overlay")
        self.setGeometry(self.screen_x, self.screen_y, self.screen_width, self.screen_height)

        # Set frameless window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

        # Add rounded corners and gradient background to simulate frosted glass
        self.setStyleSheet(
            """
            background-color: rgba(0, 0, 0, 180);
            border-radius: 25px;
            """
        )

        # Set layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search shortcuts...")
        self.search_bar.setFont(QFont("Roboto Thin", 12))
        self.search_bar.setStyleSheet("color: white; background-color: #333; border: 1px solid #555; border-radius: 10px; padding: 5px;")
        self.search_bar.textChanged.connect(self.filter_shortcuts)
        layout.addWidget(self.search_bar)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: white;")
        layout.addWidget(separator)

        # Shortcuts list
        self.shortcuts_layout = QVBoxLayout()
        self.populate_shortcuts()
        layout.addLayout(self.shortcuts_layout)

        layout.addStretch()
        self.setLayout(layout)

        # Take focus and ensure search bar is ready
        self.activateWindow()
        self.raise_()
        self.setFocus()
        self.search_bar.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def populate_shortcuts(self):
        for index, shortcut in enumerate(self.shortcuts.get("shortcuts", [])):
            shortcut_layout = QHBoxLayout()

            text_color = "white" if index % 2 == 0 else "#D3D3D3"  # Alternate text colors

            key_label = QLabel(shortcut['key'])
            key_label.setFont(QFont("Roboto Thin", 12, QFont.Weight.Normal))
            key_label.setStyleSheet(f"color: {text_color}; padding: 2px;")
            shortcut_layout.addWidget(key_label, alignment=Qt.AlignmentFlag.AlignLeft)

            description_label = QLabel(shortcut['description'])
            description_label.setFont(QFont("Roboto Thin", 12))
            description_label.setStyleSheet(f"color: {text_color}; padding: 2px;")
            shortcut_layout.addWidget(description_label, alignment=Qt.AlignmentFlag.AlignLeft)

            self.shortcuts_layout.addLayout(shortcut_layout)

    def filter_shortcuts(self, text):
        # Clear existing shortcuts from the layout
        while self.shortcuts_layout.count():
            child = self.shortcuts_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            if child.layout():
                self.clear_layout(child.layout())

        # Add only matching shortcuts to the layout
        for shortcut in self.shortcuts.get("shortcuts", []):
            if text.lower() in shortcut['key'].lower() or text.lower() in shortcut['description'].lower():
                shortcut_layout = QHBoxLayout()

                key_label = QLabel(shortcut['key'])
                key_label.setFont(QFont("Roboto Thin", 12, QFont.Weight.Normal))
                key_label.setStyleSheet("color: white; padding: 2px;")
                shortcut_layout.addWidget(key_label, alignment=Qt.AlignmentFlag.AlignLeft)

                description_label = QLabel(shortcut['description'])
                description_label.setFont(QFont("Roboto Thin", 12))
                description_label.setStyleSheet("color: white; padding: 2px;")
                shortcut_layout.addWidget(description_label, alignment=Qt.AlignmentFlag.AlignLeft)

                self.shortcuts_layout.addLayout(shortcut_layout)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    def force_focus_windows(self):
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            app_hwnd = self.winId().__int__()
            if hwnd != app_hwnd:
                ctypes.windll.user32.SetForegroundWindow(app_hwnd)
        except Exception as e:
            print(f"Failed to force focus on Windows: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            QApplication.quit()

if __name__ == "__main__":
    config_file = os.path.join(os.path.dirname(__file__), "shortcuts.json")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Apply Fusion theme

    # Create a blurred background
    background = BlurredBackground()

    # Create the main overlay
    overlay = ShortcutOverlay(config_file)
    overlay.show()

    sys.exit(app.exec())
