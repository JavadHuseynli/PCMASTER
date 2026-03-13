"""
ClassRoom Manager Agent - Əmr icraçısı.
Master-dən gələn əmrləri icra edir: kilidləmə, söndürmə, proqram açma və s.
"""

import subprocess
import platform
import logging
import webbrowser
import os

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Uzaqdan idarəetmə əmrlərini icra edən sinif."""

    def __init__(self):
        self.system = platform.system().lower()

    def shutdown(self, delay: int = 30) -> bool:
        """Kompüteri söndürür."""
        try:
            if self.system == "windows":
                subprocess.Popen(["shutdown", "/s", "/t", str(delay)])
            elif self.system == "darwin":
                # macOS — osascript ilə söndürmə (sudo tələb etmir)
                minutes = max(1, delay // 60)
                script = f'''
                    display dialog "Kompüter {minutes} dəqiqə sonra söndürüləcək!" ¬
                        with title "ClassRoom Manager" ¬
                        buttons {{"OK"}} default button "OK" ¬
                        giving up after {delay}
                '''
                subprocess.Popen(["osascript", "-e", script])
                subprocess.Popen(
                    ["osascript", "-e",
                     'tell application "System Events" to shut down'],
                )
            else:  # linux
                subprocess.Popen(["shutdown", "-h", f"+{delay // 60 or 1}"])
            logger.info(f"Söndürmə əmri verildi ({delay}s sonra)")
            return True
        except Exception as e:
            logger.error(f"Söndürmə xətası: {e}")
            return False

    def restart(self, delay: int = 30) -> bool:
        """Kompüteri yenidən başladır."""
        try:
            if self.system == "windows":
                subprocess.Popen(["shutdown", "/r", "/t", str(delay)])
            elif self.system == "darwin":
                subprocess.Popen(
                    ["osascript", "-e",
                     'tell application "System Events" to restart'],
                )
            else:  # linux
                subprocess.Popen(["shutdown", "-r", f"+{delay // 60 or 1}"])
            logger.info(f"Yenidən başlatma əmri verildi ({delay}s sonra)")
            return True
        except Exception as e:
            logger.error(f"Yenidən başlatma xətası: {e}")
            return False

    def cancel_shutdown(self) -> bool:
        """Planlanmış söndürmə/yenidən başlatmanı ləğv edir."""
        try:
            if self.system == "windows":
                subprocess.Popen(["shutdown", "/a"])
            elif self.system == "darwin":
                subprocess.Popen(["killall", "shutdown"], stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["shutdown", "-c"])
            logger.info("Söndürmə ləğv edildi")
            return True
        except Exception as e:
            logger.error(f"Söndürmə ləğv xətası: {e}")
            return False

    def run_program(self, program_path: str, args: list = None) -> bool:
        """Proqram işə salır."""
        try:
            if self.system == "darwin" and program_path.endswith(".app"):
                # macOS .app bundle — open ilə aç
                cmd = ["open", "-a", program_path] + (args or [])
            elif self.system == "darwin" and not os.path.sep in program_path:
                # macOS — ad ilə proqram açma (məs: "Safari", "TextEdit")
                cmd = ["open", "-a", program_path] + (args or [])
            else:
                cmd = [program_path] + (args or [])
            subprocess.Popen(cmd, shell=False)
            logger.info(f"Proqram işə salındı: {program_path}")
            return True
        except FileNotFoundError:
            logger.error(f"Proqram tapılmadı: {program_path}")
            return False
        except Exception as e:
            logger.error(f"Proqram işə salma xətası: {e}")
            return False

    def open_url(self, url: str) -> bool:
        """Brauzerdə URL açır."""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
            logger.info(f"URL açıldı: {url}")
            return True
        except Exception as e:
            logger.error(f"URL açma xətası: {e}")
            return False

    def remote_mouse(self, event_data: dict) -> bool:
        """Uzaqdan mouse hadisəsini icra edir."""
        try:
            action = event_data.get("action", "")
            x = event_data.get("x", 0)
            y = event_data.get("y", 0)
            button = event_data.get("button", "left")

            if self.system == "darwin":
                if action == "click":
                    btn = "1" if button == "left" else "2"
                    script = f'''
                        tell application "System Events"
                            click at {{{x}, {y}}}
                        end tell
                    '''
                    # cliclick daha dəqiq işləyir (brew install cliclick)
                    subprocess.Popen(
                        ["cliclick", f"{'c' if button == 'left' else 'rc'}:{x},{y}"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                elif action == "double_click":
                    subprocess.Popen(
                        ["cliclick", f"dc:{x},{y}"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            elif self.system == "windows":
                # PowerShell ilə mouse klik
                ps_btn = "Left" if button == "left" else "Right"
                script = f'''
                    Add-Type -AssemblyName System.Windows.Forms
                    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x},{y})
                    $signature = '[DllImport("user32.dll")] public static extern void mouse_event(int dwFlags, int dx, int dy, int cButtons, int dwExtraInfo);'
                    $type = Add-Type -MemberDefinition $signature -Name "Win32MouseEvent" -Namespace "Win32" -PassThru
                '''
                if action == "click":
                    if button == "left":
                        script += '$type::mouse_event(0x0002, 0, 0, 0, 0); $type::mouse_event(0x0004, 0, 0, 0, 0)'
                    else:
                        script += '$type::mouse_event(0x0008, 0, 0, 0, 0); $type::mouse_event(0x0010, 0, 0, 0, 0)'
                subprocess.Popen(["powershell", "-Command", script],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:  # linux
                subprocess.Popen(
                    ["xdotool", "mousemove", str(x), str(y),
                     "click", "1" if button == "left" else "3"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )

            logger.info(f"Mouse {action}: ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Mouse əmr xətası: {e}")
            return False

    def remote_key(self, event_data: dict) -> bool:
        """Uzaqdan klaviatura hadisəsini icra edir."""
        try:
            action = event_data.get("action", "")
            key = event_data.get("key", "")

            if action != "press" or not key:
                return True

            if self.system == "darwin":
                subprocess.Popen(
                    ["cliclick", f"t:{key}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif self.system == "windows":
                script = f'''
                    Add-Type -AssemblyName System.Windows.Forms
                    [System.Windows.Forms.SendKeys]::SendWait("{key}")
                '''
                subprocess.Popen(["powershell", "-Command", script],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:  # linux
                subprocess.Popen(
                    ["xdotool", "type", "--", key],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )

            logger.info(f"Key {action}: {key}")
            return True
        except Exception as e:
            logger.error(f"Key əmr xətası: {e}")
            return False

    def get_system_info(self) -> dict:
        """Sistem məlumatlarını qaytarır."""
        return {
            "hostname": platform.node(),
            "os": platform.system(),
            "os_version": platform.version(),
            "platform": platform.platform(),
            "username": os.getenv("USER") or os.getenv("USERNAME", "unknown"),
        }
