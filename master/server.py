"""
ClassRoom Manager Master - TCP Server.
Agentləri dinləyir, qeydiyyat edir, mesajları yönləndirir.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

from ..common.protocol import create_message, send_message, receive_message
from ..common.constants import MessageType, HEARTBEAT_TIMEOUT
from ..common.crypto import create_server_ssl_context, verify_pre_shared_key

logger = logging.getLogger(__name__)


@dataclass
class AgentInfo:
    """Qoşulmuş agent haqqında məlumat."""
    agent_id: str
    hostname: str
    os: str
    os_version: str
    username: str
    ip_address: str
    port: int
    reader: asyncio.StreamReader = field(repr=False)
    writer: asyncio.StreamWriter = field(repr=False)
    connected_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    last_screenshot: str = ""  # base64


class MasterServer:
    """TCP server — agentləri dinləyir və idarə edir."""

    def __init__(self, config: dict, on_agent_connected=None, on_agent_disconnected=None,
                 on_screenshot=None, on_message=None):
        self.config = config
        self.master_config = config.get("master", {})
        self.security_config = config.get("security", {})

        self.port = self.master_config.get("port", 11100)
        self.agents: dict[str, AgentInfo] = {}

        # Callback-lər
        self._on_agent_connected = on_agent_connected
        self._on_agent_disconnected = on_agent_disconnected
        self._on_screenshot = on_screenshot
        self._on_message = on_message

        self._server: asyncio.Server | None = None
        self.running = False

    async def start(self):
        """Serveri başladır."""
        ssl_ctx = None
        if self.security_config.get("use_tls", False):
            ssl_ctx = create_server_ssl_context()

        self._server = await asyncio.start_server(
            self._handle_client, "0.0.0.0", self.port, ssl=ssl_ctx
        )
        self.running = True
        logger.info(f"Server başladı: 0.0.0.0:{self.port}")

        # Heartbeat yoxlama döngüsünü başlat
        asyncio.create_task(self._check_heartbeats())

        async with self._server:
            await self._server.serve_forever()

    async def stop(self):
        """Serveri dayandırır."""
        self.running = False
        # Bütün agentlərə DISCONNECT göndər
        for agent in list(self.agents.values()):
            try:
                msg = create_message(MessageType.DISCONNECT)
                await send_message(agent.writer, msg)
                agent.writer.close()
            except Exception:
                pass
        self.agents.clear()

        if self._server:
            self._server.close()
            await self._server.wait_closed()
        logger.info("Server dayandırıldı")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Yeni agent bağlantısını emal edir."""
        addr = writer.get_extra_info("peername")
        logger.info(f"Yeni bağlantı: {addr}")

        agent_id = None
        try:
            # Qeydiyyat mesajını gözlə
            message = await asyncio.wait_for(receive_message(reader), timeout=10)
            if not message or message.get("type") != MessageType.REGISTER:
                logger.warning(f"Yanlış qeydiyyat mesajı: {addr}")
                writer.close()
                return

            payload = message.get("payload", {})
            agent_id = message.get("sender_id", "")

            # Pre-shared key yoxla
            psk = self.security_config.get("pre_shared_key", "")
            if psk:
                received_key = payload.get("pre_shared_key", "")
                if not verify_pre_shared_key(received_key, psk):
                    ack = create_message(MessageType.REGISTER_ACK, {
                        "accepted": False, "reason": "Yanlış açar"
                    })
                    await send_message(writer, ack)
                    writer.close()
                    logger.warning(f"Açar rədd edildi: {addr}")
                    return

            # Agent-i qeydiyyatdan keçir
            agent = AgentInfo(
                agent_id=agent_id,
                hostname=payload.get("hostname", "unknown"),
                os=payload.get("os", "unknown"),
                os_version=payload.get("os_version", ""),
                username=payload.get("username", ""),
                ip_address=addr[0] if addr else "",
                port=addr[1] if addr else 0,
                reader=reader,
                writer=writer,
            )
            self.agents[agent_id] = agent

            # Qəbul cavabı
            ack = create_message(MessageType.REGISTER_ACK, {"accepted": True})
            await send_message(writer, ack)

            logger.info(f"Agent qeydiyyatdan keçdi: {agent.hostname} ({agent_id})")
            if self._on_agent_connected:
                self._on_agent_connected(agent)

            # Mesaj qəbul döngüsü
            while self.running:
                msg = await receive_message(reader)
                if msg is None:
                    break
                await self._process_agent_message(agent_id, msg)

        except asyncio.TimeoutError:
            logger.warning(f"Qeydiyyat timeout: {addr}")
        except Exception as e:
            logger.error(f"Client emal xətası: {e}")
        finally:
            if agent_id and agent_id in self.agents:
                removed = self.agents.pop(agent_id)
                logger.info(f"Agent ayrıldı: {removed.hostname} ({agent_id})")
                if self._on_agent_disconnected:
                    self._on_agent_disconnected(removed)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _process_agent_message(self, agent_id: str, message: dict):
        """Agent-dən gələn mesajı emal edir."""
        msg_type = message.get("type", "")
        payload = message.get("payload", {})

        if agent_id not in self.agents:
            return

        agent = self.agents[agent_id]

        if msg_type == MessageType.HEARTBEAT:
            agent.last_heartbeat = time.time()
            ack = create_message(MessageType.HEARTBEAT_ACK)
            await send_message(agent.writer, ack)

        elif msg_type == MessageType.SCREENSHOT:
            image_data = payload.get("image", "")
            if image_data:
                agent.last_screenshot = image_data
                if self._on_screenshot:
                    self._on_screenshot(agent_id, image_data)

        elif self._on_message:
            self._on_message(agent_id, message)

    async def send_to_agent(self, agent_id: str, msg_type: str, payload: dict = None):
        """Müəyyən agentə mesaj göndərir."""
        if agent_id not in self.agents:
            logger.warning(f"Agent tapılmadı: {agent_id}")
            return
        agent = self.agents[agent_id]
        msg = create_message(msg_type, payload=payload)
        try:
            await send_message(agent.writer, msg)
        except Exception as e:
            logger.error(f"Göndərmə xətası ({agent.hostname}): {e}")

    async def send_to_all(self, msg_type: str, payload: dict = None):
        """Bütün agentlərə mesaj göndərir."""
        for agent_id in list(self.agents.keys()):
            await self.send_to_agent(agent_id, msg_type, payload)

    async def send_to_selected(self, agent_ids: list[str], msg_type: str, payload: dict = None):
        """Seçilmiş agentlərə mesaj göndərir."""
        for agent_id in agent_ids:
            await self.send_to_agent(agent_id, msg_type, payload)

    async def _check_heartbeats(self):
        """Agentlərin canlılığını yoxlayır."""
        while self.running:
            await asyncio.sleep(HEARTBEAT_TIMEOUT)
            now = time.time()
            for agent_id, agent in list(self.agents.items()):
                if now - agent.last_heartbeat > HEARTBEAT_TIMEOUT:
                    logger.warning(f"Heartbeat timeout: {agent.hostname}")
                    try:
                        agent.writer.close()
                    except Exception:
                        pass

    def get_agent_list(self) -> list[dict]:
        """Bütün qoşulmuş agentlərin siyahısını qaytarır."""
        return [
            {
                "agent_id": a.agent_id,
                "hostname": a.hostname,
                "os": a.os,
                "username": a.username,
                "ip_address": a.ip_address,
                "connected_at": a.connected_at,
            }
            for a in self.agents.values()
        ]
