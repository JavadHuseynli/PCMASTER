"""
ClassRoom Manager Master - Əsas giriş nöqtəsi.
GUI pəncərəsini açır, serveri başladır, əmrləri yönləndirir.
"""
from __future__ import annotations

import sys
import asyncio
import logging
from pathlib import Path
from threading import Thread

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from ..common.config import load_config
from ..common.constants import MessageType
from .server import MasterServer, AgentInfo
from .ui.main_window import MainWindow
from .handlers.control import ControlHandler
from .handlers.file_transfer import FileTransferHandler
from .handlers.demo import DemoHandler
from ..agent.screen_capture import ScreenCapture
from ..common.discovery import MasterBroadcaster

# Logging
log_dir = Path.home() / ".classroom_manager"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / "master.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("master")


class MasterApp:
    """Master tətbiqi — GUI, server və handler-ləri birləşdirir."""

    def __init__(self):
        self.config = load_config()
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("ClassRoom Manager Master")

        # GUI
        self.window = MainWindow(self.config)

        # Server
        self._loop: asyncio.AbstractEventLoop | None = None
        self._server_thread: Thread | None = None
        self.server: MasterServer | None = None

        # Handlers
        self.broadcaster = MasterBroadcaster(
            master_port=self.config.get("master", {}).get("port", 11100),
            psk=self.config.get("security", {}).get("pre_shared_key", ""),
        )
        self.demo_handler = DemoHandler()
        self.screen_capture = ScreenCapture(
            quality=self.config.get("master", {}).get("demo_quality", 60)
        )

        self._connect_signals()

    def _connect_signals(self):
        """GUI siqnallarını server əmrlərinə bağlayır."""
        w = self.window

        w.send_lock_signal.connect(self._on_lock)
        w.send_unlock_signal.connect(self._on_unlock)
        w.send_message_signal.connect(self._on_send_message)
        w.send_file_signal.connect(self._on_send_file)
        w.collect_file_signal.connect(self._on_collect_files)
        w.send_demo_start_signal.connect(self._on_demo_start)
        w.send_demo_stop_signal.connect(self._on_demo_stop)
        w.send_shutdown_signal.connect(self._on_shutdown)
        w.send_restart_signal.connect(self._on_restart)
        w.send_run_program_signal.connect(self._on_run_program)
        w.send_open_url_signal.connect(self._on_open_url)
        w.send_remote_mouse_signal.connect(self._on_remote_mouse)
        w.send_remote_key_signal.connect(self._on_remote_key)

    def _run_async(self, coro):
        """Asinxron funksiyanı server loop-da işlədir."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, self._loop)

    def _start_server(self):
        """Serveri ayrı thread-də başladır."""
        def run_server():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            self.server = MasterServer(
                self.config,
                on_agent_connected=self._on_agent_connected,
                on_agent_disconnected=self._on_agent_disconnected,
                on_screenshot=self._on_screenshot,
            )

            try:
                # Server və broadcast-ı paralel başlat
                self._loop.run_until_complete(asyncio.gather(
                    self.server.start(),
                    self.broadcaster.start(),
                ))
            except Exception as e:
                logger.error(f"Server xətası: {e}")

        self._server_thread = Thread(target=run_server, daemon=True)
        self._server_thread.start()

    # ─── Server callback-ləri (server thread-dən gəlir) ───

    def _on_agent_connected(self, agent: AgentInfo):
        """Agent qoşulduqda — GUI-yə siqnal göndər."""
        self.window.agent_connected_signal.emit({
            "agent_id": agent.agent_id,
            "hostname": agent.hostname,
            "os": agent.os,
            "username": agent.username,
            "ip_address": agent.ip_address,
        })

    def _on_agent_disconnected(self, agent: AgentInfo):
        """Agent ayrıldıqda."""
        self.window.agent_disconnected_signal.emit(agent.agent_id)

    def _on_screenshot(self, agent_id: str, base64_data: str):
        """Screenshot alındıqda."""
        self.window.screenshot_received_signal.emit(agent_id, base64_data)

    # ─── GUI əmr callback-ləri ───

    def _on_lock(self, agent_ids: list):
        self._run_async(
            self.server.send_to_selected(agent_ids, MessageType.LOCK_SCREEN)
        )

    def _on_unlock(self, agent_ids: list):
        self._run_async(
            self.server.send_to_selected(agent_ids, MessageType.UNLOCK_SCREEN)
        )

    def _on_send_message(self, agent_ids: list, data: dict):
        self._run_async(
            self.server.send_to_selected(
                agent_ids, MessageType.SEND_MESSAGE,
                {"title": data["title"], "text": data["text"]}
            )
        )

    def _on_send_file(self, agent_ids: list, filepath: str):
        handler = FileTransferHandler(self.server)
        self._run_async(handler.send_file(agent_ids, filepath))

    def _on_collect_files(self, agent_ids: list):
        handler = FileTransferHandler(self.server)
        self._run_async(handler.collect_files(agent_ids))

    def _on_demo_start(self, agent_ids: list, fullscreen: bool):
        fps = self.config.get("master", {}).get("demo_fps", 10)
        quality = self.config.get("master", {}).get("demo_quality", 60)
        self._run_async(
            self.demo_handler.start(
                self.server, agent_ids, fullscreen,
                self.screen_capture, fps, quality
            )
        )

    def _on_demo_stop(self, agent_ids: list):
        self._run_async(self.demo_handler.stop(self.server, agent_ids))

    def _on_shutdown(self, agent_ids: list, delay: int):
        self._run_async(
            self.server.send_to_selected(
                agent_ids, MessageType.SHUTDOWN, {"delay": delay}
            )
        )

    def _on_restart(self, agent_ids: list, delay: int):
        self._run_async(
            self.server.send_to_selected(
                agent_ids, MessageType.RESTART, {"delay": delay}
            )
        )

    def _on_run_program(self, agent_ids: list, program: str, args: list):
        self._run_async(
            self.server.send_to_selected(
                agent_ids, MessageType.RUN_PROGRAM,
                {"program": program, "args": args}
            )
        )

    def _on_open_url(self, agent_ids: list, url: str):
        self._run_async(
            self.server.send_to_selected(
                agent_ids, MessageType.OPEN_URL, {"url": url}
            )
        )

    def _on_remote_mouse(self, agent_id: str, event_data: dict):
        self._run_async(
            self.server.send_to_agent(
                agent_id, MessageType.REMOTE_MOUSE_EVENT, event_data
            )
        )

    def _on_remote_key(self, agent_id: str, event_data: dict):
        self._run_async(
            self.server.send_to_agent(
                agent_id, MessageType.REMOTE_KEY_EVENT, event_data
            )
        )

    def run(self):
        """Tətbiqi başladır."""
        self._start_server()
        self.window.status_bar.showMessage(
            f"Server işləyir: port {self.config.get('master', {}).get('port', 11100)}"
        )
        self.window.show()
        sys.exit(self.app.exec())


def main():
    app = MasterApp()
    app.run()


if __name__ == "__main__":
    main()
