from django.http import HttpRequest, HttpResponse

from apps.core.permissions import feature_permission_required
from apps.core.views.excel_view_helpers import (
    excel_export_response,
    handle_excel_import,
)
from apps.layanan.exports.excel_export import (
    export_jenis_layanan_to_excel,
    export_jenis_layanan_template_to_excel,
    export_layanan_to_excel,
    export_layanan_template_to_excel,
)
from apps.layanan.services.excel_import_service import (
    import_jenis_layanan_from_excel,
    import_layanan_from_excel,
)


@feature_permission_required("layanan.view_layanan")
def export_layanan_excel(request: HttpRequest) -> HttpResponse:
    """Download all Layanan records as an Excel file."""
    buffer = export_layanan_to_excel()
    return excel_export_response(buffer, "master_layanan.xlsx")


@feature_permission_required("layanan.add_layanan")
def import_layanan_excel(request: HttpRequest) -> HttpResponse:
    """Import Layanan records from an uploaded Excel file."""
    return handle_excel_import(
        request, import_layanan_from_excel, "daftar_layanan"
    )


@feature_permission_required("layanan.view_layanan")
def template_layanan_excel(request: HttpRequest) -> HttpResponse:
    """Download sample Excel template for Layanan import."""
    buffer = export_layanan_template_to_excel()
    return excel_export_response(buffer, "template_layanan.xlsx")


@feature_permission_required("layanan.view_jenislayanan")
def export_jenis_layanan_excel(request: HttpRequest) -> HttpResponse:
    """Download all JenisLayanan records as an Excel file."""
    buffer = export_jenis_layanan_to_excel()
    return excel_export_response(buffer, "master_jenis_layanan.xlsx")


@feature_permission_required("layanan.add_jenislayanan")
def import_jenis_layanan_excel(request: HttpRequest) -> HttpResponse:
    """Import JenisLayanan records from an uploaded Excel file."""
    return handle_excel_import(
        request, import_jenis_layanan_from_excel, "daftar_jenis_layanan"
    )


@feature_permission_required("layanan.view_jenislayanan")
def template_jenis_layanan_excel(request: HttpRequest) -> HttpResponse:
    """Download sample Excel template for Jenis Layanan import."""
    buffer = export_jenis_layanan_template_to_excel()
    return excel_export_response(buffer, "template_jenis_layanan.xlsx")
