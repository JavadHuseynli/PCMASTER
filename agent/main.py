"""
ClassRoom Manager Agent - Əsas giriş nöqtəsi.
System tray-da işləyən agent: ekran çəkmə, əmr icra, fayl idarəetmə.
"""
from __future__ import annotations

import sys
import asyncio
import logging
import signal
import base64
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap

from ..common.config import load_config
from ..common.constants import MessageType
from .client import AgentClient
from .screen_capture import ScreenCapture
from .command_executor import CommandExecutor
from .file_handler import FileHandler
from .tray_icon import AgentTrayIcon

# Logging konfiqurasiyası
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / ".classroom_manager" / "agent.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("agent")


class LockScreenWindow(QWidget):
    """Ekran kilidi pəncərəsi — tam ekran, qapatılmaz."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setStyleSheet("background-color: #1a1a2e;")

        layout = QVBoxLayout(self)
        label = QLabel("🔒 Ekranınız müəllim tərəfindən kilidlənib")
        label.setStyleSheet(
            "color: white; font-size: 28px; font-weight: bold;"
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def show_fullscreen(self):
        self.showFullScreen()
        self.activateWindow()
        self.raise_()

    def keyPressEvent(self, event):
        event.ignore()  # Bütün düymələri blokla

    def closeEvent(self, event):
        event.ignore()  # Bağlanmanın qarşısını al


class DemoWindow(QWidget):
    """Demo rejimi pəncərəsi — müəllim ekranını göstərir."""

    def __init__(self, fullscreen: bool = True):
        super().__init__()
        self.fullscreen_mode = fullscreen
        self.setWindowTitle("ClassRoom Manager - Demo")

        if fullscreen:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
            )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")
        layout.addWidget(self.image_label)

    def update_frame(self, base64_data: str):
        """Demo kadrını yeniləyir."""
        try:
            img_data = base64.b64decode(base64_data)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            if self.fullscreen_mode:
                pixmap = pixmap.scaled(
                    self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            self.image_label.setPixmap(pixmap)
        except Exception as e:
            logger.error(f"Demo kadr xətası: {e}")

    def show_demo(self):
        if self.fullscreen_mode:
            self.showFullScreen()
        else:
            self.resize(1024, 576)
            self.show()


class AsyncWorkerSignals(QObject):
    """Async worker siqnalları — Qt thread ilə async arasında körpü."""
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    lock_screen = pyqtSignal()
    unlock_screen = pyqtSignal()
    start_demo = pyqtSignal(bool)  # fullscreen
    stop_demo = pyqtSignal()
    demo_frame = pyqtSignal(str)  # base64
    show_message = pyqtSignal(str, str)  # title, message
    screenshot_request = pyqtSignal()


class AsyncWorker(QThread):
    """Asyncio döngüsünü ayrı thread-də işlədən worker."""

    def __init__(self, config: dict, signals: AsyncWorkerSignals):
        super().__init__()
        self.config = config
        self.signals = signals
        self.client: AgentClient | None = None
        self.screen_capture = ScreenCapture(
            quality=config.get("master", {}).get("screenshot_quality", 50),
            thumbnail_size=tuple(config.get("master", {}).get("thumbnail_size", [320, 180])),
        )
        self.command_executor = CommandExecutor()
        self.file_handler = FileHandler(
            config.get("agent", {}).get("file_save_path")
        )
        self._loop: asyncio.AbstractEventLoop | None = None
        self._screenshot_task = None

    def run(self):
        """Thread-in əsas metodu — asyncio loop işlədir."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self.client = AgentClient(self.config, message_callback=self._on_message)

        try:
            self._loop.run_until_complete(self._main_loop())
        except Exception as e:
            logger.error(f"Worker xətası: {e}")
        finally:
            self._loop.close()

    async def _main_loop(self):
        """Əsas asinxron döngü."""
        await asyncio.gather(
            self.client.run(),
            self._screenshot_loop(),
        )

    async def _screenshot_loop(self):
        """Dövri screenshot göndərmə."""
        interval = self.config.get("master", {}).get("screenshot_interval", 3)
        while self.client.running:
            if self.client.connected:
                screenshot_data = self.screen_capture.capture_screenshot(as_thumbnail=True)
                if screenshot_data:
                    await self.client.send(
                        MessageType.SCREENSHOT,
                        payload={"image": screenshot_data},
                    )
            await asyncio.sleep(interval)

    async def _on_message(self, message: dict):
        """Master-dən gələn mesajı emal edir."""
        msg_type = message.get("type", "")
        payload = message.get("payload", {})

        if msg_type == MessageType.LOCK_SCREEN:
            self.signals.lock_screen.emit()

        elif msg_type == MessageType.UNLOCK_SCREEN:
            self.signals.unlock_screen.emit()

        elif msg_type == MessageType.START_DEMO:
            fullscreen = payload.get("fullscreen", True)
            self.signals.start_demo.emit(fullscreen)

        elif msg_type == MessageType.STOP_DEMO:
            self.signals.stop_demo.emit()

        elif msg_type == MessageType.DEMO_FRAME:
            image_data = payload.get("image", "")
            if image_data:
                self.signals.demo_frame.emit(image_data)

        elif msg_type == MessageType.SEND_MESSAGE:
            title = payload.get("title", "Müəllimdən Mesaj")
            text = payload.get("text", "")
            self.signals.show_message.emit(title, text)

        elif msg_type == MessageType.SHUTDOWN:
            delay = payload.get("delay", 30)
            self.command_executor.shutdown(delay)

        elif msg_type == MessageType.RESTART:
            delay = payload.get("delay", 30)
            self.command_executor.restart(delay)

        elif msg_type == MessageType.RUN_PROGRAM:
            program = payload.get("program", "")
            args = payload.get("args", [])
            if program:
                self.command_executor.run_program(program, args)

        elif msg_type == MessageType.OPEN_URL:
            url = payload.get("url", "")
            if url:
                self.command_executor.open_url(url)

        elif msg_type == MessageType.FILE_TRANSFER:
            file_id = payload.get("file_id", "")
            filename = payload.get("filename", "")
            total_chunks = payload.get("total_chunks", 0)
            self.file_handler.start_receive(file_id, filename, total_chunks)

        elif msg_type == MessageType.FILE_CHUNK:
            file_id = payload.get("file_id", "")
            chunk_index = payload.get("chunk_index", 0)
            data = payload.get("data", "")
            self.file_handler.receive_chunk(file_id, chunk_index, data)

        elif msg_type == MessageType.FILE_COMPLETE:
            file_id = payload.get("file_id", "")
            self.file_handler.complete_receive(file_id)

        elif msg_type == MessageType.REMOTE_MOUSE_EVENT:
            self.command_executor.remote_mouse(payload)

        elif msg_type == MessageType.REMOTE_KEY_EVENT:
            self.command_executor.remote_key(payload)

        elif msg_type == MessageType.COLLECT_FILE:
            directory = payload.get("directory")
            files = self.file_handler.collect_files(directory)
            await self.client.send(
                MessageType.FILE_TRANSFER,
                payload={"files": files, "action": "collect_response"},
            )

    def stop(self):
        """Worker-i dayandırır."""
        if self.client:
            self.client.running = False
        self.screen_capture.close()


def main():
    """Agent proqramının əsas funksiyası."""
    # Log qovluğunu yarat
    log_dir = Path.home() / ".classroom_manager"
    log_dir.mkdir(parents=True, exist_ok=True)

    config = load_config()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("ClassRoom Manager Agent")

    # Tray ikonu
    tray = AgentTrayIcon(app)
    tray.show()

    # Pəncərələr
    lock_window = LockScreenWindow()
    demo_window = None

    # Async worker
    signals = AsyncWorkerSignals()
    worker = AsyncWorker(config, signals)

    # Siqnal bağlantıları
    def on_lock():
        lock_window.show_fullscreen()
        tray.show_message("Ekran Kilidi", "Ekranınız kilidləndi")

    def on_unlock():
        lock_window.hide()

    def on_start_demo(fullscreen):
        nonlocal demo_window
        demo_window = DemoWindow(fullscreen=fullscreen)
        demo_window.show_demo()

    def on_stop_demo():
        nonlocal demo_window
        if demo_window:
            demo_window.close()
            demo_window = None

    def on_demo_frame(data):
        if demo_window:
            demo_window.update_frame(data)

    def on_show_message(title, text):
        tray.show_message(title, text)

    def on_quit():
        worker.stop()
        worker.wait(3000)
        app.quit()

    signals.lock_screen.connect(on_lock)
    signals.unlock_screen.connect(on_unlock)
    signals.start_demo.connect(on_start_demo)
    signals.stop_demo.connect(on_stop_demo)
    signals.demo_frame.connect(on_demo_frame)
    signals.show_message.connect(on_show_message)
    tray.signals.quit_requested.connect(on_quit)

    # Worker-i başlat
    worker.start()
    tray.set_status("Qoşulur...")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
