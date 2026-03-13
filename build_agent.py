#!/usr/bin/env python3
"""
ClassRoom Manager Agent — EXE/APP build skripti.
PyInstaller ilə standalone paket yaradır.

İstifadə:
    python3 build_agent.py          # Cari OS üçün build
    python3 build_agent.py --onefile # Tək fayl
"""

import subprocess
import sys
import os
import platform
import shutil

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
AGENT_ENTRY = os.path.join(PROJECT_ROOT, "run_agent.py")
MASTER_ENTRY = os.path.join(PROJECT_ROOT, "run_master.py")
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")


def check_pyinstaller():
    """PyInstaller yüklü olub-olmadığını yoxlayır."""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("PyInstaller yüklü deyil. Yüklənir...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True


def build_agent(onefile=False):
    """Agent EXE/APP yaradır."""
    print("=" * 50)
    print("ClassRoom Manager Agent — Build başladı")
    print(f"OS: {platform.system()}")
    print(f"Python: {sys.version}")
    print("=" * 50)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "ClassRoomAgent",
        "--windowed",  # Konsol pəncərəsi göstərmə
        "--noconfirm",
        "--clean",
        "--add-data", f"{CONFIG_FILE}{os.pathsep}.",
    ]

    if onefile or "--onefile" in sys.argv:
        cmd.append("--onefile")

    # OS-a görə ikon
    if platform.system() == "Windows":
        icon_path = os.path.join(PROJECT_ROOT, "resources", "agent.ico")
        if os.path.exists(icon_path):
            cmd.extend(["--icon", icon_path])
    elif platform.system() == "Darwin":
        icon_path = os.path.join(PROJECT_ROOT, "resources", "agent.icns")
        if os.path.exists(icon_path):
            cmd.extend(["--icon", icon_path])

    # Hidden imports
    cmd.extend([
        "--hidden-import", "classroom_manager",
        "--hidden-import", "classroom_manager.agent",
        "--hidden-import", "classroom_manager.agent.main",
        "--hidden-import", "classroom_manager.agent.client",
        "--hidden-import", "classroom_manager.agent.screen_capture",
        "--hidden-import", "classroom_manager.agent.command_executor",
        "--hidden-import", "classroom_manager.agent.file_handler",
        "--hidden-import", "classroom_manager.agent.tray_icon",
        "--hidden-import", "classroom_manager.agent.autostart",
        "--hidden-import", "classroom_manager.common",
        "--hidden-import", "classroom_manager.common.config",
        "--hidden-import", "classroom_manager.common.constants",
        "--hidden-import", "classroom_manager.common.protocol",
        "--hidden-import", "classroom_manager.common.crypto",
        "--hidden-import", "classroom_manager.common.discovery",
        "--hidden-import", "mss",
        "--hidden-import", "PIL",
    ])

    cmd.append(AGENT_ENTRY)

    print(f"\nKomanda: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("BUILD UĞURLU!")
        if onefile or "--onefile" in sys.argv:
            if platform.system() == "Windows":
                exe_path = os.path.join(DIST_DIR, "ClassRoomAgent.exe")
            elif platform.system() == "Darwin":
                exe_path = os.path.join(DIST_DIR, "ClassRoomAgent")
            else:
                exe_path = os.path.join(DIST_DIR, "ClassRoomAgent")
            print(f"Fayl: {exe_path}")
        else:
            print(f"Qovluq: {os.path.join(DIST_DIR, 'ClassRoomAgent')}")
        print("=" * 50)
    else:
        print("\nBUILD XƏTASI!")
        sys.exit(1)


def build_master(onefile=False):
    """Master EXE/APP yaradır."""
    print("=" * 50)
    print("ClassRoom Manager Master — Build başladı")
    print("=" * 50)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "ClassRoomMaster",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data", f"{CONFIG_FILE}{os.pathsep}.",
    ]

    if onefile or "--onefile" in sys.argv:
        cmd.append("--onefile")

    cmd.extend([
        "--hidden-import", "classroom_manager",
        "--hidden-import", "classroom_manager.master",
        "--hidden-import", "classroom_manager.master.main",
        "--hidden-import", "classroom_manager.master.server",
        "--hidden-import", "classroom_manager.master.room_manager",
        "--hidden-import", "classroom_manager.master.ui",
        "--hidden-import", "classroom_manager.master.ui.main_window",
        "--hidden-import", "classroom_manager.master.ui.computer_widget",
        "--hidden-import", "classroom_manager.master.ui.toolbar",
        "--hidden-import", "classroom_manager.master.ui.dialogs",
        "--hidden-import", "classroom_manager.master.ui.icons",
        "--hidden-import", "classroom_manager.master.handlers",
        "--hidden-import", "classroom_manager.master.handlers.control",
        "--hidden-import", "classroom_manager.master.handlers.demo",
        "--hidden-import", "classroom_manager.master.handlers.file_transfer",
        "--hidden-import", "classroom_manager.master.handlers.monitor",
        "--hidden-import", "classroom_manager.agent.screen_capture",
        "--hidden-import", "classroom_manager.common",
        "--hidden-import", "classroom_manager.common.config",
        "--hidden-import", "classroom_manager.common.constants",
        "--hidden-import", "classroom_manager.common.protocol",
        "--hidden-import", "classroom_manager.common.crypto",
        "--hidden-import", "classroom_manager.common.discovery",
        "--hidden-import", "mss",
        "--hidden-import", "PIL",
    ])

    cmd.append(MASTER_ENTRY)

    print(f"\nKomanda: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode == 0:
        print("\nMASTER BUILD UĞURLU!")
        print(f"Qovluq: {os.path.join(DIST_DIR, 'ClassRoomMaster')}")


if __name__ == "__main__":
    check_pyinstaller()

    if "--master" in sys.argv:
        build_master("--onefile" in sys.argv)
    elif "--all" in sys.argv:
        build_agent("--onefile" in sys.argv)
        build_master("--onefile" in sys.argv)
    else:
        build_agent("--onefile" in sys.argv)

    print("\nİstifadə:")
    print("  python3 build_agent.py              # Agent build")
    print("  python3 build_agent.py --master      # Master build")
    print("  python3 build_agent.py --all         # Hər ikisi")
    print("  python3 build_agent.py --onefile     # Tək fayl EXE")
