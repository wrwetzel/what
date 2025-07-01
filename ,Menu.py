# ------------------------------------------------------------------------
#   WRW 18-June-2025

#   Menu for Hearing-Test.py
# ------------------------------------------------------------------------

from PySide6.QtWidgets import (
    QMenuBar, QMenu, QAction, QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

class ParameterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test Parameters")
        layout = QFormLayout(self)

        self.start_freq = QLineEdit("20")
        self.end_freq = QLineEdit("20000")
        self.ppd = QLineEdit("16")

        layout.addRow("Start Frequency:", self.start_freq)
        layout.addRow("End Frequency:", self.end_freq)
        layout.addRow("Points per Decade:", self.ppd)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return (
            int(self.start_freq.text()),
            int(self.end_freq.text()),
            int(self.ppd.text())
        )

def setup_menus(self):
    menu_bar = self.menuBar()

    # File menu
    file_menu = menu_bar.addMenu("File")
    quit_action = QAction("Quit", self)
    quit_action.triggered.connect(QApplication.quit)
    file_menu.addAction(quit_action)

    # Parameters menu
    param_menu = menu_bar.addMenu("Parameters")
    param_action = QAction("Edit Parameters", self)
    param_action.triggered.connect(self.show_parameter_dialog)
    param_menu.addAction(param_action)

    # View menu
    view_menu = menu_bar.addMenu("View")
    self.show_points_action = QAction("Show Test Points", self, checkable=True)
    view_menu.addAction(self.show_points_action)

    # Help menu
    help_menu = menu_bar.addMenu("Help")

    about_action = QAction("About What", self)
    about_action.triggered.connect(self.about_what)
    help_menu.addAction(about_action)

    about_qt_action = QAction("About Qt", self)
    about_qt_action.triggered.connect(QApplication.instance().aboutQt)
    help_menu.addAction(about_qt_action)

    website_action = QAction("Website", self)
    website_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://your-site.example")))
    help_menu.addAction(website_action)

def show_parameter_dialog(self):
    dialog = ParameterDialog(self)
    if dialog.exec():
        start, end, ppd = dialog.values()
        print("Updated parameters:", start, end, ppd)  # Replace with your logic

def about_what(self):
    QMessageBox.information(self, "About What", "This is a hearing test application.\nDeveloped with PySide6.")

# ------------------------------------------------------------------------
