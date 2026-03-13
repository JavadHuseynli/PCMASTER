"""
ClassRoom Manager Master - Modern dialoq pəncərələri.
Mesaj göndərmə, fayl seçmə, proqram/URL açma, parametrlər.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QFileDialog, QSpinBox, QCheckBox,
    QFormLayout, QDialogButtonBox, QGroupBox,
)
from PyQt6.QtCore import Qt


DIALOG_STYLE = """
    QDialog {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Helvetica Neue', 'Segoe UI', sans-serif;
    }
    QLabel {
        color: #c9d1d9;
        font-size: 13px;
    }
    QLineEdit, QTextEdit {
        background-color: #161b22;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 8px;
        font-size: 13px;
        selection-background-color: #1f6feb;
    }
    QLineEdit:focus, QTextEdit:focus {
        border: 1px solid #58a6ff;
    }
    QPushButton {
        background-color: #238636;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton:hover {
        background-color: #2ea043;
    }
    QPushButton:pressed {
        background-color: #1a7f37;
    }
    QDialogButtonBox QPushButton {
        min-width: 80px;
    }
    QDialogButtonBox QPushButton[text="Cancel"],
    QDialogButtonBox QPushButton[text="&Cancel"] {
        background-color: #21262d;
        color: #c9d1d9;
    }
    QDialogButtonBox QPushButton[text="Cancel"]:hover,
    QDialogButtonBox QPushButton[text="&Cancel"]:hover {
        background-color: #30363d;
    }
    QGroupBox {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        padding-top: 28px;
        margin-top: 8px;
        font-size: 13px;
        font-weight: 600;
        color: #c9d1d9;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        padding: 0 8px;
        color: #8b949e;
    }
    QSpinBox {
        background-color: #161b22;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 6px;
        font-size: 13px;
    }
    QSpinBox:focus {
        border: 1px solid #58a6ff;
    }
    QCheckBox {
        color: #c9d1d9;
        font-size: 13px;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 1px solid #30363d;
        border-radius: 4px;
        background-color: #161b22;
    }
    QCheckBox::indicator:checked {
        background-color: #238636;
        border-color: #238636;
    }
"""


class SendMessageDialog(QDialog):
    """Şagirdlərə mesaj göndərmə dialoqu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mesaj Göndər")
        self.setMinimumWidth(450)
        self.setStyleSheet(DIALOG_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("Başlıq")
        title_label.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 600;")
        layout.addWidget(title_label)

        self.title_input = QLineEdit()
        self.title_input.setText("Müəllimdən Mesaj")
        layout.addWidget(self.title_input)

        msg_label = QLabel("Mesaj mətni")
        msg_label.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 600;")
        layout.addWidget(msg_label)

        self.message_input = QTextEdit()
        self.message_input.setMinimumHeight(120)
        self.message_input.setPlaceholderText("Mesajınızı yazın...")
        layout.addWidget(self.message_input)

        layout.addSpacing(8)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Göndər")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Ləğv et")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> dict:
        return {
            "title": self.title_input.text(),
            "text": self.message_input.toPlainText(),
        }


class SendFileDialog(QDialog):
    """Fayl göndərmə dialoqu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fayl Göndər")
        self.setMinimumWidth(500)
        self.setStyleSheet(DIALOG_STYLE)
        self._file_path = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("Göndəriləcək fayl")
        label.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 600;")
        layout.addWidget(label)

        h_layout = QHBoxLayout()
        h_layout.setSpacing(8)
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.path_input.setPlaceholderText("Fayl seçin...")
        h_layout.addWidget(self.path_input)

        browse_btn = QPushButton("Seç...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse)
        h_layout.addWidget(browse_btn)
        layout.addLayout(h_layout)

        # Fayl haqqında məlumat
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        layout.addWidget(self.info_label)

        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Göndər")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Ləğv et")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Fayl Seçin")
        if path:
            self._file_path = path
            self.path_input.setText(path)
            # Fayl ölçüsü göstər
            import os
            size = os.path.getsize(path)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            self.info_label.setText(f"Ölçü: {size_str}  •  Hədəf: ~/Desktop/ClassRoom/")

    def get_file_path(self) -> str:
        return self._file_path


class RunProgramDialog(QDialog):
    """Proqram işə salma dialoqu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Proqram Aç")
        self.setMinimumWidth(450)
        self.setStyleSheet(DIALOG_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        prog_label = QLabel("Proqram")
        prog_label.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 600;")
        layout.addWidget(prog_label)

        h_layout = QHBoxLayout()
        h_layout.setSpacing(8)
        self.program_input = QLineEdit()
        self.program_input.setPlaceholderText("məs: Safari, notepad.exe, /usr/bin/firefox")
        h_layout.addWidget(self.program_input)

        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(40)
        browse_btn.clicked.connect(self._browse)
        h_layout.addWidget(browse_btn)
        layout.addLayout(h_layout)

        args_label = QLabel("Arqumentlər (ixtiyari)")
        args_label.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 600;")
        layout.addWidget(args_label)

        self.args_input = QLineEdit()
        self.args_input.setPlaceholderText("boşluqla ayrılmış arqumentlər")
        layout.addWidget(self.args_input)

        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("İşə Sal")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Ləğv et")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Proqram Seçin")
        if path:
            self.program_input.setText(path)

    def get_data(self) -> dict:
        args = self.args_input.text().split() if self.args_input.text() else []
        return {
            "program": self.program_input.text(),
            "args": args,
        }


class OpenUrlDialog(QDialog):
    """URL açma dialoqu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("URL Aç")
        self.setMinimumWidth(450)
        self.setStyleSheet(DIALOG_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("Web ünvan")
        label.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 600;")
        layout.addWidget(label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        layout.addWidget(self.url_input)

        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Aç")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Ləğv et")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_url(self) -> str:
        return self.url_input.text()


class SettingsDialog(QDialog):
    """Parametrlər dialoqu."""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parametrlər")
        self.setMinimumWidth(500)
        self.setStyleSheet(DIALOG_STYLE)
        self.config = config.copy()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Server
        server_group = QGroupBox("Server")
        server_layout = QFormLayout()
        server_layout.setSpacing(10)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(self.config.get("master", {}).get("port", 11100))
        server_layout.addRow("Port:", self.port_spin)

        self.screenshot_interval = QSpinBox()
        self.screenshot_interval.setRange(1, 30)
        self.screenshot_interval.setValue(
            self.config.get("master", {}).get("screenshot_interval", 3)
        )
        self.screenshot_interval.setSuffix(" san")
        server_layout.addRow("Screenshot intervalı:", self.screenshot_interval)

        self.screenshot_quality = QSpinBox()
        self.screenshot_quality.setRange(10, 100)
        self.screenshot_quality.setValue(
            self.config.get("master", {}).get("screenshot_quality", 50)
        )
        self.screenshot_quality.setSuffix("%")
        server_layout.addRow("Screenshot keyfiyyəti:", self.screenshot_quality)

        self.demo_fps = QSpinBox()
        self.demo_fps.setRange(5, 30)
        self.demo_fps.setValue(self.config.get("master", {}).get("demo_fps", 10))
        self.demo_fps.setSuffix(" FPS")
        server_layout.addRow("Demo FPS:", self.demo_fps)

        server_group.setLayout(server_layout)
        layout.addWidget(server_group)

        # Təhlükəsizlik
        security_group = QGroupBox("Təhlükəsizlik")
        security_layout = QFormLayout()
        security_layout.setSpacing(10)

        self.tls_check = QCheckBox("TLS şifrələmə aktiv")
        self.tls_check.setChecked(self.config.get("security", {}).get("use_tls", False))
        security_layout.addRow(self.tls_check)

        self.psk_input = QLineEdit()
        self.psk_input.setText(self.config.get("security", {}).get("pre_shared_key", ""))
        self.psk_input.setEchoMode(QLineEdit.EchoMode.Password)
        security_layout.addRow("Paylaşılmış açar:", self.psk_input)

        security_group.setLayout(security_layout)
        layout.addWidget(security_group)

        # Düymələr
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Saxla")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Ləğv et")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_config(self) -> dict:
        self.config["master"]["port"] = self.port_spin.value()
        self.config["master"]["screenshot_interval"] = self.screenshot_interval.value()
        self.config["master"]["screenshot_quality"] = self.screenshot_quality.value()
        self.config["master"]["demo_fps"] = self.demo_fps.value()
        self.config["security"]["use_tls"] = self.tls_check.isChecked()
        self.config["security"]["pre_shared_key"] = self.psk_input.text()
        return self.config
