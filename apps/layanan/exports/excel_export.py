import io

from apps.core.exports.excel_base import build_workbook
from apps.layanan.selectors.excel_selectors import (
    get_jenis_layanan_export_queryset,
    get_layanan_export_queryset,
)

LAYANAN_HEADERS = ["nama_layanan"]
JENIS_LAYANAN_HEADERS = ["layanan", "nama_jenis", "tarif"]


def export_layanan_to_excel() -> io.BytesIO:
    """Export all Layanan records to an in-memory .xlsx buffer."""
    queryset = get_layanan_export_queryset()
    rows = [[obj.nama_layanan] for obj in queryset]
    return build_workbook(LAYANAN_HEADERS, rows, sheet_title="Layanan")


def export_layanan_template_to_excel() -> io.BytesIO:
    """Generate an Excel template for Layanan import with sample data."""
    sample_rows = [
        ["AIR BERSIH"],
        ["WIFI"],
    ]
    return build_workbook(
        LAYANAN_HEADERS, sample_rows, sheet_title="Template Layanan"
    )


def export_jenis_layanan_to_excel() -> io.BytesIO:
    """Export all JenisLayanan records to an in-memory .xlsx buffer."""
    queryset = get_jenis_layanan_export_queryset()
    rows = [
        [obj.layanan.nama_layanan, obj.nama_jenis, obj.tarif]
        for obj in queryset
    ]
    return build_workbook(
        JENIS_LAYANAN_HEADERS, rows, sheet_title="Jenis Layanan"
    )


def export_jenis_layanan_template_to_excel() -> io.BytesIO:
    """Generate an Excel template for Jenis Layanan import with sample data."""
    sample_rows = [
        ["AIR BERSIH", "Paket Standar", 50000],
        ["WIFI", "WiFi Paket 100", 150000],
    ]
    return build_workbook(
        JENIS_LAYANAN_HEADERS, sample_rows, sheet_title="Template Jenis Layanan"
    )

