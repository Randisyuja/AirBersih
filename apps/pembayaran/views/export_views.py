"""Export document views for pembayaran (ADR 002 §1.1 & §1.6)."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
from apps.pembayaran.exports.excel_export import export_pembayaran_to_excel
from apps.pembayaran.exports.pdf_export import generate_laporan_pembayaran_pdf


@login_required
def export_pembayaran_excel(request: HttpRequest) -> HttpResponse:
    """Exports payment records to Excel format."""
    buffer = export_pembayaran_to_excel()
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/ms-excel",
    )
    response["Content-Disposition"] = 'attachment; filename="laporan_pembayaran.xlsx"'
    return response


@login_required
@xframe_options_sameorigin
def export_pembayaran_pdf(
    request: HttpRequest, layanan: str, tahun: int
) -> HttpResponse:
    """Exports annual payment status matrix to PDF format (supports same-origin iframe preview)."""
    nama_layanan = layanan.upper()
    current_year = timezone.now().year

    try:
        tahun_int = int(tahun) if tahun else current_year
    except (ValueError, TypeError):
        tahun_int = current_year

    buffer = generate_laporan_pembayaran_pdf(layanan=nama_layanan, tahun=tahun_int)

    is_download = request.GET.get("download") == "1"
    disposition_type = "attachment" if is_download else "inline"

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = (
        f'{disposition_type}; filename="Laporan_Pembayaran_{nama_layanan}_{tahun_int}.pdf"'
    )
    return response
