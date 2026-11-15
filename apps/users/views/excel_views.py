from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse

from apps.core.views.excel_view_helpers import (
    excel_export_response,
    handle_excel_import,
)
from apps.users.exports.excel_export import (
    export_kasir_to_excel,
    export_users_template_to_excel,
)
from apps.users.services.excel_import_service import import_kasir_from_excel


@login_required
def export_users_excel(request: HttpRequest) -> HttpResponse:
    """Download all Kasir records as an Excel file."""
    buffer = export_kasir_to_excel()
    return excel_export_response(buffer, "master_users.xlsx")


@login_required
def import_users_excel(request: HttpRequest) -> HttpResponse:
    """Import Kasir records from an uploaded Excel file."""
    return handle_excel_import(
        request, import_kasir_from_excel, "daftar_users"
    )


@login_required
def template_users_excel(request: HttpRequest) -> HttpResponse:
    """Download sample Excel template for Users / Kasir import."""
    buffer = export_users_template_to_excel()
    return excel_export_response(buffer, "template_users.xlsx")

