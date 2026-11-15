"""QR Code SVG generator for customer/member cards and thermal receipts (ADR 002 §1.6)."""

import io
from reportlab.graphics import renderSVG
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing


def generate_qr_svg_bytes(value: str, size: int = 160) -> io.BytesIO:
    """
    Generates an in-memory SVG QR code buffer for `value` using ReportLab QrCodeWidget.
    Returns io.BytesIO per ADR 002 §1.6.
    """
    clean_value = (value or "-").strip()
    qr_widget = qr.QrCodeWidget(clean_value)
    bounds = qr_widget.getBounds()
    width = max(bounds[2] - bounds[0], 1)
    height = max(bounds[3] - bounds[1], 1)

    drawing = Drawing(
        size,
        size,
        transform=[float(size) / width, 0, 0, float(size) / height, 0, 0],
    )
    drawing.add(qr_widget)

    svg_str = renderSVG.drawToString(drawing)
    buffer = io.BytesIO(
        svg_str.encode("utf-8") if isinstance(svg_str, str) else svg_str
    )
    buffer.seek(0)
    return buffer
