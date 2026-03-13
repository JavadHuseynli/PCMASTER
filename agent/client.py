"""
ClassRoom Manager Agent - Master-ə qoşulma və əlaqə idarəetməsi.
Asinxron TCP client: qeydiyyat, heartbeat, əmr qəbulu.
"""
from __future__ import annotations

import asyncio
import platform
import uuid
import logging
from datetime import datetime, timezone

from ..common.protocol import create_message, send_message, receive_message
from ..common.constants import MessageType, DEFAULT_HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT
from ..common.crypto import create_client_ssl_context, verify_pre_shared_key
from ..common.discovery import find_master_sync

logger = logging.getLogger(__name__)


class AgentClient:
    """Master server-ə qoşulan agent client."""

    def __init__(self, config: dict, message_callback=None):
        self.config = config
        self.agent_config = config.get("agent", {})
        self.security_config = config.get("security", {})

        self.master_host = self.agent_config.get("master_host", "")
        self.master_port = self.agent_config.get("master_port", 11100)
        self._auto_discover = not self.master_host or self.master_host in ("", "auto")
        self.heartbeat_interval = self.agent_config.get("heartbeat_interval", DEFAULT_HEARTBEAT_INTERVAL)

        self.agent_id = str(uuid.uuid4())[:8]
        self.hostname = platform.node()
        self.connected = False
        self.running = False

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._message_callback = message_callback
        self._reconnect_delay = 2

    async def connect(self) -> bool:
        """Master-ə qoşulur."""
        try:
            ssl_ctx = None
            if self.security_config.get("use_tls", False):
                ssl_ctx = create_client_ssl_context()

            self._reader, self._writer = await asyncio.open_connection(
                self.master_host, self.master_port, ssl=ssl_ctx
            )

            # Qeydiyyat mesajı göndər
            register_msg = create_message(
                MessageType.REGISTER,
                payload={
                    "hostname": self.hostname,
                    "os": platform.system(),
                    "os_version": platform.version(),
                    "username": self._get_username(),
                    "pre_shared_key": self.security_config.get("pre_shared_key", ""),
                },
                sender_id=self.agent_id,
            )
            await send_message(self._writer, register_msg)

            # Qeydiyyat cavabını gözlə
            response = await receive_message(self._reader)
            if response and response.get("type") == MessageType.REGISTER_ACK:
                if response.get("payload", {}).get("accepted", False):
                    self.connected = True
                    logger.info(f"Master-ə qoşuldu: {self.master_host}:{self.master_port}")
                    return True
                else:
                    reason = response.get("payload", {}).get("reason", "Naməlum")
                    logger.error(f"Qeydiyyat rədd edildi: {reason}")
                    return False

            logger.error("Qeydiyyat cavabı alınmadı")
            return False

        except (ConnectionRefusedError, OSError) as e:
            logger.error(f"Qoşulma xətası: {e}")
            return False

    async def disconnect(self):
        """Master-dən ayrılır."""
        self.connected = False
        self.running = False
        if self._writer:
            try:
                msg = create_message(MessageType.DISCONNECT, sender_id=self.agent_id)
                await send_message(self._writer, msg)
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None
        logger.info("Master-dən ayrıldı")

    async def run(self):
        """Əsas döngü: qoşulma, heartbeat, mesaj qəbulu."""
        self.running = True

        while self.running:
            if not self.connected:
                # Avto-tapma: Master IP-si bilinmirsə şəbəkədə axtar
                if self._auto_discover:
                    logger.info("Master şəbəkədə axtarılır...")
                    result = find_master_sync(timeout=8)
                    if result:
                        self.master_host = result["host"]
                        self.master_port = result["port"]
                        logger.info(f"Master tapıldı: {self.master_host}:{self.master_port}")
                    else:
                        logger.info(f"Master tapılmadı, {self._reconnect_delay}s sonra yenidən...")
                        await asyncio.sleep(self._reconnect_delay)
                        continue

                success = await self.connect()
                if not success:
                    logger.info(f"{self._reconnect_delay}s sonra yenidən cəhd ediləcək...")
                    await asyncio.sleep(self._reconnect_delay)
                    continue

            # Heartbeat və mesaj qəbulunu paralel işlət
            try:
                await asyncio.gather(
                    self._heartbeat_loop(),
                    self._receive_loop(),
                )
            except Exception as e:
                logger.error(f"Əlaqə xətası: {e}")
                self.connected = False
                if self._writer:
                    self._writer.close()
                    self._writer = None

    async def _heartbeat_loop(self):
        """Dövri heartbeat göndərir."""
        while self.connected and self.running:
            try:
                msg = create_message(MessageType.HEARTBEAT, sender_id=self.agent_id)
                await send_message(self._writer, msg)
                await asyncio.sleep(self.heartbeat_interval)
            except Exception:
                self.connected = False
                break

    async def _receive_loop(self):
        """Master-dən mesajları qəbul edir."""
        while self.connected and self.running:
            try:
                message = await receive_message(self._reader)
                if message is None:
                    logger.warning("Əlaqə kəsildi")
                    self.connected = False
                    break

                await self._handle_message(message)

            except Exception as e:
                logger.error(f"Mesaj qəbul xətası: {e}")
                self.connected = False
                break

    async def _handle_message(self, message: dict):
        """Gələn mesajı emal edir."""
        msg_type = message.get("type", "")
        logger.debug(f"Mesaj alındı: {msg_type}")

        if msg_type == MessageType.HEARTBEAT_ACK:
            pass  # Normal cavab
        elif self._message_callback:
            await self._message_callback(message)

    async def send(self, msg_type: str, payload: dict = None):
        """Master-ə mesaj göndərir."""
        if not self.connected or not self._writer:
            logger.warning("Qoşulu deyil, mesaj göndərilə bilmir")
            return
        msg = create_message(msg_type, payload=payload, sender_id=self.agent_id)
        await send_message(self._writer, msg)

    @staticmethod
    def _get_username() -> str:
        import os
        return os.getenv("USER") or os.getenv("USERNAME", "unknown")
