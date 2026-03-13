"""
ClassRoom Manager Master - Əsas pəncərə.
Otaq idarəetməsi, uzaqdan müdaxilə, modern dark tema.
"""
from __future__ import annotations

import base64
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QStatusBar, QLabel, QListWidget, QListWidgetItem, QSplitter,
    QMessageBox, QApplication, QLayout, QSizePolicy,
    QGraphicsDropShadowEffect, QPushButton, QInputDialog, QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, QRect, QPoint
from PyQt6.QtGui import QPixmap, QColor, QFont, QMouseEvent, QKeyEvent

from .toolbar import MasterToolbar
from .computer_widget import ComputerWidget
from .dialogs import (
    SendMessageDialog, SendFileDialog, RunProgramDialog,
    OpenUrlDialog, SettingsDialog,
)
from ..room_manager import (
    load_rooms, save_rooms, add_room, remove_room, rename_room,
    assign_computer, get_room_for, get_alias, set_alias, get_all_aliases,
)

logger = logging.getLogger(__name__)


class FlowLayout(QLayout):
    """Widget-ləri sətir-sətir düzən layout (responsive grid)."""

    def __init__(self, parent=None, margin=12, h_spacing=12, v_spacing=12):
        super().__init__(parent)
        self._h_space = h_spacing
        self._v_space = v_spacing
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        effective = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            w = item.sizeHint()
            next_x = x + w.width() + self._h_space
            if next_x - self._h_space > effective.right() and line_height > 0:
                x = effective.x()
                y += line_height + self._v_space
                next_x = x + w.width() + self._h_space
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), w))
            x = next_x
            line_height = max(line_height, w.height())

        return y + line_height - rect.y() + m.bottom()


class RemoteControlViewer(QWidget):
    """Uzaqdan müdaxilə pəncərəsi — ekranı görüb mouse/klaviatura ilə idarə etmək."""

    mouse_event_signal = pyqtSignal(str, dict)  # agent_id, event_data
    key_event_signal = pyqtSignal(str, dict)    # agent_id, event_data

    def __init__(self, agent_id: str, hostname: str, parent=None):
        super().__init__(parent)
        self.agent_id = agent_id
        self.setWindowTitle(f"Müdaxilə — {hostname}")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("background-color: #010409;")
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._screen_size = (1920, 1080)  # Varsayılan, screenshot-dan yenilənəcək

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Başlıq paneli
        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet("background-color: #161b22; border-bottom: 1px solid #21262d;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)

        status_dot = QLabel()
        status_dot.setFixedSize(8, 8)
        status_dot.setStyleSheet("""
            background-color: #3fb950; border-radius: 4px;
            min-width: 8px; max-width: 8px;
            min-height: 8px; max-height: 8px;
        """)
        header_layout.addWidget(status_dot)

        title = QLabel(f"  {hostname}  —  Uzaqdan müdaxilə aktiv")
        title.setStyleSheet("color: #c9d1d9; font-size: 12px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.info_label = QLabel("Gözlənilir...")
        self.info_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        header_layout.addWidget(self.info_label)

        layout.addWidget(header)

        # Ekran görüntüsü
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #010409;")
        self.image_label.setMouseTracking(True)
        layout.addWidget(self.image_label)

    def update_image(self, base64_data: str):
        try:
            img_data = base64.b64decode(base64_data)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            self._screen_size = (pixmap.width(), pixmap.height())
            scaled = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
            self.info_label.setText(f"{pixmap.width()}x{pixmap.height()}")
        except Exception:
            pass

    def _map_to_screen(self, pos):
        """Widget koordinatlarını ekran koordinatlarına çevirir."""
        label = self.image_label
        pixmap = label.pixmap()
        if not pixmap or pixmap.isNull():
            return None

        # Pixmap-ın label içindəki mövqeyini tap
        lw, lh = label.width(), label.height()
        pw, ph = pixmap.width(), pixmap.height()
        offset_x = (lw - pw) / 2
        offset_y = (lh - ph) / 2

        # Label-ə nisbətən pozisiya
        rel_x = pos.x() - label.x() - offset_x
        rel_y = pos.y() - label.y() - offset_y - 36  # header height

        if rel_x < 0 or rel_y < 0 or rel_x > pw or rel_y > ph:
            return None

        # Ekran koordinatlarına çevir
        screen_x = rel_x / pw * self._screen_size[0]
        screen_y = rel_y / ph * self._screen_size[1]
        return (int(screen_x), int(screen_y))

    def mousePressEvent(self, event: QMouseEvent):
        coords = self._map_to_screen(event.pos())
        if coords:
            self.mouse_event_signal.emit(self.agent_id, {
                "action": "click",
                "x": coords[0],
                "y": coords[1],
                "button": "left" if event.button() == Qt.MouseButton.LeftButton else "right",
            })

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        coords = self._map_to_screen(event.pos())
        if coords:
            self.mouse_event_signal.emit(self.agent_id, {
                "action": "double_click",
                "x": coords[0],
                "y": coords[1],
                "button": "left",
            })

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        self.key_event_signal.emit(self.agent_id, {
            "action": "press",
            "key": event.text(),
            "key_code": event.key(),
            "modifiers": int(event.modifiers()),
        })

    def keyReleaseEvent(self, event: QKeyEvent):
        self.key_event_signal.emit(self.agent_id, {
            "action": "release",
            "key": event.text(),
            "key_code": event.key(),
        })


class FullScreenViewer(QWidget):
    """Sadə tam ekran baxış pəncərəsi (müdaxiləsiz)."""

    def __init__(self, hostname: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"ClassRoom Manager — {hostname}")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: #010409;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #010409;")
        layout.addWidget(self.image_label)

    def update_image(self, base64_data: str):
        try:
            img_data = base64.b64decode(base64_data)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            scaled = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
        except Exception:
            pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()


class MainWindow(QMainWindow):
    """Master tətbiqinin əsas pəncərəsi."""

    # Server siqnalları
    agent_connected_signal = pyqtSignal(dict)
    agent_disconnected_signal = pyqtSignal(str)
    screenshot_received_signal = pyqtSignal(str, str)

    # Əmr siqnalları
    send_lock_signal = pyqtSignal(list)
    send_unlock_signal = pyqtSignal(list)
    send_message_signal = pyqtSignal(list, dict)
    send_file_signal = pyqtSignal(list, str)
    collect_file_signal = pyqtSignal(list)
    send_demo_start_signal = pyqtSignal(list, bool)
    send_demo_stop_signal = pyqtSignal(list)
    send_shutdown_signal = pyqtSignal(list, int)
    send_restart_signal = pyqtSignal(list, int)
    send_run_program_signal = pyqtSignal(list, str, list)
    send_open_url_signal = pyqtSignal(list, str)
    send_remote_mouse_signal = pyqtSignal(str, dict)
    send_remote_key_signal = pyqtSignal(str, dict)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.computer_widgets: dict[str, ComputerWidget] = {}
        self.viewer_windows: dict[str, FullScreenViewer] = {}
        self.remote_windows: dict[str, RemoteControlViewer] = {}
        self._agent_info: dict[str, dict] = {}
        self._current_room_filter: str | None = None  # None = hamısı

        self.setWindowTitle("ClassRoom Manager")
        self.setMinimumSize(1200, 700)
        self._apply_dark_theme()
        self._setup_ui()
        self._connect_signals()
        self._load_rooms()

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #010409;
            }
            QWidget {
                color: #c9d1d9;
                font-family: 'Helvetica Neue', 'Segoe UI', sans-serif;
            }
            QScrollArea {
                border: none;
                background-color: #010409;
            }
            QStatusBar {
                background-color: #0d1117;
                border-top: 1px solid #21262d;
                color: #8b949e;
                font-size: 12px;
                padding: 4px 12px;
            }
            QSplitter::handle {
                background-color: #21262d;
                width: 1px;
            }
            QScrollBar:vertical {
                background-color: #010409;
                width: 8px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #30363d;
                border-radius: 4px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #484f58;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

    def _setup_ui(self):
        # Toolbar
        self.toolbar = MasterToolbar(self)
        self.addToolBar(self.toolbar)

        # Mərkəz widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ═══ Sol panel — Otaqlar ═══
        left_panel = QWidget()
        left_panel.setFixedWidth(220)
        left_panel.setStyleSheet("background-color: #0d1117;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        # Otaqlar başlığı
        header_layout = QHBoxLayout()
        panel_title = QLabel("OTAQLAR")
        panel_title.setStyleSheet("""
            color: #8b949e; font-size: 11px; font-weight: 700;
            letter-spacing: 1px;
        """)
        header_layout.addWidget(panel_title)
        header_layout.addStretch()

        add_btn = QPushButton("+")
        add_btn.setFixedSize(24, 24)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2ea043; }
        """)
        add_btn.setToolTip("Yeni otaq əlavə et")
        add_btn.clicked.connect(self._on_add_room)
        header_layout.addWidget(add_btn)

        left_layout.addLayout(header_layout)

        # Otaq siyahısı
        self.room_list = QListWidget()
        self.room_list.setStyleSheet("""
            QListWidget {
                background-color: #0d1117;
                border: none;
                outline: none;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 6px;
                margin: 1px 0;
                color: #c9d1d9;
            }
            QListWidget::item:selected {
                background-color: #161b22;
                color: #58a6ff;
            }
            QListWidget::item:hover {
                background-color: #161b22;
            }
        """)
        self.room_list.currentItemChanged.connect(self._on_room_selected)
        self.room_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.room_list.customContextMenuRequested.connect(self._on_room_context_menu)
        left_layout.addWidget(self.room_list)

        splitter.addWidget(left_panel)

        # ═══ Mərkəz — Kompüter grid ═══
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: #010409;")
        self.flow_layout = FlowLayout(self.grid_container, margin=16, h_spacing=16, v_spacing=16)

        scroll.setWidget(self.grid_container)
        splitter.addWidget(scroll)

        splitter.setSizes([220, 980])
        main_layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(16)

        self.online_label = QLabel("● Online: 0")
        self.online_label.setStyleSheet("color: #3fb950; font-size: 12px;")
        self.offline_label = QLabel("● Offline: 0")
        self.offline_label.setStyleSheet("color: #f85149; font-size: 12px;")
        self.total_label = QLabel("Cəmi: 0")
        self.total_label.setStyleSheet("color: #8b949e; font-size: 12px;")

        status_layout.addWidget(self.online_label)
        status_layout.addWidget(self.offline_label)
        status_layout.addWidget(self.total_label)

        self.status_bar.addPermanentWidget(status_widget)
        self.status_bar.showMessage("Server gözlənilir...")

    def _connect_signals(self):
        self.agent_connected_signal.connect(self._on_agent_connected)
        self.agent_disconnected_signal.connect(self._on_agent_disconnected)
        self.screenshot_received_signal.connect(self._on_screenshot_received)

        self.toolbar.lock_clicked.connect(self._on_lock)
        self.toolbar.unlock_clicked.connect(self._on_unlock)
        self.toolbar.message_clicked.connect(self._on_send_message)
        self.toolbar.file_send_clicked.connect(self._on_send_file)
        self.toolbar.file_collect_clicked.connect(self._on_collect_files)
        self.toolbar.demo_fullscreen_clicked.connect(lambda: self._on_demo(True))
        self.toolbar.demo_window_clicked.connect(lambda: self._on_demo(False))
        self.toolbar.shutdown_clicked.connect(self._on_shutdown)
        self.toolbar.restart_clicked.connect(self._on_restart)
        self.toolbar.run_program_clicked.connect(self._on_run_program)
        self.toolbar.open_url_clicked.connect(self._on_open_url)
        self.toolbar.select_all_clicked.connect(self._select_all)
        self.toolbar.settings_clicked.connect(self._on_settings)
        self.toolbar.monitor_clicked.connect(self._on_stop_demo)
        self.toolbar.remote_control_clicked.connect(self._on_remote_control)

    # ═══ Otaq idarəetməsi ═══

    def _load_rooms(self):
        """Otaqları yükləyib sol paneli doldurur."""
        self.room_list.clear()

        # "Hamısı" elementi
        all_item = QListWidgetItem("  Bütün Kompüterlər")
        all_item.setData(Qt.ItemDataRole.UserRole, None)
        self.room_list.addItem(all_item)

        # Təyin olunmayanlar
        unassigned = QListWidgetItem("  Təyin olunmamış")
        unassigned.setData(Qt.ItemDataRole.UserRole, "__unassigned__")
        self.room_list.addItem(unassigned)

        # Otaqlar
        data = load_rooms()
        for room_name in data.get("rooms", []):
            count = sum(1 for v in data.get("assignments", {}).values() if v == room_name)
            item = QListWidgetItem(f"  {room_name}  ({count})")
            item.setData(Qt.ItemDataRole.UserRole, room_name)
            self.room_list.addItem(item)

        self.room_list.setCurrentRow(0)

    def _on_add_room(self):
        text, ok = QInputDialog.getText(self, "Yeni Otaq", "Otaq adı:")
        if ok and text.strip():
            if add_room(text.strip()):
                self._load_rooms()
                self.status_bar.showMessage(f"Otaq yaradıldı: {text.strip()}", 3000)
            else:
                self.status_bar.showMessage("Bu adda otaq artıq var!", 3000)

    def _on_room_context_menu(self, pos):
        item = self.room_list.itemAt(pos)
        if not item:
            return

        room_name = item.data(Qt.ItemDataRole.UserRole)
        if room_name is None or room_name == "__unassigned__":
            return  # Sistem elementləri üçün menyu yoxdur

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
            QMenu::item:selected { background-color: #21262d; }
            QMenu::separator {
                height: 1px;
                background-color: #30363d;
                margin: 4px 8px;
            }
        """)

        add_comp_action = menu.addAction("Kompüter əlavə et...")
        menu.addSeparator()
        rename_action = menu.addAction("Adını dəyiş...")
        delete_action = menu.addAction("Sil")

        action = menu.exec(self.room_list.mapToGlobal(pos))
        if action == add_comp_action:
            self._on_add_computer_to_room(room_name)
        elif action == rename_action:
            new_name, ok = QInputDialog.getText(
                self, "Otaq adını dəyiş", "Yeni ad:", text=room_name
            )
            if ok and new_name.strip():
                rename_room(room_name, new_name.strip())
                self._load_rooms()
                self._refresh_room_labels()
        elif action == delete_action:
            reply = QMessageBox.question(
                self, "Otaq Silmə",
                f'"{room_name}" otağını silmək istəyirsiniz?',
            )
            if reply == QMessageBox.StandardButton.Yes:
                remove_room(room_name)
                self._load_rooms()
                self._refresh_room_labels()

    def _on_room_selected(self, current, previous):
        if not current:
            return
        self._current_room_filter = current.data(Qt.ItemDataRole.UserRole)
        self._filter_computers()

    def _filter_computers(self):
        """Seçilmiş otağa görə kompüterləri filtrlə."""
        room_filter = self._current_room_filter

        for agent_id, widget in self.computer_widgets.items():
            agent_room = get_room_for(agent_id)
            if room_filter is None:
                # Hamısını göstər
                widget.setVisible(True)
            elif room_filter == "__unassigned__":
                widget.setVisible(agent_room is None)
            else:
                widget.setVisible(agent_room == room_filter)

    def _on_add_computer_to_room(self, room_name: str):
        """Otağa kompüter əlavə et — onlayn kompüterlərdən seçim."""
        # Hələ bu otağa təyin olunmamış kompüterləri göstər
        available = []
        available_ids = []
        for agent_id, widget in self.computer_widgets.items():
            current_room = get_room_for(agent_id)
            if current_room != room_name:
                alias = get_alias(agent_id) or widget.hostname
                available.append(alias)
                available_ids.append(agent_id)

        if not available:
            QMessageBox.information(
                self, "Kompüter yoxdur",
                "Əlavə ediləcək kompüter yoxdur — hamısı artıq bu otaqdadır."
            )
            return

        name, ok = QInputDialog.getItem(
            self, "Kompüter Əlavə Et",
            f'"{room_name}" otağına əlavə ediləcək kompüteri seçin:',
            available, editable=False,
        )
        if ok and name:
            idx = available.index(name)
            agent_id = available_ids[idx]
            assign_computer(agent_id, room_name)
            widget = self.computer_widgets.get(agent_id)
            if widget:
                widget.set_room(room_name)
            self._load_rooms()
            self._filter_computers()
            self.status_bar.showMessage(
                f"{name} → '{room_name}' otağına əlavə edildi", 3000
            )

    def _on_assign_room(self, agent_id: str):
        """Kompüteri otağa təyin et."""
        data = load_rooms()
        rooms = data.get("rooms", [])
        if not rooms:
            QMessageBox.information(self, "Otaq yoxdur", "Əvvəlcə otaq yaradın.")
            return

        room, ok = QInputDialog.getItem(
            self, "Otağa Təyin Et", "Otaq seçin:", rooms, editable=False,
        )
        if ok and room:
            assign_computer(agent_id, room)
            widget = self.computer_widgets.get(agent_id)
            if widget:
                widget.set_room(room)
            self._load_rooms()
            self._filter_computers()
            self.status_bar.showMessage(f"Kompüter '{room}' otağına təyin edildi", 3000)

    def _on_rename_computer(self, agent_id: str, new_name: str):
        """Kompüterin adını dəyişir."""
        set_alias(agent_id, new_name)
        widget = self.computer_widgets.get(agent_id)
        if widget:
            widget.set_display_name(new_name)
        self.status_bar.showMessage(f"Ad dəyişdirildi: {new_name}", 3000)

    def _refresh_room_labels(self):
        """Bütün widget-lərin otaq etiketlərini yeniləyir."""
        for agent_id, widget in self.computer_widgets.items():
            room = get_room_for(agent_id)
            widget.set_room(room)

    # ═══ Status ═══

    def _update_status_bar(self):
        online = sum(1 for w in self.computer_widgets.values() if w._online)
        total = len(self.computer_widgets)
        offline = total - online
        self.online_label.setText(f"● Online: {online}")
        self.offline_label.setText(f"● Offline: {offline}")
        self.total_label.setText(f"Cəmi: {total}")

    def _get_selected_ids(self) -> list[str]:
        selected = [aid for aid, w in self.computer_widgets.items()
                     if w.is_selected and w.isVisible()]
        if not selected:
            selected = [aid for aid, w in self.computer_widgets.items() if w.isVisible()]
        return selected

    # ═══ Server callback-ləri ═══

    @pyqtSlot(dict)
    def _on_agent_connected(self, agent_info: dict):
        agent_id = agent_info["agent_id"]
        hostname = agent_info["hostname"]
        self._agent_info[agent_id] = agent_info

        widget = ComputerWidget(agent_id, hostname)
        widget.clicked.connect(self._on_computer_clicked)
        widget.double_clicked.connect(self._on_computer_double_clicked)
        widget.rename_requested.connect(self._on_rename_computer)
        widget.assign_room_requested.connect(self._on_assign_room)
        widget.remote_control_requested.connect(self._open_remote_control)
        widget.set_online()

        # Alias varsa tətbiq et
        alias = get_alias(agent_id)
        if alias:
            widget.set_display_name(alias)

        # Otaq varsa etiket göstər
        room = get_room_for(agent_id)
        if room:
            widget.set_room(room)

        self.computer_widgets[agent_id] = widget
        self.flow_layout.addWidget(widget)
        self._update_status_bar()
        self._load_rooms()  # Sayları yeniləmək üçün
        self._filter_computers()
        self.status_bar.showMessage(f"{alias or hostname} qoşuldu", 3000)
        logger.info(f"GUI: Agent əlavə edildi — {hostname}")

    @pyqtSlot(str)
    def _on_agent_disconnected(self, agent_id: str):
        if agent_id in self.computer_widgets:
            self.computer_widgets[agent_id].set_offline()
            self._update_status_bar()

            if agent_id in self.viewer_windows:
                self.viewer_windows.pop(agent_id).close()
            if agent_id in self.remote_windows:
                self.remote_windows.pop(agent_id).close()

    @pyqtSlot(str, str)
    def _on_screenshot_received(self, agent_id: str, base64_data: str):
        if agent_id in self.computer_widgets:
            self.computer_widgets[agent_id].update_screenshot(base64_data)
        if agent_id in self.viewer_windows:
            self.viewer_windows[agent_id].update_image(base64_data)
        if agent_id in self.remote_windows:
            self.remote_windows[agent_id].update_image(base64_data)

    # ═══ Uzaqdan müdaxilə ═══

    def _on_remote_control(self):
        """Toolbar-dan uzaqdan müdaxilə — seçilmiş kompüter."""
        ids = self._get_selected_ids()
        if ids:
            self._open_remote_control(ids[0])

    def _open_remote_control(self, agent_id: str):
        """Uzaqdan müdaxilə pəncərəsini açır."""
        if agent_id in self.remote_windows:
            self.remote_windows[agent_id].raise_()
            self.remote_windows[agent_id].activateWindow()
            return

        info = self._agent_info.get(agent_id, {})
        alias = get_alias(agent_id)
        hostname = alias or info.get("hostname", agent_id)

        viewer = RemoteControlViewer(agent_id, hostname)
        viewer.mouse_event_signal.connect(
            lambda aid, data: self.send_remote_mouse_signal.emit(aid, data)
        )
        viewer.key_event_signal.connect(
            lambda aid, data: self.send_remote_key_signal.emit(aid, data)
        )
        viewer.show()
        self.remote_windows[agent_id] = viewer
        self.status_bar.showMessage(f"Uzaqdan müdaxilə: {hostname}", 3000)

    # ═══ Toolbar callback-ləri ═══

    def _on_computer_clicked(self, agent_id: str):
        for aid, w in self.computer_widgets.items():
            w.set_selected(aid == agent_id)

    def _on_computer_double_clicked(self, agent_id: str):
        self._open_remote_control(agent_id)

    def _on_lock(self):
        ids = self._get_selected_ids()
        self.send_lock_signal.emit(ids)
        self.status_bar.showMessage(f"{len(ids)} kompüter kilidləndi", 3000)

    def _on_unlock(self):
        ids = self._get_selected_ids()
        self.send_unlock_signal.emit(ids)
        self.status_bar.showMessage(f"{len(ids)} kompüterin kilidi açıldı", 3000)

    def _on_send_message(self):
        dialog = SendMessageDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["text"]:
                ids = self._get_selected_ids()
                self.send_message_signal.emit(ids, data)

    def _on_send_file(self):
        dialog = SendFileDialog(self)
        if dialog.exec():
            filepath = dialog.get_file_path()
            if filepath:
                ids = self._get_selected_ids()
                self.send_file_signal.emit(ids, filepath)
                self.status_bar.showMessage(f"Fayl göndərilir: {len(ids)} kompüter", 3000)

    def _on_collect_files(self):
        ids = self._get_selected_ids()
        self.collect_file_signal.emit(ids)
        self.status_bar.showMessage("Fayllar toplanır...", 3000)

    def _on_demo(self, fullscreen: bool):
        ids = self._get_selected_ids()
        self.send_demo_start_signal.emit(ids, fullscreen)
        mode = "tam ekran" if fullscreen else "pəncərə"
        self.status_bar.showMessage(f"Demo başladı ({mode})", 3000)

    def _on_stop_demo(self):
        ids = self._get_selected_ids()
        self.send_demo_stop_signal.emit(ids)
        self.status_bar.showMessage("Demo dayandırıldı", 3000)

    def _on_shutdown(self):
        ids = self._get_selected_ids()
        reply = QMessageBox.question(
            self, "Söndürmə Təsdiqi",
            f"{len(ids)} kompüteri söndürmək istəyirsiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.send_shutdown_signal.emit(ids, 30)

    def _on_restart(self):
        ids = self._get_selected_ids()
        reply = QMessageBox.question(
            self, "Yenidən Başlatma Təsdiqi",
            f"{len(ids)} kompüteri yenidən başlatmaq istəyirsiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.send_restart_signal.emit(ids, 30)

    def _on_run_program(self):
        dialog = RunProgramDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["program"]:
                ids = self._get_selected_ids()
                self.send_run_program_signal.emit(ids, data["program"], data["args"])

    def _on_open_url(self):
        dialog = OpenUrlDialog(self)
        if dialog.exec():
            url = dialog.get_url()
            if url:
                ids = self._get_selected_ids()
                self.send_open_url_signal.emit(ids, url)

    def _select_all(self):
        visible = [w for w in self.computer_widgets.values() if w.isVisible()]
        all_selected = all(w.is_selected for w in visible) if visible else False
        for w in visible:
            w.set_selected(not all_selected)

    def _on_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            self.config = dialog.get_config()
            from ..common.config import save_config
            save_config(self.config)
            self.status_bar.showMessage("Parametrlər saxlanıldı", 3000)

    def closeEvent(self, event):
        for viewer in self.viewer_windows.values():
            viewer.close()
        for viewer in self.remote_windows.values():
            viewer.close()
        event.accept()
