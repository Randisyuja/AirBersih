from django.http import HttpRequest, HttpResponse

from apps.core.permissions import feature_permission_required
from apps.core.views.excel_view_helpers import (
    excel_export_response,
    handle_excel_import,
)
from apps.pelanggan.exports.excel_export import (
    export_langganan_to_excel,
    export_langganan_template_to_excel,
    export_pelanggan_to_excel,
    export_pelanggan_template_to_excel,
)
from apps.pelanggan.services.excel_import_service import (
    import_langganan_from_excel,
    import_pelanggan_from_excel,
)


@feature_permission_required("pelanggan.view_pelanggan")
def export_pelanggan_excel(request: HttpRequest) -> HttpResponse:
    """Download all Pelanggan records as an Excel file."""
    buffer = export_pelanggan_to_excel()
    return excel_export_response(buffer, "master_pelanggan.xlsx")


@feature_permission_required("pelanggan.add_pelanggan")
def import_pelanggan_excel(request: HttpRequest) -> HttpResponse:
    """Import Pelanggan records from an uploaded Excel file."""
    return handle_excel_import(
        request, import_pelanggan_from_excel, "daftar_pelanggan"
    )


@feature_permission_required("pelanggan.view_pelanggan")
def template_pelanggan_excel(request: HttpRequest) -> HttpResponse:
    """Download sample Excel template for Pelanggan import."""
    buffer = export_pelanggan_template_to_excel()
    return excel_export_response(buffer, "template_pelanggan.xlsx")


@feature_permission_required("pelanggan.view_langganan")
def export_langganan_excel(request: HttpRequest) -> HttpResponse:
    """Download all Langganan records as an Excel file."""
    buffer = export_langganan_to_excel()
    return excel_export_response(buffer, "master_langganan.xlsx")


@feature_permission_required("pelanggan.add_langganan")
def import_langganan_excel(request: HttpRequest) -> HttpResponse:
    """Import Langganan records from an uploaded Excel file."""
    return handle_excel_import(
        request, import_langganan_from_excel, "daftar_langganan"
    )


@feature_permission_required("pelanggan.view_langganan")
def template_langganan_excel(request: HttpRequest) -> HttpResponse:
    """Download sample Excel template for Langganan import."""
    buffer = export_langganan_template_to_excel()
    return excel_export_response(buffer, "template_langganan.xlsx")
