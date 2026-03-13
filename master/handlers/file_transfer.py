"""
ClassRoom Manager Master - Fayl ötürmə handler.
Faylları agentlərə göndərir və agentlərdən toplayır.
"""
from __future__ import annotations

import asyncio
import uuid
import base64
import logging
from pathlib import Path

from ...common.constants import MessageType, FILE_CHUNK_SIZE

logger = logging.getLogger(__name__)


class FileTransferHandler:
    """Fayl göndərmə və toplama."""

    def __init__(self, server):
        self.server = server
        self._collect_path = Path.home() / ".classroom_manager" / "collected"
        self._collect_path.mkdir(parents=True, exist_ok=True)

    async def send_file(self, agent_ids: list[str], filepath: str):
        """Faylı seçilmiş agentlərə göndərir."""
        path = Path(filepath)
        if not path.exists():
            logger.error(f"Fayl tapılmadı: {filepath}")
            return

        file_id = str(uuid.uuid4())[:8]
        filename = path.name

        try:
            data = path.read_bytes()
        except IOError as e:
            logger.error(f"Fayl oxuma xətası: {e}")
            return

        total_chunks = (len(data) + FILE_CHUNK_SIZE - 1) // FILE_CHUNK_SIZE

        # FILE_TRANSFER başlat mesajı
        await self.server.send_to_selected(
            agent_ids, MessageType.FILE_TRANSFER, {
                "file_id": file_id,
                "filename": filename,
                "total_chunks": total_chunks,
                "file_size": len(data),
            }
        )

        # Chunk-ları göndər
        for i in range(total_chunks):
            start = i * FILE_CHUNK_SIZE
            end = start + FILE_CHUNK_SIZE
            chunk_data = base64.b64encode(data[start:end]).decode("ascii")

            await self.server.send_to_selected(
                agent_ids, MessageType.FILE_CHUNK, {
                    "file_id": file_id,
                    "chunk_index": i,
                    "data": chunk_data,
                }
            )
            # Şəbəkəyə yük verməmək üçün kiçik pauza
            await asyncio.sleep(0.01)

        # Tamamlandı mesajı
        await self.server.send_to_selected(
            agent_ids, MessageType.FILE_COMPLETE, {"file_id": file_id}
        )

        logger.info(f"Fayl göndərildi: {filename} → {len(agent_ids)} agent ({total_chunks} chunk)")

    async def collect_files(self, agent_ids: list[str]):
        """Agentlərdən faylları toplayır."""
        await self.server.send_to_selected(
            agent_ids, MessageType.COLLECT_FILE, {}
        )
        logger.info(f"Fayl toplama əmri göndərildi: {len(agent_ids)} agent")

    def save_collected_file(self, agent_hostname: str, filename: str, data: str):
        """Toplanmış faylı saxlayır."""
        agent_dir = self._collect_path / agent_hostname
        agent_dir.mkdir(parents=True, exist_ok=True)

        filepath = agent_dir / filename
        try:
            file_data = base64.b64decode(data)
            filepath.write_bytes(file_data)
            logger.info(f"Toplanmış fayl saxlanıldı: {filepath}")
        except Exception as e:
            logger.error(f"Fayl saxlama xətası: {e}")
