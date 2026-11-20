from django.http import HttpRequest, HttpResponse

from apps.core.permissions import feature_permission_required
from apps.core.views.excel_view_helpers import (
    excel_export_response,
    handle_excel_import,
)
from apps.rumah.exports.excel_export import (
    export_rumah_to_excel,
    export_rumah_template_to_excel,
)
from apps.rumah.services.excel_import_service import import_rumah_from_excel


@feature_permission_required("rumah.view_rumah")
def export_rumah_excel(request: HttpRequest) -> HttpResponse:
    """Download all Rumah records as an Excel file."""
    buffer = export_rumah_to_excel()
    return excel_export_response(buffer, "master_rumah.xlsx")


@feature_permission_required("rumah.add_rumah")
def import_rumah_excel(request: HttpRequest) -> HttpResponse:
    """Import Rumah records from an uploaded Excel file."""
    return handle_excel_import(request, import_rumah_from_excel, "daftar_rumah")


@feature_permission_required("rumah.view_rumah")
def template_rumah_excel(request: HttpRequest) -> HttpResponse:
    """Download sample Excel template for Rumah import."""
    buffer = export_rumah_template_to_excel()
    return excel_export_response(buffer, "template_rumah.xlsx")
