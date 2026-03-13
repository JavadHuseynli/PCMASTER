#!/usr/bin/env python3
"""
ClassRoom Manager — GUI Installer.
Progress bar ilə asılılıqları yükləyir və EXE yaradır.
"""

import sys
import os
import subprocess
import threading
import re

# Əvvəlcə tkinter ilə başlayırıq (əlavə asılılıq tələb etmir)
import tkinter as tk
from tkinter import ttk, messagebox

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD_SCRIPT = os.path.join(PROJECT_ROOT, "build_agent.py")


class InstallerApp:
    """GUI ilə quraşdırma pəncərəsi."""

    STEPS = [
        ("Python yoxlanılır...", 5),
        ("pip yenilənir...", 10),
        ("PyQt6 yüklənir...", 25),
        ("Pillow yüklənir...", 35),
        ("mss yüklənir...", 42),
        ("cryptography yüklənir...", 50),
        ("PyInstaller yüklənir...", 60),
        ("Agent EXE yaradılır...", 80),
        ("Master EXE yaradılır...", 95),
        ("Tamamlandı!", 100),
    ]

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ClassRoom Manager — Quraşdırma")
        self.root.geometry("550x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#0d1117")

        # Mərkəzə yerləşdir
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 275
        y = (self.root.winfo_screenheight() // 2) - 200
        self.root.geometry(f"550x400+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        # Başlıq
        title = tk.Label(
            self.root, text="ClassRoom Manager",
            font=("Helvetica", 22, "bold"),
            fg="#c9d1d9", bg="#0d1117",
        )
        title.pack(pady=(30, 5))

        subtitle = tk.Label(
            self.root, text="Quraşdırma Proqramı",
            font=("Helvetica", 12),
            fg="#8b949e", bg="#0d1117",
        )
        subtitle.pack(pady=(0, 25))

        # Status mətni
        self.status_label = tk.Label(
            self.root, text="Başlamaq üçün düyməni basın",
            font=("Helvetica", 11),
            fg="#c9d1d9", bg="#0d1117",
        )
        self.status_label.pack(pady=(0, 10))

        # Progress bar
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "green.Horizontal.TProgressbar",
            troughcolor="#161b22",
            background="#238636",
            thickness=25,
        )

        self.progress = ttk.Progressbar(
            self.root,
            style="green.Horizontal.TProgressbar",
            orient="horizontal",
            length=450,
            mode="determinate",
            maximum=100,
        )
        self.progress.pack(pady=(0, 5))

        # Faiz mətni
        self.percent_label = tk.Label(
            self.root, text="0%",
            font=("Helvetica", 14, "bold"),
            fg="#238636", bg="#0d1117",
        )
        self.percent_label.pack(pady=(0, 15))

        # Log sahəsi
        self.log_text = tk.Text(
            self.root,
            height=5,
            font=("Courier", 9),
            bg="#161b22", fg="#8b949e",
            relief="flat",
            borderwidth=0,
            wrap="word",
        )
        self.log_text.pack(padx=30, fill="x")
        self.log_text.config(state="disabled")

        # Düymələr
        btn_frame = tk.Frame(self.root, bg="#0d1117")
        btn_frame.pack(pady=(15, 0))

        self.install_btn = tk.Button(
            btn_frame, text="Quraşdır",
            font=("Helvetica", 12, "bold"),
            fg="white", bg="#238636",
            activebackground="#2ea043",
            activeforeground="white",
            relief="flat",
            padx=30, pady=8,
            cursor="hand2",
            command=self._start_install,
        )
        self.install_btn.pack(side="left", padx=5)

        self.close_btn = tk.Button(
            btn_frame, text="Bağla",
            font=("Helvetica", 12),
            fg="#c9d1d9", bg="#21262d",
            activebackground="#30363d",
            activeforeground="#c9d1d9",
            relief="flat",
            padx=30, pady=8,
            cursor="hand2",
            command=self.root.quit,
        )
        self.close_btn.pack(side="left", padx=5)

    def _log(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _set_progress(self, value, status=""):
        self.progress["value"] = value
        self.percent_label.config(text=f"{int(value)}%")
        if status:
            self.status_label.config(text=status)
        self.root.update_idletasks()

    def _run_cmd(self, cmd, desc=""):
        """Komandanı işlədir və nəticəni qaytarır."""
        self._log(f">> {desc or ' '.join(cmd[:3])}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=PROJECT_ROOT,
            )
            if result.returncode != 0:
                err = result.stderr.strip().split("\n")[-1] if result.stderr else "Unknown error"
                self._log(f"   XƏTA: {err}")
                return False
            return True
        except subprocess.TimeoutExpired:
            self._log("   XƏTA: Vaxt bitdi (timeout)")
            return False
        except Exception as e:
            self._log(f"   XƏTA: {e}")
            return False

    def _install_thread(self):
        """Quraşdırma prosesini ayrı thread-də işlədir."""
        python = sys.executable or "python"

        # 1. Python yoxla
        self._set_progress(5, "Python yoxlanılır...")
        self._log(f"Python: {sys.version}")

        # 2. pip yenilə
        self._set_progress(10, "pip yenilənir...")
        self._run_cmd([python, "-m", "pip", "install", "--upgrade", "pip", "-q"], "pip upgrade")

        # 3-7. Asılılıqlar
        deps = [
            ("PyQt6", 25),
            ("Pillow", 35),
            ("mss", 42),
            ("cryptography", 50),
            ("pyinstaller", 60),
        ]
        for dep_name, pct in deps:
            self._set_progress(pct, f"{dep_name} yüklənir...")
            ok = self._run_cmd(
                [python, "-m", "pip", "install", dep_name, "-q"],
                f"pip install {dep_name}",
            )
            if not ok:
                self._set_progress(pct, f"XƏTA: {dep_name} yüklənə bilmədi!")
                self._log(f"Quraşdırma dayandırıldı — {dep_name} yüklənmədi.")
                self.install_btn.config(state="normal", text="Yenidən Cəhd")
                return

        # 8. Agent EXE
        self._set_progress(65, "Agent EXE yaradılır... (bu bir az çəkə bilər)")
        self._log("Agent build başladı...")
        ok = self._run_cmd(
            [python, BUILD_SCRIPT, "--onefile"],
            "build Agent EXE",
        )
        if ok:
            self._set_progress(80, "Agent EXE hazırdır!")
            self._log("Agent EXE uğurla yaradıldı.")
        else:
            self._log("Agent build xətası — davam edilir...")

        # 9. Master EXE
        self._set_progress(85, "Master EXE yaradılır...")
        self._log("Master build başladı...")
        ok = self._run_cmd(
            [python, BUILD_SCRIPT, "--master", "--onefile"],
            "build Master EXE",
        )
        if ok:
            self._set_progress(95, "Master EXE hazırdır!")
            self._log("Master EXE uğurla yaradıldı.")
        else:
            self._log("Master build xətası.")

        # 10. Tamamlandı
        self._set_progress(100, "Quraşdırma tamamlandı!")
        self._log("")
        self._log("=" * 45)
        self._log("  TAMAMDIR!")
        self._log(f"  Agent:  dist/ClassRoomAgent")
        self._log(f"  Master: dist/ClassRoomMaster")
        self._log("=" * 45)

        self.install_btn.config(state="disabled")
        self.percent_label.config(fg="#3fb950")
        self.status_label.config(fg="#3fb950")

        messagebox.showinfo(
            "Quraşdırma Tamamlandı",
            "EXE faylları yaradıldı!\n\n"
            "dist/ClassRoomAgent — Şagird kompüterləri üçün\n"
            "dist/ClassRoomMaster — Müəllim kompüteri üçün",
        )

    def _start_install(self):
        self.install_btn.config(state="disabled", text="Quraşdırılır...")
        thread = threading.Thread(target=self._install_thread, daemon=True)
        thread.start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = InstallerApp()
    app.run()
