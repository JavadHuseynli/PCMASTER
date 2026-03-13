"""
ClassRoom Manager Konfiqurator - Parametrləri tənzimləmə GUI.
Master və Agent konfiqurasiyalarını bir yerdən idarə edir.
"""

import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QFormLayout, QLineEdit, QSpinBox, QCheckBox,
    QPushButton, QLabel, QGroupBox, QMessageBox, QComboBox,
)
from PyQt6.QtCore import Qt

from ..common.config import load_config, save_config, get_config_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("configurator")


class ConfiguratorWindow(QMainWindow):
    """Konfiqurator əsas pəncərəsi."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClassRoom Manager - Konfiqurator")
        self.setMinimumSize(600, 500)
        self.config = load_config()
        self._setup_ui()
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e32; }
            QWidget { color: #e0e0e0; font-size: 13px; }
            QTabWidget::pane {
                border: 1px solid #3a3a5c;
                background-color: #1e1e32;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #16162a;
                border: 1px solid #3a3a5c;
                padding: 8px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2a2a4a;
                border-bottom: none;
            }
            QGroupBox {
                border: 1px solid #3a3a5c;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 8px;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #2a2a4a;
                border: 1px solid #3a3a5c;
                border-radius: 4px;
                padding: 6px;
                color: white;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:pressed { background-color: #1565C0; }
            QPushButton#cancel_btn {
                background-color: #546E7A;
            }
        """)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        tabs = QTabWidget()

        # Master tab
        master_tab = self._create_master_tab()
        tabs.addTab(master_tab, "Master (Server)")

        # Agent tab
        agent_tab = self._create_agent_tab()
        tabs.addTab(agent_tab, "Agent (Client)")

        # Təhlükəsizlik tab
        security_tab = self._create_security_tab()
        tabs.addTab(security_tab, "Təhlükəsizlik")

        layout.addWidget(tabs)

        # Düymələr
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Ləğv Et")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Saxla")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        # Config path
        path_label = QLabel(f"Konfiqurasiya: {get_config_path()}")
        path_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(path_label)

    def _create_master_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Şəbəkə
        net_group = QGroupBox("Şəbəkə")
        net_layout = QFormLayout()

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(self.config["master"]["port"])
        net_layout.addRow("Port:", self.port_spin)

        net_group.setLayout(net_layout)
        layout.addWidget(net_group)

        # Monitorinq
        mon_group = QGroupBox("Monitorinq")
        mon_layout = QFormLayout()

        self.ss_interval = QSpinBox()
        self.ss_interval.setRange(1, 30)
        self.ss_interval.setValue(self.config["master"]["screenshot_interval"])
        self.ss_interval.setSuffix(" saniyə")
        mon_layout.addRow("Screenshot intervalı:", self.ss_interval)

        self.ss_quality = QSpinBox()
        self.ss_quality.setRange(10, 100)
        self.ss_quality.setValue(self.config["master"]["screenshot_quality"])
        self.ss_quality.setSuffix("%")
        mon_layout.addRow("Screenshot keyfiyyəti:", self.ss_quality)

        mon_group.setLayout(mon_layout)
        layout.addWidget(mon_group)

        # Demo
        demo_group = QGroupBox("Demo Rejimi")
        demo_layout = QFormLayout()

        self.demo_fps = QSpinBox()
        self.demo_fps.setRange(5, 30)
        self.demo_fps.setValue(self.config["master"]["demo_fps"])
        self.demo_fps.setSuffix(" FPS")
        demo_layout.addRow("Demo FPS:", self.demo_fps)

        self.demo_quality = QSpinBox()
        self.demo_quality.setRange(10, 100)
        self.demo_quality.setValue(self.config["master"]["demo_quality"])
        self.demo_quality.setSuffix("%")
        demo_layout.addRow("Demo keyfiyyəti:", self.demo_quality)

        demo_group.setLayout(demo_layout)
        layout.addWidget(demo_group)

        layout.addStretch()
        return widget

    def _create_agent_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        conn_group = QGroupBox("Əlaqə")
        conn_layout = QFormLayout()

        self.master_host = QLineEdit()
        self.master_host.setText(self.config["agent"]["master_host"])
        conn_layout.addRow("Master IP:", self.master_host)

        self.master_port = QSpinBox()
        self.master_port.setRange(1024, 65535)
        self.master_port.setValue(self.config["agent"]["master_port"])
        conn_layout.addRow("Master Port:", self.master_port)

        self.heartbeat_interval = QSpinBox()
        self.heartbeat_interval.setRange(1, 60)
        self.heartbeat_interval.setValue(self.config["agent"]["heartbeat_interval"])
        self.heartbeat_interval.setSuffix(" saniyə")
        conn_layout.addRow("Heartbeat intervalı:", self.heartbeat_interval)

        self.auto_connect = QCheckBox("Avtomatik qoşulma")
        self.auto_connect.setChecked(self.config["agent"]["auto_connect"])
        conn_layout.addRow(self.auto_connect)

        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        file_group = QGroupBox("Fayl")
        file_layout = QFormLayout()

        self.file_save_path = QLineEdit()
        self.file_save_path.setText(self.config["agent"]["file_save_path"])
        file_layout.addRow("Fayl saxlama yolu:", self.file_save_path)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        layout.addStretch()
        return widget

    def _create_security_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        sec_group = QGroupBox("Təhlükəsizlik Parametrləri")
        sec_layout = QFormLayout()

        self.use_tls = QCheckBox("TLS şifrələmə aktiv")
        self.use_tls.setChecked(self.config["security"]["use_tls"])
        sec_layout.addRow(self.use_tls)

        self.psk_input = QLineEdit()
        self.psk_input.setText(self.config["security"]["pre_shared_key"])
        self.psk_input.setEchoMode(QLineEdit.EchoMode.Password)
        sec_layout.addRow("Paylaşılmış açar:", self.psk_input)

        self.show_psk = QCheckBox("Açarı göstər")
        self.show_psk.toggled.connect(
            lambda checked: self.psk_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        sec_layout.addRow(self.show_psk)

        self.allowed_masters = QLineEdit()
        self.allowed_masters.setText(
            ", ".join(self.config["security"].get("allowed_masters", []))
        )
        self.allowed_masters.setPlaceholderText("IP1, IP2, ... (boş = hamısı)")
        sec_layout.addRow("İcazəli master IP-lər:", self.allowed_masters)

        sec_group.setLayout(sec_layout)
        layout.addWidget(sec_group)

        layout.addStretch()
        return widget

    def _save(self):
        """Konfiqurasiyanı saxlayır."""
        # Master
        self.config["master"]["port"] = self.port_spin.value()
        self.config["master"]["screenshot_interval"] = self.ss_interval.value()
        self.config["master"]["screenshot_quality"] = self.ss_quality.value()
        self.config["master"]["demo_fps"] = self.demo_fps.value()
        self.config["master"]["demo_quality"] = self.demo_quality.value()

        # Agent
        self.config["agent"]["master_host"] = self.master_host.text()
        self.config["agent"]["master_port"] = self.master_port.value()
        self.config["agent"]["heartbeat_interval"] = self.heartbeat_interval.value()
        self.config["agent"]["auto_connect"] = self.auto_connect.isChecked()
        self.config["agent"]["file_save_path"] = self.file_save_path.text()

        # Təhlükəsizlik
        self.config["security"]["use_tls"] = self.use_tls.isChecked()
        self.config["security"]["pre_shared_key"] = self.psk_input.text()
        masters_text = self.allowed_masters.text().strip()
        self.config["security"]["allowed_masters"] = (
            [m.strip() for m in masters_text.split(",") if m.strip()]
            if masters_text else []
        )

        if save_config(self.config):
            QMessageBox.information(self, "Uğurlu", "Konfiqurasiya saxlanıldı!")
            self.close()
        else:
            QMessageBox.critical(self, "Xəta", "Konfiqurasiya saxlanıla bilmədi!")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ClassRoom Manager Konfiqurator")
    window = ConfiguratorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
