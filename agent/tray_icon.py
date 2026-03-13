"""
ClassRoom Manager Agent - System tray ikonu.
Agent-in arxa planda işləyərkən tray-da görünməsi və idarəsi.
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PyQt6.QtCore import QTimer, pyqtSignal, QObject

from classroom_manager.agent.autostart import install_autostart, remove_autostart, is_installed

logger = logging.getLogger(__name__)


class TraySignals(QObject):
    """Tray siqnalları."""
    quit_requested = pyqtSignal()
    toggle_visibility = pyqtSignal()


def create_default_icon() -> QIcon:
    """Default proqram ikonu yaradır (resurs faylı olmadıqda)."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Yaşıl dairə
    painter.setBrush(QColor(76, 175, 80))
    painter.setPen(QColor(56, 142, 60))
    painter.drawEllipse(4, 4, 56, 56)

    # "CM" yazısı
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Arial", 18, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), 0x0084, "CM")  # AlignCenter

    painter.end()
    return QIcon(pixmap)


class AgentTrayIcon:
    """System tray ikonu sinfi."""

    def __init__(self, app: QApplication = None):
        self.app = app or QApplication.instance()
        self.signals = TraySignals()

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(create_default_icon())
        self.tray.setToolTip("ClassRoom Manager Agent")

        self._setup_menu()
        self._status = "Qoşulmayıb"
        self._update_tooltip()

    def _setup_menu(self):
        """Sağ-klik menyusunu qurur."""
        menu = QMenu()

        self.status_action = QAction("Status: Qoşulmayıb")
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)

        menu.addSeparator()

        self.autostart_action = QAction("Avtomatik başlatma")
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(is_installed())
        self.autostart_action.triggered.connect(self._toggle_autostart)
        menu.addAction(self.autostart_action)

        menu.addSeparator()

        quit_action = QAction("Çıxış")
        quit_action.triggered.connect(self.signals.quit_requested.emit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)

    def show(self):
        """Tray ikonunu göstərir."""
        self.tray.show()
        logger.info("Tray ikonu göstərildi")

    def hide(self):
        """Tray ikonunu gizlədir."""
        self.tray.hide()

    def set_status(self, status: str):
        """Statusu yeniləyir."""
        self._status = status
        self.status_action.setText(f"Status: {status}")
        self._update_tooltip()

    def set_connected(self):
        """Qoşulmuş statusu."""
        self.set_status("Qoşulub ✓")
        self._set_icon_color(QColor(76, 175, 80))  # yaşıl

    def set_disconnected(self):
        """Əlaqə kəsilmiş statusu."""
        self.set_status("Qoşulmayıb")
        self._set_icon_color(QColor(244, 67, 54))  # qırmızı

    def show_message(self, title: str, message: str):
        """Bildiriş göstərir."""
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)

    def _update_tooltip(self):
        self.tray.setToolTip(f"ClassRoom Manager Agent\n{self._status}")

    def _toggle_autostart(self, checked: bool):
        """Avtomatik başlatma toggle."""
        if checked:
            success = install_autostart()
            if success:
                self.show_message("ClassRoom Manager", "Avtomatik başlatma aktivləşdirildi")
                logger.info("Autostart aktivləşdirildi")
            else:
                self.autostart_action.setChecked(False)
                self.show_message("ClassRoom Manager", "Avtomatik başlatma qurula bilmədi")
                logger.error("Autostart qurmaq alınmadı")
        else:
            success = remove_autostart()
            if success:
                self.show_message("ClassRoom Manager", "Avtomatik başlatma deaktivləşdirildi")
                logger.info("Autostart deaktivləşdirildi")
            else:
                self.autostart_action.setChecked(True)
                self.show_message("ClassRoom Manager", "Avtomatik başlatma silə bilmədi")
                logger.error("Autostart silmək alınmadı")

    def _set_icon_color(self, color: QColor):
        """İkon rəngini dəyişir."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(color)
        painter.setPen(color.darker(120))
        painter.drawEllipse(4, 4, 56, 56)

        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 18, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), 0x0084, "CM")

        painter.end()
        self.tray.setIcon(QIcon(pixmap))
