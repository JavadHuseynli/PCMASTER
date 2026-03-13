"""
ClassRoom Manager - Konfiqurasiya idarəetməsi.
JSON faylından oxuma/yazma.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from .constants import (
    DEFAULT_PORT,
    DEFAULT_SCREENSHOT_INTERVAL,
    DEFAULT_SCREENSHOT_QUALITY,
    DEFAULT_THUMBNAIL_WIDTH,
    DEFAULT_THUMBNAIL_HEIGHT,
    DEFAULT_DEMO_FPS,
    DEFAULT_DEMO_QUALITY,
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_FILE_SAVE_PATH,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "master": {
        "port": DEFAULT_PORT,
        "screenshot_interval": DEFAULT_SCREENSHOT_INTERVAL,
        "screenshot_quality": DEFAULT_SCREENSHOT_QUALITY,
        "thumbnail_size": [DEFAULT_THUMBNAIL_WIDTH, DEFAULT_THUMBNAIL_HEIGHT],
        "demo_fps": DEFAULT_DEMO_FPS,
        "demo_quality": DEFAULT_DEMO_QUALITY,
    },
    "agent": {
        "master_host": "192.168.1.100",
        "master_port": DEFAULT_PORT,
        "heartbeat_interval": DEFAULT_HEARTBEAT_INTERVAL,
        "auto_connect": True,
        "file_save_path": DEFAULT_FILE_SAVE_PATH,
    },
    "security": {
        "use_tls": False,
        "pre_shared_key": "sinif2024",
        "allowed_masters": [],
    },
}


def get_config_path() -> Path:
    """Konfiqurasiya faylının yolunu qaytarır."""
    # Əvvəlcə cari qovluqda axtarır, sonra ev qovluğunda
    local_path = Path("config.json")
    if local_path.exists():
        return local_path

    home_path = Path.home() / ".classroom_manager" / "config.json"
    return home_path


def load_config(config_path: str | Path = None) -> dict:
    """Konfiqurasiya faylını yükləyir. Fayl yoxdursa default yaradır."""
    if config_path is None:
        config_path = get_config_path()
    else:
        config_path = Path(config_path)

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            # Default dəyərləri əlavə et (əskik olanlar üçün)
            merged = _deep_merge(DEFAULT_CONFIG, config)
            logger.info(f"Konfiqurasiya yükləndi: {config_path}")
            return merged
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Konfiqurasiya oxuma xətası: {e}")
            return DEFAULT_CONFIG.copy()
    else:
        logger.info("Konfiqurasiya faylı tapılmadı, default istifadə olunur")
        save_config(DEFAULT_CONFIG, config_path)
        return DEFAULT_CONFIG.copy()


def save_config(config: dict, config_path: str | Path = None) -> bool:
    """Konfiqurasiyanı fayla yazır."""
    if config_path is None:
        config_path = get_config_path()
    else:
        config_path = Path(config_path)

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info(f"Konfiqurasiya saxlanıldı: {config_path}")
        return True
    except IOError as e:
        logger.error(f"Konfiqurasiya yazma xətası: {e}")
        return False


def _deep_merge(default: dict, override: dict) -> dict:
    """İki dict-i dərin birləşdirir. Override dəyərləri üstünlük qazanır."""
    result = default.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
