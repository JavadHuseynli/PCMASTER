"""
ClassRoom Manager - QPainter ilə çəkilmiş professional ikonlar.
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QFont, QPainterPath
from PyQt6.QtCore import Qt, QRect, QRectF, QPointF


def _make_icon(draw_func, bg_color: str, size: int = 32) -> QIcon:
    """Ikon yaradır: rəngli fon + çəkim funksiyası."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Fon
    p.setBrush(QColor(bg_color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(1, 1, size - 2, size - 2, 7, 7)

    # İkon çəkimi
    pen = QPen(QColor("white"))
    pen.setWidth(2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    draw_func(p, size)
    p.end()

    return QIcon(pixmap)


def icon_monitor(size=32) -> QIcon:
    """Monitorinq — göz ikonu."""
    def draw(p: QPainter, s):
        cx, cy = s / 2, s / 2
        # Göz forması
        path = QPainterPath()
        path.moveTo(6, cy)
        path.cubicTo(10, cy - 6, s - 10, cy - 6, s - 6, cy)
        path.cubicTo(s - 10, cy + 6, 10, cy + 6, 6, cy)
        p.drawPath(path)
        # Bəbək
        p.setBrush(QColor("white"))
        p.drawEllipse(QPointF(cx, cy), 3.5, 3.5)
    return _make_icon(draw, "#238636", size)


def icon_demo_full(size=32) -> QIcon:
    """Demo tam ekran — monitor ikonu."""
    def draw(p: QPainter, s):
        # Monitor
        p.drawRoundedRect(6, 7, s - 12, s - 16, 2, 2)
        # Ayaq
        p.drawLine(int(s * 0.35), s - 7, int(s * 0.65), s - 7)
        p.drawLine(s // 2, s - 9, s // 2, s - 7)
    return _make_icon(draw, "#1f6feb", size)


def icon_demo_window(size=32) -> QIcon:
    """Demo pəncərə — pəncərə ikonu."""
    def draw(p: QPainter, s):
        p.drawRoundedRect(7, 8, s - 14, s - 14, 2, 2)
        # Başlıq xətti
        p.drawLine(7, 13, s - 7, 13)
        # Kiçik dairələr
        p.setBrush(QColor("white"))
        for i, x in enumerate([10, 14, 18]):
            p.drawEllipse(QPointF(x, 10.5), 1, 1)
    return _make_icon(draw, "#1a7f37", size)


def icon_lock(size=32) -> QIcon:
    """Kilidlə — kilid ikonu."""
    def draw(p: QPainter, s):
        cx = s / 2
        # Kilid gövdəsi
        p.drawRoundedRect(8, int(s * 0.45), s - 16, int(s * 0.35), 2, 2)
        # Kilid qolu (arc)
        path = QPainterPath()
        path.moveTo(11, int(s * 0.45))
        path.lineTo(11, int(s * 0.35))
        path.cubicTo(11, 8, s - 11, 8, s - 11, int(s * 0.35))
        path.lineTo(s - 11, int(s * 0.45))
        p.drawPath(path)
    return _make_icon(draw, "#9e6a03", size)


def icon_unlock(size=32) -> QIcon:
    """Kilidi aç — açıq kilid ikonu."""
    def draw(p: QPainter, s):
        cx = s / 2
        # Kilid gövdəsi
        p.drawRoundedRect(8, int(s * 0.45), s - 16, int(s * 0.35), 2, 2)
        # Açıq qol
        path = QPainterPath()
        path.moveTo(11, int(s * 0.45))
        path.lineTo(11, int(s * 0.35))
        path.cubicTo(11, 8, s - 11, 8, s - 11, int(s * 0.35))
        p.drawPath(path)
    return _make_icon(draw, "#238636", size)


def icon_message(size=32) -> QIcon:
    """Mesaj — söhbət balonu."""
    def draw(p: QPainter, s):
        # Balon
        p.drawRoundedRect(6, 7, s - 12, s - 16, 4, 4)
        # Quyruq
        p.drawLine(10, s - 9, 8, s - 5)
        # Xətlər (mətn)
        p.drawLine(10, 13, s - 10, 13)
        p.drawLine(10, 17, s - 14, 17)
    return _make_icon(draw, "#8957e5", size)


def icon_file_send(size=32) -> QIcon:
    """Fayl göndər — fayl + ox ikonu."""
    def draw(p: QPainter, s):
        # Fayl
        p.drawRect(9, 6, s - 18, s - 12)
        # Ox yuxarı
        cx = s / 2
        p.drawLine(int(cx), 10, int(cx), s - 10)
        p.drawLine(int(cx), 10, int(cx) - 4, 14)
        p.drawLine(int(cx), 10, int(cx) + 4, 14)
    return _make_icon(draw, "#1f6feb", size)


def icon_file_collect(size=32) -> QIcon:
    """Fayl topla — fayl + aşağı ox."""
    def draw(p: QPainter, s):
        # Fayl
        p.drawRect(9, 6, s - 18, s - 12)
        # Ox aşağı
        cx = s / 2
        p.drawLine(int(cx), 10, int(cx), s - 10)
        p.drawLine(int(cx), s - 10, int(cx) - 4, s - 14)
        p.drawLine(int(cx), s - 10, int(cx) + 4, s - 14)
    return _make_icon(draw, "#0d8a72", size)


def icon_run_program(size=32) -> QIcon:
    """Proqram aç — play üçbucağı."""
    def draw(p: QPainter, s):
        p.setBrush(QColor("white"))
        path = QPainterPath()
        path.moveTo(12, 8)
        path.lineTo(s - 8, s / 2)
        path.lineTo(12, s - 8)
        path.closeSubpath()
        p.drawPath(path)
    return _make_icon(draw, "#57606a", size)


def icon_open_url(size=32) -> QIcon:
    """URL aç — dünya kürəsi."""
    def draw(p: QPainter, s):
        cx, cy = s / 2, s / 2
        r = s / 2 - 6
        # Dairə
        p.drawEllipse(QPointF(cx, cy), r, r)
        # Üfüqi xətt
        p.drawLine(int(cx - r), int(cy), int(cx + r), int(cy))
        # Şaquli ellips
        p.drawEllipse(QPointF(cx, cy), r * 0.4, r)
    return _make_icon(draw, "#6e7681", size)


def icon_shutdown(size=32) -> QIcon:
    """Söndür — power ikonu."""
    def draw(p: QPainter, s):
        cx, cy = s / 2, s / 2
        r = s / 2 - 8
        # Arc (üst hissədə boşluq)
        p.drawArc(QRectF(cx - r, cy - r + 2, r * 2, r * 2), 50 * 16, 260 * 16)
        # Şaquli xətt
        p.drawLine(int(cx), 8, int(cx), int(cy + 2))
    return _make_icon(draw, "#da3633", size)


def icon_restart(size=32) -> QIcon:
    """Yenidən başlat — dövrə ox."""
    def draw(p: QPainter, s):
        cx, cy = s / 2, s / 2
        r = s / 2 - 8
        # Arc
        p.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2), 90 * 16, 270 * 16)
        # Ox ucu
        p.setBrush(QColor("white"))
        path = QPainterPath()
        path.moveTo(cx, cy - r - 3)
        path.lineTo(cx + 4, cy - r + 1)
        path.lineTo(cx - 4, cy - r + 1)
        path.closeSubpath()
        p.drawPath(path)
    return _make_icon(draw, "#bd561d", size)


def icon_select_all(size=32) -> QIcon:
    """Hamısını seç — checkbox ikonu."""
    def draw(p: QPainter, s):
        p.drawRoundedRect(8, 8, s - 16, s - 16, 3, 3)
        # Tick
        p.drawLine(11, int(s / 2), int(s / 2 - 1), s - 11)
        p.drawLine(int(s / 2 - 1), s - 11, s - 10, 11)
    return _make_icon(draw, "#57606a", size)


def icon_settings(size=32) -> QIcon:
    """Parametrlər — dişli çarx."""
    def draw(p: QPainter, s):
        cx, cy = s / 2, s / 2
        # Daxili dairə
        p.drawEllipse(QPointF(cx, cy), 4, 4)
        # Xarici dairə (dişli)
        p.drawEllipse(QPointF(cx, cy), 7, 7)
        # Dişlər (xətlər)
        import math
        for i in range(6):
            angle = math.radians(i * 60)
            x1 = cx + 7 * math.cos(angle)
            y1 = cy + 7 * math.sin(angle)
            x2 = cx + 10 * math.cos(angle)
            y2 = cy + 10 * math.sin(angle)
            p.drawLine(int(x1), int(y1), int(x2), int(y2))
    return _make_icon(draw, "#57606a", size)


def icon_remote_control(size=32) -> QIcon:
    """Uzaqdan müdaxilə — cursor ikonu."""
    def draw(p: QPainter, s):
        p.setBrush(QColor("white"))
        path = QPainterPath()
        path.moveTo(8, 8)
        path.lineTo(8, s - 8)
        path.lineTo(14, s - 14)
        path.lineTo(19, s - 7)
        path.lineTo(22, s - 9)
        path.lineTo(17, s - 16)
        path.lineTo(s - 8, s - 16)
        path.closeSubpath()
        p.drawPath(path)
    return _make_icon(draw, "#e3b341", size)


def icon_add_room(size=32) -> QIcon:
    """Otaq əlavə et — plus ikonu."""
    def draw(p: QPainter, s):
        cx, cy = s / 2, s / 2
        p.drawLine(int(cx), 10, int(cx), s - 10)
        p.drawLine(10, int(cy), s - 10, int(cy))
    return _make_icon(draw, "#238636", size)
