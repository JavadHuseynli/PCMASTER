"""
ClassRoom Manager Agent - Ekran çəkmə modulu.
mss kitabxanası ilə ekran screenshot-u çəkir və JPEG formatında sıxır.
"""

import io
import base64
import logging
from PIL import Image
import mss

logger = logging.getLogger(__name__)


class ScreenCapture:
    """Ekran çəkmə və sıxılma sinfi."""

    def __init__(self, quality: int = 50, thumbnail_size: tuple = (320, 180)):
        self.quality = quality
        self.thumbnail_size = thumbnail_size
        self._sct = None

    def _get_sct(self) -> mss.mss:
        if self._sct is None:
            self._sct = mss.mss()
        return self._sct

    def capture_screenshot(self, as_thumbnail: bool = True) -> str:
        """
        Ekran screenshot-u çəkir.
        Returns: Base64 kodlanmış JPEG şəkil
        """
        try:
            sct = self._get_sct()
            monitor = sct.monitors[1]  # Əsas ekran
            screenshot = sct.grab(monitor)

            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

            if as_thumbnail:
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=self.quality, optimize=True)
            buffer.seek(0)

            return base64.b64encode(buffer.getvalue()).decode("ascii")

        except Exception as e:
            logger.error(f"Ekran çəkmə xətası: {e}")
            return ""

    def capture_full_screenshot(self, quality: int = 80) -> str:
        """Tam ölçülü ekran çəkir (demo rejimi üçün)."""
        try:
            sct = self._get_sct()
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)

            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            buffer.seek(0)

            return base64.b64encode(buffer.getvalue()).decode("ascii")

        except Exception as e:
            logger.error(f"Tam ekran çəkmə xətası: {e}")
            return ""

    def get_screen_size(self) -> tuple:
        """Ekran ölçülərini qaytarır."""
        try:
            sct = self._get_sct()
            monitor = sct.monitors[1]
            return monitor["width"], monitor["height"]
        except Exception:
            return 1920, 1080

    def close(self):
        """Resursları təmizləyir."""
        if self._sct:
            self._sct.close()
            self._sct = None
