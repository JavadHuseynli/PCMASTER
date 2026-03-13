"""
ClassRoom Manager - Şəbəkə avto-tapma modulu.
Master UDP broadcast edir, Agent dinləyib Master-in IP-sini tapır.
"""
from __future__ import annotations

import asyncio
import json
import socket
import logging

logger = logging.getLogger(__name__)

DISCOVERY_PORT = 11101
DISCOVERY_MAGIC = "CLASSROOM_MASTER"
BROADCAST_INTERVAL = 3  # saniyə


class MasterBroadcaster:
    """Master öz varlığını şəbəkəyə broadcast edir."""

    def __init__(self, master_port: int = 11100, psk: str = ""):
        self.master_port = master_port
        self.psk = psk
        self._running = False
        self._sock = None

    async def start(self):
        """Broadcast döngüsünü başladır."""
        self._running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._sock.setblocking(False)

        message = json.dumps({
            "magic": DISCOVERY_MAGIC,
            "port": self.master_port,
            "psk_hash": self.psk[:4] if self.psk else "",  # Yalnız 4 simvol (tanıma üçün)
        }).encode("utf-8")

        logger.info(f"Master broadcast başladı: port {DISCOVERY_PORT}")

        while self._running:
            try:
                self._sock.sendto(message, ("<broadcast>", DISCOVERY_PORT))
            except Exception as e:
                logger.debug(f"Broadcast xətası: {e}")
            await asyncio.sleep(BROADCAST_INTERVAL)

    def stop(self):
        self._running = False
        if self._sock:
            self._sock.close()
            self._sock = None


class AgentDiscovery:
    """Agent şəbəkədə Master-i axtarır."""

    def __init__(self, timeout: float = 10):
        self.timeout = timeout

    async def find_master(self) -> dict | None:
        """
        Master-i şəbəkədə axtarır.
        Returns: {"host": "192.168.1.100", "port": 11100} və ya None
        """
        loop = asyncio.get_event_loop()
        result = None

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass  # Windows-da SO_REUSEPORT yoxdur
        sock.bind(("", DISCOVERY_PORT))
        sock.setblocking(False)

        logger.info(f"Master axtarılır (UDP port {DISCOVERY_PORT})...")

        try:
            deadline = loop.time() + self.timeout
            while loop.time() < deadline:
                try:
                    data, addr = await asyncio.wait_for(
                        loop.sock_recvfrom(sock, 1024),
                        timeout=min(2, deadline - loop.time()),
                    )
                    msg = json.loads(data.decode("utf-8"))
                    if msg.get("magic") == DISCOVERY_MAGIC:
                        result = {
                            "host": addr[0],
                            "port": msg.get("port", 11100),
                            "psk_hash": msg.get("psk_hash", ""),
                        }
                        logger.info(f"Master tapıldı: {addr[0]}:{result['port']}")
                        break
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.debug(f"Discovery oxuma xətası: {e}")
                    await asyncio.sleep(0.5)
        finally:
            sock.close()

        if result is None:
            logger.warning("Master tapılmadı (timeout)")
        return result


def find_master_sync(timeout: float = 10) -> dict | None:
    """Sinxron versiya — Agent başlanğıcında istifadə üçün."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except AttributeError:
        pass
    sock.bind(("", DISCOVERY_PORT))
    sock.settimeout(2)

    import time
    deadline = time.time() + timeout

    try:
        while time.time() < deadline:
            try:
                data, addr = sock.recvfrom(1024)
                msg = json.loads(data.decode("utf-8"))
                if msg.get("magic") == DISCOVERY_MAGIC:
                    logger.info(f"Master tapıldı (sync): {addr[0]}:{msg.get('port', 11100)}")
                    return {
                        "host": addr[0],
                        "port": msg.get("port", 11100),
                    }
            except socket.timeout:
                continue
            except Exception:
                continue
    finally:
        sock.close()

    return None
