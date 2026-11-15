import io

from apps.core.exports.excel_base import build_workbook
from apps.users.selectors.excel_selectors import get_kasir_export_queryset

KASIR_HEADERS = [
    "username",
    "first_name",
    "last_name",
    "email",
    "no_hp",
    "is_active",
]


def export_kasir_to_excel() -> io.BytesIO:
    """Export all Kasir records to an in-memory .xlsx buffer."""
    queryset = get_kasir_export_queryset()
    rows = [
        [
            obj.username,
            obj.first_name,
            obj.last_name,
            obj.email,
            obj.no_hp or "",
            "Ya" if obj.is_active else "Tidak",
        ]
        for obj in queryset
    ]
    return build_workbook(KASIR_HEADERS, rows, sheet_title="Kasir")


def export_users_template_to_excel() -> io.BytesIO:
    """Generate an Excel template for Users/Kasir import with sample data."""
    sample_rows = [
        ["kasir01", "Ahmad", "Dahlan", "ahmad@example.com", "081298765432", "Ya"],
        ["kasir02", "Dewi", "Sartika", "dewi@example.com", "081234567899", "Ya"],
    ]
    return build_workbook(
        KASIR_HEADERS, sample_rows, sheet_title="Template Kasir"
    )


export_users_to_excel = export_kasir_to_excel
export_kasir_template_to_excel = export_users_template_to_excel

