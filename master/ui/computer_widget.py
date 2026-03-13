"""
ClassRoom Manager Master - Kompüter Widget.
Hər agent üçün modern kart — sağ klik menyusu ilə ad dəyişmə, otaq təyinatı.
"""

from __future__ import annotations

import base64
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QMenu, QInputDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QPixmap, QColor, QMouseEvent, QAction,
)


class ComputerWidget(QFrame):
    """Bir kompüteri təmsil edən modern kart widget."""

    clicked = pyqtSignal(str)
    double_clicked = pyqtSignal(str)
    selected_changed = pyqtSignal(str, bool)
    rename_requested = pyqtSignal(str, str)  # agent_id, new_name
    assign_room_requested = pyqtSignal(str)  # agent_id
    remote_control_requested = pyqtSignal(str)  # agent_id

    def __init__(self, agent_id: str, hostname: str, parent=None):
        super().__init__(parent)
        self.agent_id = agent_id
        self.hostname = hostname
        self.display_name = hostname
        self._selected = False
        self._online = True

        self.setFixedSize(300, 220)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style(selected=False)

        # Kölgə effekti
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Thumbnail container
        self.thumbnail_container = QWidget()
        self.thumbnail_container.setFixedHeight(170)
        self.thumbnail_container.setStyleSheet(
            "background-color: #0d1117; border-radius: 12px 12px 0 0;"
        )
        thumb_layout = QVBoxLayout(self.thumbnail_container)
        thumb_layout.setContentsMargins(4, 4, 4, 0)
        thumb_layout.setSpacing(0)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(292, 164)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            background-color: #161b22;
            border-radius: 10px;
            color: #484f58;
            font-size: 12px;
        """)
        self.thumbnail_label.setText("Gözlənilir...")
        thumb_layout.addWidget(self.thumbnail_label)

        layout.addWidget(self.thumbnail_container)

        # Alt info paneli
        info_panel = QWidget()
        info_panel.setFixedHeight(50)
        info_panel.setStyleSheet(
            "background-color: #161b22; border-radius: 0 0 12px 12px;"
        )
        info_layout = QHBoxLayout(info_panel)
        info_layout.setContentsMargins(12, 4, 12, 8)
        info_layout.setSpacing(8)

        # Status indikatoru
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(10, 10)
        self._set_status_dot(True)
        info_layout.addWidget(self.status_dot)

        # Ad və status
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.name_label = QLabel(hostname)
        self.name_label.setStyleSheet("""
            color: #e6edf3;
            font-size: 12px;
            font-weight: 600;
            font-family: 'Helvetica Neue', 'Segoe UI', sans-serif;
        """)
        text_layout.addWidget(self.name_label)

        self.status_label = QLabel("Online")
        self.status_label.setStyleSheet("""
            color: #3fb950;
            font-size: 10px;
            font-family: 'Helvetica Neue', 'Segoe UI', sans-serif;
        """)
        text_layout.addWidget(self.status_label)

        info_layout.addLayout(text_layout)
        info_layout.addStretch()

        # Otaq etiketi
        self.room_label = QLabel("")
        self.room_label.setStyleSheet("""
            color: #8b949e;
            font-size: 9px;
            background-color: #21262d;
            border-radius: 4px;
            padding: 2px 6px;
        """)
        self.room_label.hide()
        info_layout.addWidget(self.room_label)

        layout.addWidget(info_panel)

    def set_display_name(self, name: str):
        """Göstərilən adı dəyişir."""
        self.display_name = name
        self.name_label.setText(name)

    def set_room(self, room_name: str | None):
        """Otaq etiketini göstərir/gizlədir."""
        if room_name:
            self.room_label.setText(room_name)
            self.room_label.show()
        else:
            self.room_label.hide()

    def _set_status_dot(self, online: bool):
        color = "#3fb950" if online else "#f85149"
        self.status_dot.setStyleSheet(f"""
            background-color: {color};
            border-radius: 5px;
            min-width: 10px; max-width: 10px;
            min-height: 10px; max-height: 10px;
        """)

    def update_screenshot(self, base64_data: str):
        try:
            img_data = base64.b64decode(base64_data)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            scaled = pixmap.scaled(
                292, 164,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.thumbnail_label.setPixmap(scaled)
        except Exception:
            pass

    def set_online(self):
        self._online = True
        self._set_status_dot(True)
        self.status_label.setText("Online")
        self.status_label.setStyleSheet("color: #3fb950; font-size: 10px;")

    def set_offline(self):
        self._online = False
        self._set_status_dot(False)
        self.status_label.setText("Offline")
        self.status_label.setStyleSheet("color: #f85149; font-size: 10px;")
        self.thumbnail_label.setText("Offline")
        self.thumbnail_label.setPixmap(QPixmap())

    @property
    def is_selected(self) -> bool:
        return self._selected

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style(selected)
        self.selected_changed.emit(self.agent_id, selected)

    def toggle_selected(self):
        self.set_selected(not self._selected)

    def _apply_style(self, selected: bool):
        if selected:
            self.setStyleSheet("""
                ComputerWidget {
                    background-color: #161b22;
                    border: 2px solid #58a6ff;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                ComputerWidget {
                    background-color: #161b22;
                    border: 1px solid #30363d;
                    border-radius: 12px;
                }
                ComputerWidget:hover {
                    border: 1px solid #58a6ff;
                }
            """)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.toggle_selected()
            else:
                self.clicked.emit(self.agent_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.agent_id)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        """Sağ klik menyusu."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 4px;
                color: #c9d1d9;
                font-size: 12px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #21262d;
            }
            QMenu::separator {
                height: 1px;
                background-color: #30363d;
                margin: 4px 8px;
            }
        """)

        # Uzaqdan müdaxilə
        remote_action = menu.addAction("Uzaqdan Müdaxilə")
        remote_action.triggered.connect(
            lambda: self.remote_control_requested.emit(self.agent_id)
        )

        menu.addSeparator()

        # Ad dəyiş
        rename_action = menu.addAction("Adını Dəyiş...")
        rename_action.triggered.connect(self._on_rename)

        # Otağa təyin et
        assign_action = menu.addAction("Otağa Təyin Et...")
        assign_action.triggered.connect(
            lambda: self.assign_room_requested.emit(self.agent_id)
        )

        menu.exec(event.globalPos())

    def _on_rename(self):
        text, ok = QInputDialog.getText(
            self, "Adını Dəyiş",
            "Yeni ad:",
            text=self.display_name,
        )
        if ok and text.strip():
            self.rename_requested.emit(self.agent_id, text.strip())
