import io

from apps.core.exports.excel_base import build_workbook
from apps.rumah.selectors.excel_selectors import get_rumah_export_queryset

RUMAH_HEADERS = ["rt", "no_rumah"]


def export_rumah_to_excel() -> io.BytesIO:
    """Export all Rumah records to an in-memory .xlsx buffer."""
    queryset = get_rumah_export_queryset()
    rows = [[obj.rt, obj.no_rumah] for obj in queryset]
    return build_workbook(RUMAH_HEADERS, rows, sheet_title="Rumah")


def export_rumah_template_to_excel() -> io.BytesIO:
    """Generate an Excel template for Rumah import with sample data."""
    sample_rows = [
        ["05", "A1"],
        ["06", "B2"],
    ]
    return build_workbook(
        RUMAH_HEADERS, sample_rows, sheet_title="Template Rumah"
    )

