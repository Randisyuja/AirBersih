"""PDF report generator for pembayaran (ADR 002 §1.6 - returns io.BytesIO)."""

import io
from typing import Any, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from apps.pembayaran.selectors.payment_selectors import get_total_pemasukan_tahunan
from apps.pembayaran.selectors.report_selectors import get_service_payment_matrix


def generate_laporan_pembayaran_pdf(
    layanan: str,
    tahun: int,
    data: Optional[List[List[Any]]] = None,
    total_pemasukan: Optional[int] = None,
) -> io.BytesIO:
    """
    Constructs a landscape A4 ReportLab PDF table and writes to in-memory BytesIO.
    Returns io.BytesIO buffer.
    """
    nama_layanan = (layanan or "").strip().upper()

    if data is None:
        data = [
            [
                "Nama Pelanggan",
                "Alamat Rumah",
                "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                "Jul", "Aug", "Sep", "Okt", "Nov", "Des",
            ],
        ]
        matrix_rows = get_service_payment_matrix(layanan=nama_layanan, tahun=tahun)
        for row in matrix_rows:
            nominals = row.get("nominal_bulan") or []
            status_list = row.get("status_bulan") or []
            cells = []
            for i in range(12):
                nom = nominals[i] if i < len(nominals) else 0
                st = status_list[i] if i < len(status_list) else ""
                if nom > 0:
                    cells.append(f"{nom:,.0f}".replace(",", "."))
                elif st == "Lunas":
                    cells.append("Lunas")
                else:
                    cells.append("-")
            data.append([row["pelanggan"], row["alamat"], *cells])

    if total_pemasukan is None:
        total_pemasukan = get_total_pemasukan_tahunan(nama_layanan, tahun)

    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=landscape(A4))

    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ])

    total_width = 9.5 * inch
    col_count = len(data[0]) if data else 14
    weights = [2.2, 1.6] + [1] * max(0, col_count - 2)
    total_weight = sum(weights)
    col_widths = [(w / total_weight) * total_width for w in weights]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(style)
    table.hAlign = "LEFT"

    styles = getSampleStyleSheet()
    title = Paragraph(
        f"Laporan Pembayaran {nama_layanan.capitalize()} {tahun}",
        styles["Heading1"],
    )

    total_text = Paragraph(
        f"<b>Total pemasukan tahun {tahun}:</b> "
        f"Rp {total_pemasukan:,.0f}".replace(",", "."),
        styles["Normal"],
    )

    pdf.build([
        title,
        Spacer(1, 12),
        table,
        Spacer(1, 16),
        total_text,
    ])

    buffer.seek(0)
    return buffer


# Alias for backward compatibility with existing tests
generate_pembayaran_pdf = generate_laporan_pembayaran_pdf
