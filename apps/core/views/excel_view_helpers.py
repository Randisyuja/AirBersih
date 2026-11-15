import io
from typing import Callable

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from apps.core.dto.excel_dto import ImportResultDTO
from apps.core.exceptions.excel_exceptions import ExcelValidationError

XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def excel_export_response(buffer: io.BytesIO, filename: str) -> HttpResponse:
    """Wrap a BytesIO Excel buffer into an attachment HttpResponse."""
    response = HttpResponse(buffer.getvalue(), content_type=XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def handle_excel_import(
    request: HttpRequest,
    import_fn: Callable,
    redirect_url_name: str,
) -> HttpResponse:
    """Handle POST Excel upload, invoke import service, and set flash messages."""
    if request.method != "POST":
        return redirect(redirect_url_name)

    file_obj = request.FILES.get("file")
    if not file_obj:
        messages.error(request, "Pilih file Excel (.xlsx) terlebih dahulu.")
        return redirect(redirect_url_name)

    try:
        result: ImportResultDTO = import_fn(file_obj)
    except ExcelValidationError as exc:
        messages.error(request, f"Gagal import: {exc}")
        return redirect(redirect_url_name)

    summary = (
        f"Import selesai: {result.created_count} ditambahkan, "
        f"{result.updated_count} diperbarui, {result.skipped_count} dilewati."
    )
    if result.has_errors:
        first_errors = "; ".join(
            f"Baris {e.row_number} ({e.field}): {e.message}"
            for e in result.errors[:3]
        )
        messages.warning(request, f"{summary} Error: {first_errors}")
    else:
        messages.success(request, summary)

    return redirect(redirect_url_name)
