"""
ClassRoom Manager Agent - Fayl idarəetmə modulu.
Master-dən faylları qəbul edir və faylları geri göndərir.
"""
from __future__ import annotations

import os
import base64
import logging
from pathlib import Path

from ..common.constants import FILE_CHUNK_SIZE, DEFAULT_FILE_SAVE_PATH

logger = logging.getLogger(__name__)


class FileHandler:
    """Fayl qəbulu və göndərməsi."""

    def __init__(self, save_path: str = None):
        self.save_path = Path(os.path.expanduser(save_path or DEFAULT_FILE_SAVE_PATH))
        self.save_path.mkdir(parents=True, exist_ok=True)
        self._receiving_files: dict[str, dict] = {}  # file_id -> {name, chunks, total}

    def start_receive(self, file_id: str, filename: str, total_chunks: int) -> None:
        """Fayl qəbuluna başlayır."""
        self._receiving_files[file_id] = {
            "name": filename,
            "chunks": {},
            "total": total_chunks,
        }
        logger.info(f"Fayl qəbulu başladı: {filename} ({total_chunks} chunk)")

    def receive_chunk(self, file_id: str, chunk_index: int, data: str) -> float:
        """
        Fayl parçasını qəbul edir.
        Returns: Tamamlanma faizi (0.0 - 1.0)
        """
        if file_id not in self._receiving_files:
            logger.warning(f"Naməlum fayl ID: {file_id}")
            return 0.0

        file_info = self._receiving_files[file_id]
        file_info["chunks"][chunk_index] = base64.b64decode(data)

        progress = len(file_info["chunks"]) / file_info["total"]
        return progress

    def complete_receive(self, file_id: str) -> str | None:
        """Fayl qəbulunu tamamlayır və faylı diskə yazır."""
        if file_id not in self._receiving_files:
            return None

        file_info = self._receiving_files.pop(file_id)
        filename = file_info["name"]
        filepath = self.save_path / filename

        # Eyni adlı fayl varsa nömrə əlavə et
        if filepath.exists():
            base = filepath.stem
            ext = filepath.suffix
            counter = 1
            while filepath.exists():
                filepath = self.save_path / f"{base}_{counter}{ext}"
                counter += 1

        try:
            with open(filepath, "wb") as f:
                for i in range(file_info["total"]):
                    if i in file_info["chunks"]:
                        f.write(file_info["chunks"][i])
            logger.info(f"Fayl saxlanıldı: {filepath}")
            return str(filepath)
        except IOError as e:
            logger.error(f"Fayl yazma xətası: {e}")
            return None

    def collect_files(self, directory: str = None) -> list[dict]:
        """
        Qovluqdakı faylları toplamaq üçün siyahı yaradır.
        Returns: [{"name": str, "data": str (base64), "size": int}]
        """
        collect_path = Path(os.path.expanduser(directory)) if directory else self.save_path

        if not collect_path.exists():
            logger.warning(f"Qovluq tapılmadı: {collect_path}")
            return []

        files = []
        for filepath in collect_path.iterdir():
            if filepath.is_file():
                try:
                    data = filepath.read_bytes()
                    files.append({
                        "name": filepath.name,
                        "data": base64.b64encode(data).decode("ascii"),
                        "size": len(data),
                    })
                except IOError as e:
                    logger.error(f"Fayl oxuma xətası ({filepath}): {e}")

        logger.info(f"{len(files)} fayl toplandı: {collect_path}")
        return files

    def prepare_file_chunks(self, filepath: str) -> list[dict] | None:
        """Faylı chunk-lara bölür göndərmə üçün."""
        path = Path(filepath)
        if not path.exists():
            logger.error(f"Fayl tapılmadı: {filepath}")
            return None

        chunks = []
        try:
            data = path.read_bytes()
            total = (len(data) + FILE_CHUNK_SIZE - 1) // FILE_CHUNK_SIZE

            for i in range(total):
                start = i * FILE_CHUNK_SIZE
                end = start + FILE_CHUNK_SIZE
                chunk_data = base64.b64encode(data[start:end]).decode("ascii")
                chunks.append({
                    "index": i,
                    "data": chunk_data,
                    "total": total,
                })

            return chunks
        except IOError as e:
            logger.error(f"Fayl oxuma xətası: {e}")
            return None
