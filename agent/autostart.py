"""
ClassRoom Manager Agent - Avtomatik baslatma modulu.
OS-a uygun olaraq agent-in komputer acildiqda avtomatik baslamasini idarə edir.
"""

import sys
import os
import platform
import logging
import subprocess

logger = logging.getLogger(__name__)

APP_NAME = "ClassRoomManagerAgent"
PLIST_LABEL = "com.classroom.agent"

# EXE olaraq işlədikdə sys.executable özü EXE-dir
# Python ilə işlədikdə isə run_agent.py yolunu istifadə edirik
_FROZEN = getattr(sys, "frozen", False)
if _FROZEN:
    # PyInstaller EXE — birbaşa exe yolunu istifadə et
    EXE_PATH = sys.executable
    RUN_AGENT_PATH = EXE_PATH
    PYTHON_PATH = EXE_PATH
else:
    RUN_AGENT_PATH = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "run_agent.py")
    )
    PYTHON_PATH = sys.executable or "python3"


def _get_os() -> str:
    """Əməliyyat sistemini aşkarlayır."""
    system = platform.system()
    if system == "Darwin":
        return "macos"
    elif system == "Windows":
        return "windows"
    elif system == "Linux":
        return "linux"
    else:
        return "unknown"


# ---------------------------------------------------------------------------
# macOS — LaunchAgent plist
# ---------------------------------------------------------------------------

def _macos_plist_path() -> str:
    return os.path.expanduser(f"~/Library/LaunchAgents/{PLIST_LABEL}.plist")


def _macos_plist_content() -> str:
    if _FROZEN:
        program_args = f"""    <array>
        <string>{EXE_PATH}</string>
    </array>"""
    else:
        program_args = f"""    <array>
        <string>{PYTHON_PATH}</string>
        <string>{RUN_AGENT_PATH}</string>
    </array>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_LABEL}</string>
    <key>ProgramArguments</key>
{program_args}
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/{PLIST_LABEL}.out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/{PLIST_LABEL}.err.log</string>
</dict>
</plist>
"""


def _macos_install() -> bool:
    path = _macos_plist_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(_macos_plist_content())
        logger.info("macOS LaunchAgent yaradildi: %s", path)
        return True
    except Exception as e:
        logger.error("macOS autostart qurarkən xəta: %s", e)
        return False


def _macos_remove() -> bool:
    path = _macos_plist_path()
    try:
        if os.path.exists(path):
            # Əvvəlcə unload edək (xəta olsa da davam edirik)
            try:
                subprocess.run(
                    ["launchctl", "unload", path],
                    capture_output=True, timeout=5,
                )
            except Exception:
                pass
            os.remove(path)
            logger.info("macOS LaunchAgent silindi: %s", path)
        return True
    except Exception as e:
        logger.error("macOS autostart silərkən xəta: %s", e)
        return False


def _macos_is_installed() -> bool:
    return os.path.isfile(_macos_plist_path())


# ---------------------------------------------------------------------------
# Windows — Registry
# ---------------------------------------------------------------------------

_WIN_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _windows_install() -> bool:
    try:
        import winreg
        if _FROZEN:
            command = f'"{EXE_PATH}"'
        else:
            command = f'"{PYTHON_PATH}" "{RUN_AGENT_PATH}"'
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _WIN_REG_KEY, 0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        logger.info("Windows registry-yə əlavə edildi: %s", APP_NAME)
        return True
    except Exception as e:
        logger.error("Windows autostart qurarkən xəta: %s", e)
        return False


def _windows_remove() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _WIN_REG_KEY, 0, winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        logger.info("Windows registry-dən silindi: %s", APP_NAME)
        return True
    except Exception as e:
        logger.error("Windows autostart silərkən xəta: %s", e)
        return False


def _windows_is_installed() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _WIN_REG_KEY, 0, winreg.KEY_QUERY_VALUE
        )
        try:
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Linux — .desktop file
# ---------------------------------------------------------------------------

def _linux_desktop_path() -> str:
    return os.path.expanduser(f"~/.config/autostart/{APP_NAME}.desktop")


def _linux_desktop_content() -> str:
    if _FROZEN:
        exec_cmd = EXE_PATH
    else:
        exec_cmd = f"python3 {RUN_AGENT_PATH}"
    return f"""[Desktop Entry]
Type=Application
Name=ClassRoom Manager Agent
Exec={exec_cmd}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=ClassRoom Manager Agent avtomatik baslatma
"""


def _linux_install() -> bool:
    path = _linux_desktop_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(_linux_desktop_content())
        os.chmod(path, 0o755)
        logger.info("Linux .desktop faylı yaradıldı: %s", path)
        return True
    except Exception as e:
        logger.error("Linux autostart qurarkən xəta: %s", e)
        return False


def _linux_remove() -> bool:
    path = _linux_desktop_path()
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.info("Linux .desktop faylı silindi: %s", path)
        return True
    except Exception as e:
        logger.error("Linux autostart silərkən xəta: %s", e)
        return False


def _linux_is_installed() -> bool:
    return os.path.isfile(_linux_desktop_path())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_HANDLERS = {
    "macos": (_macos_install, _macos_remove, _macos_is_installed),
    "windows": (_windows_install, _windows_remove, _windows_is_installed),
    "linux": (_linux_install, _linux_remove, _linux_is_installed),
}


def install_autostart() -> bool:
    """Avtomatik baslatmani qurur. Ugurlu olduqda True qaytarir."""
    current_os = _get_os()
    handler = _HANDLERS.get(current_os)
    if handler is None:
        logger.warning("Dəstəklənməyən OS: %s", current_os)
        return False
    return handler[0]()


def remove_autostart() -> bool:
    """Avtomatik baslatmani silir. Ugurlu olduqda True qaytarir."""
    current_os = _get_os()
    handler = _HANDLERS.get(current_os)
    if handler is None:
        logger.warning("Dəstəklənməyən OS: %s", current_os)
        return False
    return handler[1]()


def is_installed() -> bool:
    """Avtomatik baslatma qurulubsa True qaytarir."""
    current_os = _get_os()
    handler = _HANDLERS.get(current_os)
    if handler is None:
        return False
    return handler[2]()
