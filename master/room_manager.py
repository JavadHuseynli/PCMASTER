from __future__ import annotations
"""
ClassRoom Manager - Otaq idarəetmə modulu.
Otaqlar yaradılır, kompüterlər otaqlara təyin edilir.
Məlumatlar JSON faylında saxlanılır.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ROOMS_FILE = Path.home() / ".classroom_manager" / "rooms.json"


def _ensure_file():
    ROOMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not ROOMS_FILE.exists():
        ROOMS_FILE.write_text(json.dumps({
            "rooms": [],
            "assignments": {},
            "aliases": {},
        }, ensure_ascii=False, indent=2))


def load_rooms() -> dict:
    """Otaq məlumatlarını yükləyir."""
    _ensure_file()
    try:
        data = json.loads(ROOMS_FILE.read_text(encoding="utf-8"))
        # Əmin ol ki bütün açarlar var
        data.setdefault("rooms", [])
        data.setdefault("assignments", {})
        data.setdefault("aliases", {})
        return data
    except Exception as e:
        logger.error(f"Otaq faylı oxuma xətası: {e}")
        return {"rooms": [], "assignments": {}, "aliases": {}}


def save_rooms(data: dict):
    """Otaq məlumatlarını saxlayır."""
    _ensure_file()
    try:
        ROOMS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        logger.error(f"Otaq faylı yazma xətası: {e}")


def add_room(name: str) -> bool:
    data = load_rooms()
    if name in data["rooms"]:
        return False
    data["rooms"].append(name)
    save_rooms(data)
    return True


def remove_room(name: str) -> bool:
    data = load_rooms()
    if name not in data["rooms"]:
        return False
    data["rooms"].remove(name)
    # Bu otaqdakı təyinatları sil
    data["assignments"] = {
        k: v for k, v in data["assignments"].items() if v != name
    }
    save_rooms(data)
    return True


def rename_room(old_name: str, new_name: str) -> bool:
    data = load_rooms()
    if old_name not in data["rooms"] or new_name in data["rooms"]:
        return False
    idx = data["rooms"].index(old_name)
    data["rooms"][idx] = new_name
    # Təyinatları yenilə
    data["assignments"] = {
        k: (new_name if v == old_name else v)
        for k, v in data["assignments"].items()
    }
    save_rooms(data)
    return True


def assign_computer(agent_id: str, room_name: str):
    data = load_rooms()
    data["assignments"][agent_id] = room_name
    save_rooms(data)


def unassign_computer(agent_id: str):
    data = load_rooms()
    data["assignments"].pop(agent_id, None)
    save_rooms(data)


def get_room_for(agent_id: str) -> str | None:
    data = load_rooms()
    return data["assignments"].get(agent_id)


def get_computers_in_room(room_name: str) -> list[str]:
    data = load_rooms()
    return [k for k, v in data["assignments"].items() if v == room_name]


def set_alias(agent_id: str, alias: str):
    """Kompüterə ad (alias) verir."""
    data = load_rooms()
    data["aliases"][agent_id] = alias
    save_rooms(data)


def get_alias(agent_id: str) -> str | None:
    data = load_rooms()
    return data["aliases"].get(agent_id)


def get_all_aliases() -> dict[str, str]:
    data = load_rooms()
    return data.get("aliases", {})
