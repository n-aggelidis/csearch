import sys
import os

from PyQt6 import QtWidgets, QtCore, QtGui

def resource_path(relative_path):
    """ Returns absolute path to resource, compatible with PyInstaller. """
    if hasattr(sys, '_MEIPASS'):
        # Use temp folder if running as AppImage/PyInstaller
        return os.path.join(sys._MEIPASS, relative_path)
    # Otherwise use local folder
    base_path = os.path.dirname(os.path.abspath(__file__))
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
        text = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        if not text:
            super().paint(painter, option, index)
            return

        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        painter.save()

        doc = QtGui.QTextDocument()
        doc.setDefaultFont(options.font)
        doc.setDocumentMargin(0)
        doc.setHtml(text)

        # Draw background (e.g. selection) without plain text
        options.text = ""
        options.widget.style().drawControl(QtWidgets.QStyle.ControlElement.CE_ItemViewItem, options, painter)

        # Indent text area slightly
        painter.translate(options.rect.left() + 4, options.rect.top() + 4)
        clip = QtCore.QRectF(0, 0, options.rect.width() - 8, options.rect.height() - 8)

        # Change HTML text color to white when row is selected
        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()
        ctx.clip = clip
        if option.state & QtWidgets.QStyle.StateFlag.State_Selected:
            ctx.palette.setColor(QtGui.QPalette.ColorRole.Text, option.palette.color(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.HighlightedText))

        doc.documentLayout().draw(painter, ctx)
        painter.restore()