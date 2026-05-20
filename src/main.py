__version__ = "0.1"

import sys
import os
import signal
from PyQt6 import QtWidgets, QtCore

from core import Localizer
from ui import GUI

# Set working directory for PyInstaller to access .ui files
if hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)

if __name__ == "__main__":
    # Allow immediate exit via Ctrl+C in the terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Initialize application
    app = QtWidgets.QApplication(sys.argv)
    app.setProperty("useNativeDialogs", True)

    # Make sure window manager can recognize flatpak
    if os.path.exists("/.flatpak-info"):
        app.setApplicationName("org.csearch.CSearch")
        app.setDesktopFileName("org.csearch.CSearch")

    # Detect system language and configure localization
    locale = QtCore.QLocale.system()
    #locale = QtCore.QLocale("de_DE")

    Localizer.set_language(locale.name())

    # Initialize and show main window
    window = GUI(locale=locale, version=__version__)
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())