"""
ClassRoom Manager Master - Demo rejimi handler.
Müəllim ekranını çəkib agentlərə yayımlayır.
"""
from __future__ import annotations

import asyncio
import logging
from ..handlers.monitor import MonitorHandler

logger = logging.getLogger(__name__)


class DemoHandler:
    """Demo rejimi — müəllim ekranını yayımlama."""

    def __init__(self):
        self.active = False
        self._task: asyncio.Task | None = None

    def is_active(self) -> bool:
        return self.active

    async def start(self, server, agent_ids: list[str], fullscreen: bool,
                    screen_capture, fps: int = 10, quality: int = 60):
        """Demo yayımını başladır."""
        self.active = True
        logger.info(f"Demo başladı: {len(agent_ids)} agent, FPS={fps}")

        from ...common.constants import MessageType

        # Agentlərə START_DEMO göndər
        await server.send_to_selected(
            agent_ids, MessageType.START_DEMO, {"fullscreen": fullscreen}
        )

        # Ekran çəkib göndərmə döngüsü
        interval = 1.0 / fps
        while self.active:
            frame = screen_capture.capture_full_screenshot(quality=quality)
            if frame:
                await server.send_to_selected(
                    agent_ids, MessageType.DEMO_FRAME, {"image": frame}
                )
            await asyncio.sleep(interval)

    async def stop(self, server, agent_ids: list[str]):
        """Demo yayımını dayandırır."""
        self.active = False
        from ...common.constants import MessageType
        await server.send_to_selected(agent_ids, MessageType.STOP_DEMO)
        logger.info("Demo dayandırıldı")
