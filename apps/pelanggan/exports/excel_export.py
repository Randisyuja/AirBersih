import io

from apps.core.exports.excel_base import build_workbook
from apps.pelanggan.selectors.excel_selectors import (
    get_langganan_export_queryset,
    get_pelanggan_export_queryset,
)

PELANGGAN_HEADERS = ["nama", "no_hp", "no_rumah"]
LANGGANAN_HEADERS = ["pelanggan", "jenis_layanan", "harga", "aktif"]


def export_pelanggan_to_excel() -> io.BytesIO:
    """Export all Pelanggan records to an in-memory .xlsx buffer."""
    queryset = get_pelanggan_export_queryset()
    rows = [
        [
            obj.nama,
            obj.no_hp or "",
            obj.rumah.no_rumah if obj.rumah else "",
        ]
        for obj in queryset
    ]
    return build_workbook(PELANGGAN_HEADERS, rows, sheet_title="Pelanggan")


def export_pelanggan_template_to_excel() -> io.BytesIO:
    """Generate an Excel template for Pelanggan import with sample data."""
    sample_rows = [
        ["Budi Santoso", "081234567890", "A1"],
        ["Siti Aminah", "082345678901", "B2"],
    ]
    return build_workbook(
        PELANGGAN_HEADERS, sample_rows, sheet_title="Template Pelanggan"
    )


def export_langganan_to_excel() -> io.BytesIO:
    """Export all Langganan records to an in-memory .xlsx buffer."""
    queryset = get_langganan_export_queryset()
    rows = [
        [
            obj.pelanggan.nama,
            obj.jenis_layanan.nama_jenis,
            obj.harga,
            "Ya" if obj.aktif else "Tidak",
        ]
        for obj in queryset
    ]
    return build_workbook(LANGGANAN_HEADERS, rows, sheet_title="Langganan")


def export_langganan_template_to_excel() -> io.BytesIO:
    """Generate an Excel template for Langganan import with sample data."""
    sample_rows = [
        ["Budi Santoso", "Paket Standar", 50000, "Ya"],
        ["Siti Aminah", "WiFi Paket 100", 150000, "Ya"],
    ]
    return build_workbook(
        LANGGANAN_HEADERS, sample_rows, sheet_title="Template Langganan"
    )

