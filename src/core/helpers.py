import sys
import os
import inspect

import re
import html
from PyQt6 import QtWidgets, QtCore, QtGui
from .localizer import Localizer

def resource_path(relative_path):
    """ Returns absolute path to resource, compatible with PyInstaller. """
    if hasattr(sys, '_MEIPASS'):
        # Use temp folder if running as AppImage/PyInstaller
        # PyInstaller flattens paths to root, so we extract only the filename
        return os.path.join(sys._MEIPASS, os.path.basename(relative_path))
    # Otherwise use local folder of the calling script
    caller_filename = inspect.stack()[1].filename
    base_path = os.path.dirname(os.path.abspath(caller_filename))
    return os.path.join(base_path, relative_path)

class SelectAllLineEdit(QtWidgets.QLineEdit):
    """ Custom QLineEdit that selects all text when focused. """
    def focusInEvent(self, event):
        super().focusInEvent(event)
        QtCore.QTimer.singleShot(0, self.selectAll)

class DateTableWidgetItem(QtWidgets.QTableWidgetItem):
    """ Custom table item for sorting by timestamp instead of string. """
    def __init__(self, text, timestamp):
        super().__init__(text)
        self.timestamp = timestamp

    def __lt__(self, other):
        # Sort items by numerical timestamp
        if isinstance(other, DateTableWidgetItem):
            return self.timestamp < other.timestamp
        return super().__lt__(other)

class RichTextDelegate(QtWidgets.QStyledItemDelegate):
    """ Delegate to render HTML (e.g. bold text) in table cells. """
    def paint(self, painter, option, index):
        # 1. Let the base class draw the background, focus rectangle, etc.
        # This is the most robust way to handle selection styles correctly.
        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        
        painter.save()

        # The text contains HTML, so we clear it from the options to prevent
        # the base class from drawing the raw HTML string.
        text = options.text
        options.text = ""
        style = options.widget.style()
        style.drawControl(QtWidgets.QStyle.ControlElement.CE_ItemViewItem, options, painter)

        if not text:
            painter.restore()
            return

        # 2. Prepare fonts and colors
        normal_font = options.font
        bold_font = QtGui.QFont(normal_font)
        bold_font.setBold(True)

        # 3. Prepare the drawing rectangle with padding
        text_rect = style.subElementRect(QtWidgets.QStyle.SubElement.SE_ItemViewItemText, options)

        # 4. Parse the simple HTML and draw segment by segment
        parts = re.split(r'(<b>.*?</b>)', text)
        x = text_rect.left()
        elide_mode = QtCore.Qt.TextElideMode.ElideRight

        for part in parts:
            if not part:
                continue
            
            is_bold = part.startswith('<b>') and part.endswith('</b>')
            
            segment_text = html.unescape(part[3:-4] if is_bold else part)
            current_font = bold_font if is_bold else normal_font
            
            painter.setFont(current_font)
            font_metrics = QtGui.QFontMetrics(current_font)

            remaining_width = options.rect.right() - x
            elided_text = font_metrics.elidedText(segment_text, elide_mode, remaining_width)

            painter.drawText(x, text_rect.top(), remaining_width, text_rect.height(), 
                             QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.TextFlag.TextSingleLine, 
                             elided_text)
            
            x += font_metrics.horizontalAdvance(elided_text)

            if elided_text != segment_text:
                break

        painter.restore()

class AppPickerDialog(QtWidgets.QDialog):
    """ Custom dialog to select installed applications """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(Localizer.get("open_with"))
        self.resize(400, 500)

        layout = QtWidgets.QVBoxLayout(self)

        # Search field for filtering applications
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText(Localizer.get("search_app"))
        self.search_box.textChanged.connect(self.filter_apps)
        layout.addWidget(self.search_box)

        # List of applications
        self.app_list = QtWidgets.QListWidget()
        self.app_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.app_list)

        # Dialog buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.apps = {}  # Store App Name -> Executable Command
        self.load_desktop_files()

    def load_desktop_files(self):
        """ Scans Linux system directories for installed GUI applications """
        if os.path.exists("/.flatpak-info"):
            # Im Flatpak ist das Host-Dateisystem unter /run/host gemountet.
            # Wir scannen hier auch die Ordner für Flatpak- und Snap-Apps auf dem Host!
            xdg_dirs = [
                "/run/host/usr/share",
                "/run/host/usr/local/share",
                "/run/host/var/lib/flatpak/exports/share",
                #"/run/host/var/lib/snapd/desktop"
            ]
        else:
            # NixOS and other Linux distributions use XDG_DATA_DIRS to store app paths
            xdg_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/share").split(":")
            xdg_dirs.append("/var/lib/flatpak/exports/share")
            #xdg_dirs.append("/var/lib/snapd/desktop")

        # User-spezifische App-Ordner (für Flatpak und Non-Flatpak gleich)
        xdg_dirs.append(os.path.expanduser("~/.local/share/flatpak/exports/share"))
        xdg_dirs.append(os.path.expanduser("~/.local/share"))

        for d in xdg_dirs:
            app_dir = os.path.join(d, "applications")
            if not os.path.isdir(app_dir):
                continue

            for root, _, files in os.walk(app_dir):
                for file in files:
                    if file.endswith(".desktop"):
                        self.parse_desktop_file(os.path.join(root, file))

        # Sort alphabetically and populate list
        for name in sorted(self.apps.keys(), key=str.lower):
            self.app_list.addItem(name)

    def parse_desktop_file(self, filepath):
        """ Extracts name and execution command from a .desktop file """
        try:
            name, exec_cmd, no_display = None, None, False
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                in_main_section = False
                for line in f:
                    line = line.strip()
                    if line == "[Desktop Entry]":
                        in_main_section = True
                    elif line.startswith("["):
                        in_main_section = False

                    if in_main_section:
                        # Prioritize localized names, fallback to default
                        if line.startswith("Name[de]="):
                            name = line.split("=", 1)[1]
                        elif line.startswith("Name=") and not name:
                            name = line.split("=", 1)[1]
                        elif line.startswith("Exec=") and not exec_cmd:
                            exec_cmd = line.split("=", 1)[1]
                        elif line.startswith("NoDisplay=true"):
                            no_display = True
                        elif line.startswith("Terminal=true"):
                            # Verstecke reine Terminal-Programme, da wir kein Terminal mitstarten
                            no_display = True

            # Include only visible applications with valid commands
            if name and exec_cmd and not no_display:
                self.apps[name] = exec_cmd
        except Exception:
            pass

    def filter_apps(self, text):
        """ Filters the application list based on search text """
        search_text = text.lower()
        for i in range(self.app_list.count()):
            item = self.app_list.item(i)
            item.setHidden(search_text not in item.text().lower())

    def get_selected_command(self):
        """ Returns the execution command of the selected application """
        item = self.app_list.currentItem()
        if item:
            return self.apps.get(item.text())
        return None