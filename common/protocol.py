"""
ClassRoom Manager - Şəbəkə protokolu.
JSON əsaslı mesajlaşma sistemi: göndərmə və qəbul funksiyaları.
"""

from __future__ import annotations

import json
import struct
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

HEADER_FORMAT = "!I"  # 4 bayt, unsigned int, network byte order
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


def create_message(msg_type: str, payload: dict = None, sender_id: str = "") -> dict:
    """Standart mesaj strukturu yaradır."""
    return {
        "type": msg_type,
        "payload": payload or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sender_id": sender_id,
    }


def encode_message(message: dict) -> bytes:
    """Mesajı baytlara çevirir: [4 bayt uzunluq][JSON data]"""
    data = json.dumps(message, ensure_ascii=False).encode("utf-8")
    header = struct.pack(HEADER_FORMAT, len(data))
    return header + data


def decode_message(data: bytes) -> dict:
    """Baytları mesaja çevirir."""
    return json.loads(data.decode("utf-8"))


async def send_message(writer: asyncio.StreamWriter, message: dict) -> None:
    """Asinxron mesaj göndərmə."""
    try:
        encoded = encode_message(message)
        writer.write(encoded)
        await writer.drain()
    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        logger.error(f"Mesaj göndərmə xətası: {e}")
        raise


async def receive_message(reader: asyncio.StreamReader) -> Optional[dict]:
    """Asinxron mesaj qəbulu. Əlaqə kəsilərsə None qaytarır."""
    try:
        header_data = await reader.readexactly(HEADER_SIZE)
        if not header_data:
            return None

        (msg_length,) = struct.unpack(HEADER_FORMAT, header_data)

        if msg_length > 50 * 1024 * 1024:  # 50MB limit
            logger.warning(f"Həddən böyük mesaj: {msg_length} bayt")
            return None

        data = await reader.readexactly(msg_length)
        return decode_message(data)

    except asyncio.IncompleteReadError:
        logger.debug("Əlaqə kəsildi (incomplete read)")
        return None
    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        logger.error(f"Mesaj qəbul xətası: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode xətası: {e}")
        return None
