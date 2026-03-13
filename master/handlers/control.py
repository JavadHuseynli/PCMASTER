"""
ClassRoom Manager Master - İdarəetmə handler.
Kilidləmə, söndürmə, proqram açma əmrlərini agentlərə göndərir.
"""
from __future__ import annotations

import asyncio
import logging

from ...common.constants import MessageType

logger = logging.getLogger(__name__)


class ControlHandler:
    """Uzaqdan idarəetmə əmrləri."""

    def __init__(self, server):
        self.server = server

    async def lock_screens(self, agent_ids: list[str]):
        """Seçilmiş agentlərin ekranını kilidləyir."""
        await self.server.send_to_selected(agent_ids, MessageType.LOCK_SCREEN)
        logger.info(f"Ekran kilidi göndərildi: {len(agent_ids)} agent")

    async def unlock_screens(self, agent_ids: list[str]):
        """Seçilmiş agentlərin ekran kilidini açır."""
        await self.server.send_to_selected(agent_ids, MessageType.UNLOCK_SCREEN)
        logger.info(f"Ekran kilidi açıldı: {len(agent_ids)} agent")

    async def send_message(self, agent_ids: list[str], title: str, text: str):
        """Agentlərə mesaj göndərir."""
        await self.server.send_to_selected(
            agent_ids, MessageType.SEND_MESSAGE, {"title": title, "text": text}
        )
        logger.info(f"Mesaj göndərildi: {len(agent_ids)} agent")

    async def shutdown(self, agent_ids: list[str], delay: int = 30):
        """Agentləri söndürür."""
        await self.server.send_to_selected(
            agent_ids, MessageType.SHUTDOWN, {"delay": delay}
        )
        logger.info(f"Söndürmə əmri: {len(agent_ids)} agent, {delay}s sonra")

    async def restart(self, agent_ids: list[str], delay: int = 30):
        """Agentləri yenidən başladır."""
        await self.server.send_to_selected(
            agent_ids, MessageType.RESTART, {"delay": delay}
        )
        logger.info(f"Yenidən başlatma: {len(agent_ids)} agent, {delay}s sonra")

    async def run_program(self, agent_ids: list[str], program: str, args: list = None):
        """Agentlərdə proqram işə salır."""
        await self.server.send_to_selected(
            agent_ids, MessageType.RUN_PROGRAM, {"program": program, "args": args or []}
        )
        logger.info(f"Proqram əmri: {program} → {len(agent_ids)} agent")

    async def open_url(self, agent_ids: list[str], url: str):
        """Agentlərdə URL açır."""
        await self.server.send_to_selected(
            agent_ids, MessageType.OPEN_URL, {"url": url}
        )
        logger.info(f"URL əmri: {url} → {len(agent_ids)} agent")
