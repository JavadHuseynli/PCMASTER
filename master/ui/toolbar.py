"""
ClassRoom Manager Master - Modern Toolbar.
Professional QPainter ikonları ilə.
"""

from PyQt6.QtWidgets import QToolBar, QWidget, QSizePolicy
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from . import icons


class MasterToolbar(QToolBar):
    """Master tətbiqinin modern toolbar-ı."""

    monitor_clicked = pyqtSignal()
    demo_fullscreen_clicked = pyqtSignal()
    demo_window_clicked = pyqtSignal()
    lock_clicked = pyqtSignal()
    unlock_clicked = pyqtSignal()
    message_clicked = pyqtSignal()
    file_send_clicked = pyqtSignal()
    file_collect_clicked = pyqtSignal()
    run_program_clicked = pyqtSignal()
    open_url_clicked = pyqtSignal()
    shutdown_clicked = pyqtSignal()
    restart_clicked = pyqtSignal()
    select_all_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    remote_control_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Əsas Alətlər", parent)
        self.setMovable(False)
        self.setIconSize(QSize(32, 32))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setStyleSheet("""
            QToolBar {
                background-color: #0d1117;
                border-bottom: 1px solid #21262d;
                padding: 6px 8px;
                spacing: 2px;
            }
            QToolButton {
                color: #c9d1d9;
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 6px 8px;
                font-size: 10px;
                min-width: 60px;
                font-family: 'Helvetica Neue', 'Segoe UI', sans-serif;
            }
            QToolButton:hover {
                background-color: #161b22;
                color: #f0f6fc;
            }
            QToolButton:pressed {
                background-color: #21262d;
            }
            QToolBar::separator {
                width: 1px;
                background-color: #21262d;
                margin: 8px 4px;
            }
        """)

        self._add_actions()

    def _add_actions(self):
        self._add(icons.icon_monitor(), "Monitorinq", self.monitor_clicked)
        self._add(icons.icon_remote_control(), "Müdaxilə", self.remote_control_clicked)
        self.addSeparator()

        self._add(icons.icon_demo_full(), "Demo (Tam)", self.demo_fullscreen_clicked)
        self._add(icons.icon_demo_window(), "Demo (Pəncərə)", self.demo_window_clicked)
        self.addSeparator()

        self._add(icons.icon_lock(), "Kilidlə", self.lock_clicked)
        self._add(icons.icon_unlock(), "Kilidi Aç", self.unlock_clicked)
        self.addSeparator()

        self._add(icons.icon_message(), "Mesaj", self.message_clicked)
        self.addSeparator()

        self._add(icons.icon_file_send(), "Fayl Göndər", self.file_send_clicked)
        self._add(icons.icon_file_collect(), "Fayl Topla", self.file_collect_clicked)
        self.addSeparator()

        self._add(icons.icon_run_program(), "Proqram Aç", self.run_program_clicked)
        self._add(icons.icon_open_url(), "URL Aç", self.open_url_clicked)
        self.addSeparator()

        self._add(icons.icon_shutdown(), "Söndür", self.shutdown_clicked)
        self._add(icons.icon_restart(), "Yenidən", self.restart_clicked)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        self._add(icons.icon_select_all(), "Hamısını Seç", self.select_all_clicked)
        self._add(icons.icon_settings(), "Parametrlər", self.settings_clicked)

    def _add(self, icon, label: str, signal):
        action = QAction(icon, label, self)
        action.setToolTip(label)
        action.triggered.connect(signal.emit)
        self.addAction(action)
