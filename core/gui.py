import os
import re
import subprocess
import html
import shlex
from .localizer import Localizer
from PyQt6 import QtWidgets, uic, QtCore, QtGui
from .helpers import resource_path, DateTableWidgetItem, RichTextDelegate
from .app_picker_dialog import AppPickerDialog
from .search_worker import SearchWorker

class GrepGuiApp(QtWidgets.QMainWindow):
    """ Main GUI Application Class """
    def __init__(self, locale):
        super().__init__()

        # Load UI from file
        uic.loadUi(resource_path("window.ui"), self)
        self.setWindowIcon(QtGui.QIcon(resource_path('../icon.svg')))

        # Replace default LineEdits with custom ones that select all text on click
        # for field in [self.Path, self.Search_item, self.Search_filename]:
        #     field.setLineEdit(SelectAllLineEdit())

        # Set system locale and translate UI
        self.locale = locale
        self.retranslate_ui()

        # Initialize settings for history storage
        self.settings = QtCore.QSettings("CSearch", "CSearch")
        
        # Load search history
        self._load_history(self.Path, "history_path", set_active=True)
        self._load_history(self.Search_filename, "history_filename", set_active=False)
        self._load_history(self.Search_item, "history_item", set_active=False)

        # Load checkbox settings
        self.CheckSubfolders.setChecked(self.settings.value("setting_subfolders", True, type=bool))
        self.CheckIgnoreCase.setChecked(self.settings.value("setting_ignore_case", True, type=bool))

        # Configure Results table
        self.Results.setSortingEnabled(True)
        self.Results.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        # Configure table headers
        h = self.Results.horizontalHeader()
        h.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.Results.setColumnWidth(0, 250)
        h.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        h.setHighlightSections(False)
        self.Results.verticalHeader().setHighlightSections(False)

        # Apply rich text delegate to the matches column
        self.Results.setItemDelegateForColumn(3, RichTextDelegate(self.Results))

        # Connect signals and slots
        self.Browse.clicked.connect(self.open_dir)
        self.Browse.setMinimumWidth(120)
        self.InfoExt.clicked.connect(self.show_button_info)
        self.InfoFileName.clicked.connect(self.show_button_info)
        self.InfoContent.clicked.connect(self.show_button_info)
        self.StartSearch.clicked.connect(self.toggle_search)
        for field in [self.Path, self.Search_item, self.Search_filename]:
            if field.lineEdit():
                field.lineEdit().returnPressed.connect(self.toggle_search)

        self.Results.itemDoubleClicked.connect(self.open_file)

        # Enable and connect custom context menu
        self.Results.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.Results.customContextMenuRequested.connect(self.show_context_menu)

        self.animation_timer = QtCore.QTimer()
        self.animation_timer.timeout.connect(self.animate_status)
        self.worker = None

    def retranslate_ui(self):
        """ Translates UI elements based on the current locale """
        self.setWindowTitle(Localizer.get("app_title"))

        self.labelPath.setText(Localizer.get("search_path"))
        self.Browse.setText(Localizer.get("browse"))

        self.labelExt.setText(Localizer.get("extensions"))
        self.Extensions.setPlaceholderText(Localizer.get("ext_placeholder"))
        self.InfoExt.setToolTip(Localizer.get("ext_tooltip"))

        self.labelFileName.setText(Localizer.get("search_filename"))
        self.Search_filename.lineEdit().setPlaceholderText(Localizer.get("filename_placeholder"))
        self.InfoFileName.setToolTip(Localizer.get("filename_tooltip"))

        self.labelContent.setText(Localizer.get("search_content"))
        self.Search_item.lineEdit().setPlaceholderText(Localizer.get("content_placeholder"))
        self.InfoContent.setToolTip(Localizer.get("content_tooltip"))

        self.CheckSubfolders.setText(Localizer.get("subfolders"))
        self.CheckIgnoreCase.setText(Localizer.get("ignore_case"))
        self.StartSearch.setText(Localizer.get("start_search"))

        # Translate table headers
        if self.Results.horizontalHeaderItem(0):
            self.Results.horizontalHeaderItem(0).setText(Localizer.get("header_name"))
            self.Results.horizontalHeaderItem(1).setText(Localizer.get("header_modified"))
            self.Results.horizontalHeaderItem(2).setText(Localizer.get("header_folder"))
            self.Results.horizontalHeaderItem(3).setText(Localizer.get("header_matches"))

    def show_context_menu(self, position):
        """ Displays context menu on right-click in the results table """
        selected_rows = self.Results.selectionModel().selectedRows()
        if not selected_rows:
            return

        # Collect hidden absolute paths from selected rows
        paths = [
            self.Results.item(index.row(), 0).data(QtCore.Qt.ItemDataRole.UserRole)
            for index in selected_rows if self.Results.item(index.row(), 0)
        ]
        paths = [p for p in paths if p]

        if not paths:
            return

        menu = QtWidgets.QMenu()

        # Build menu actions
        open_text = Localizer.get("open_files", len(paths)) if len(paths) > 1 else Localizer.get("open")
        action_open = menu.addAction(open_text)

        action_open_with = None
        if len(paths) == 1:
            action_open_with = menu.addAction(Localizer.get("open_with"))

        action_open_folder = menu.addAction(Localizer.get("open_folder")  if len(paths) == 1 else Localizer.get("open_folder_all"))

        menu.addSeparator()
        action_copy = menu.addAction(Localizer.get("copy_path") if len(paths) == 1 else Localizer.get("copy_paths"))

        # Show menu at cursor position
        action = menu.exec(self.Results.viewport().mapToGlobal(position))

        # Handle selected action
        if action == action_open:
            self._handle_multi_open(paths)
        elif action == action_open_with and action_open_with:
            self._handle_open_with(paths[0])
        elif action == action_open_folder:
            self._handle_open_folder(paths)
        elif action == action_copy:
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText("\n".join(paths))
            self.statusbar.showMessage(Localizer.get("paths_copied", len(paths)), 3000)

    def _handle_open_with(self, file_path):
        """ Opens a custom dialog to select an application to open the file """
        dialog = AppPickerDialog(self)

        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            cmd = dialog.get_selected_command()
            if cmd:
                # Remove placeholders from the desktop entry command
                clean_cmd = re.sub(r'%[fFuU]', '', cmd).strip()
                args = shlex.split(clean_cmd)
                args.append(file_path)

                try:
                    subprocess.Popen(args)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, Localizer.get("error"), Localizer.get("program_start_error", e))

    def _handle_open_folder(self, paths):
        """ Opens the containing folder(s) of the selected files """
        folders = set(os.path.dirname(p) for p in paths)
        for f in folders:
            if os.path.exists(f):
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(f))

    def _handle_multi_open(self, paths):
        """ Opens multiple files with a warning prompt if there are too many """
        if len(paths) > 5:
            reply = QtWidgets.QMessageBox.question(
                self, Localizer.get("warning"), Localizer.get("open_multiple_warning", len(paths)),
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if reply == QtWidgets.QMessageBox.StandardButton.No:
                return
        for p in paths:
            if os.path.exists(p):
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(p))

    def open_dir(self):
        """ Opens a directory selection dialog """
        start_dir = QtCore.QDir.homePath()
        path = QtWidgets.QFileDialog.getExistingDirectory(self, Localizer.get("select_folder"), start_dir)
        if path: self.Path.setCurrentText(path)

    def show_button_info(self):
        """ Displays the tooltip of the clicked info button """
        button = self.sender()
        if button:
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), button.toolTip(), button)

    def toggle_search(self):
        """ Starts or cancels the search process """
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            return

        search_path = self.Path.currentText()
        if not search_path or not os.path.exists(search_path):
            QtWidgets.QMessageBox.warning(self, Localizer.get("error"), Localizer.get("invalid_path"))
            return

        filename_text = self.Search_filename.currentText().strip()
        content_text = self.Search_item.currentText().strip()

        if not filename_text and not content_text:
            QtWidgets.QMessageBox.warning(self, Localizer.get("error"), Localizer.get("empty_search_terms"))
            return

        # Save to history
        self._save_history(self.Path, "history_path")
        self._save_history(self.Search_filename, "history_filename")
        self._save_history(self.Search_item, "history_item")

        # Save checkbox settings
        self.settings.setValue("setting_subfolders", self.CheckSubfolders.isChecked())
        self.settings.setValue("setting_ignore_case", self.CheckIgnoreCase.isChecked())

        # Parse search parameters
        raw_exts = self.Extensions.text().split(',') if self.Extensions.text() else []
        valid_exts = [
            f".{e.strip().lstrip('.').lower()}" 
            for e in raw_exts if e.strip() and e.strip() != '.'
        ]

        params = {
            'path': search_path,
            'extensions': valid_exts,
            'filename_terms': [t.strip().lower() for t in filename_text.split(',') if t.strip()],
            'content_terms': [t.strip() for t in content_text.split(',') if t.strip()],
            'subfolders': self.CheckSubfolders.isChecked(),
            'ignore_case': self.CheckIgnoreCase.isChecked()
        }

        # Prepare UI for search
        self.Results.setSortingEnabled(False)
        self.Results.setRowCount(0)
        self.StartSearch.setText(Localizer.get("cancel"))
        self.StartSearch.setStyleSheet("color: red;")
        self.animation_timer.start(500)

        # Start search worker
        self.worker = SearchWorker(params)
        self.worker.match_found_signal.connect(self.add_row)
        self.worker.finished_signal.connect(self.search_done)
        self.worker.start()

    def animate_status(self):
        """ Animates the status bar text during search """
        txt = self.statusbar.currentMessage().replace(".", "")
        dots = "." * ((len(self.statusbar.currentMessage()) - len(txt) + 1) % 4)
        self.statusbar.showMessage(Localizer.get("search_running") + dots)

    def search_done(self, success, elapsed, msg):
        """ Handles the end of the search process """
        self.animation_timer.stop()
        self.StartSearch.setText(Localizer.get("start_search"))
        self.StartSearch.setStyleSheet("")
        self.Results.setSortingEnabled(True)

        if success:
            elapsed_str = self.locale.toString(elapsed, 'f', 2)
            self.statusbar.showMessage(Localizer.get("search_completed",self.Results.rowCount(), elapsed_str))
        else:
            self.statusbar.showMessage(msg)

    def add_row(self, path, name, folder, date, match, tooltip, lno):
        """ Adds a new row with search results to the table """
        row = self.Results.rowCount()
        self.Results.insertRow(row)

        # Store hidden path and page number in UserRole data
        name_item = QtWidgets.QTableWidgetItem(name)
        name_item.setData(QtCore.Qt.ItemDataRole.UserRole, path)
        name_item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, lno)

        self.Results.setItem(row, 0, name_item)

        # Format modification date
        qdt = QtCore.QDateTime.fromSecsSinceEpoch(int(date))
        date_str = self.locale.toString(qdt, QtCore.QLocale.FormatType.ShortFormat)
        self.Results.setItem(row, 1, DateTableWidgetItem(date_str, date))

        self.Results.setItem(row, 2, QtWidgets.QTableWidgetItem(folder))

        # Escape HTML to prevent formatting issues
        safe_match = html.escape(match)

        # Highlight search terms in bold
        terms = [t.strip() for t in self.Search_item.currentText().split(',') if t.strip()]
        ignore_case = self.CheckIgnoreCase.isChecked()

        for term in terms:
            safe_term = html.escape(term)
            flags = re.IGNORECASE if ignore_case else 0
            pattern = re.compile(re.escape(safe_term), flags)
            safe_match = pattern.sub(r'<b>\g<0></b>', safe_match)

        match_item = QtWidgets.QTableWidgetItem(safe_match)

        # Build formatted tooltip
        if tooltip:
            lines = tooltip.split('\n')
            div_lines = []

            max_tooltip_lines = 25
            for line in lines[:max_tooltip_lines]:
                if len(line) > 200:
                    line = line[:200] + Localizer.get("line_truncated")

                safe_line = html.escape(line)
                div_lines.append(
                    f"<div style='margin-left: 80px; text-indent: -80px; white-space: pre-wrap; margin-bottom: 2px;'>"
                    f"{safe_line}"
                    f"</div>"
                )

            if len(lines) > max_tooltip_lines:
                div_lines.append(
                    f"<div style='margin-left: 80px; text-indent: -80px;'>"
                    f"{Localizer.get("lines_hidden")}"
                    f"</div>"
                )

            tt_html = (
                f"<div style='width: 600px; font-family: monospace;'>"
                f"{''.join(div_lines)}"
                f"</div>"
            )
            match_item.setToolTip(tt_html)

        self.Results.setItem(row, 3, match_item)

    def open_file(self, item):
        """ Opens the selected file on double click """
        if item.column() == 0:
            file_path = item.data(QtCore.Qt.ItemDataRole.UserRole)
            page_no = item.data(QtCore.Qt.ItemDataRole.UserRole + 1)

            if file_path and os.path.exists(file_path):
                url = QtCore.QUrl.fromLocalFile(file_path)

                # Append page fragment for PDFs
                if file_path.lower().endswith('.pdf') and page_no:
                    url.setFragment(f"page={page_no}")

                QtGui.QDesktopServices.openUrl(url)
            else:
                QtWidgets.QMessageBox.warning(self, Localizer.get("error"), Localizer.get("file_not_found"))

    def _load_history(self, combo_box, settings_key, set_active=True):
        """ Loads history into a combobox from QSettings """
        items = self.settings.value(settings_key, [])
        if isinstance(items, str):
            items = [items]
        else:
            items = [str(i) for i in items]
            
        combo_box.clear()
        if items:
            combo_box.addItems(items)
            if set_active:
                combo_box.setCurrentIndex(0)
            else:
                combo_box.setCurrentIndex(-1)
                combo_box.setCurrentText("")
        else:
            combo_box.setCurrentIndex(-1)
            combo_box.setCurrentText("")

    def _save_history(self, combo_box, settings_key):
        """ Saves the current text of a combobox to history """
        text = combo_box.currentText().strip()
        if not text:
            return
            
        items = [combo_box.itemText(i) for i in range(combo_box.count())]
        if text in items:
            items.remove(text)
            
        items.insert(0, text)
        items = items[:10]  # Keep the last 8 entries
        
        combo_box.clear()
        combo_box.addItems(items)
        combo_box.setCurrentText(text)
        
        self.settings.setValue(settings_key, items)
