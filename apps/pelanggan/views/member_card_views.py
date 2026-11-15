"""Views for QR code SVG and printable Member/Customer Card (ADR 002 §1.1)."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from apps.pelanggan.exports.qr_export import generate_qr_svg_bytes
from apps.pelanggan.models import Langganan


def _ensure_kode_pelanggan(langganan: Langganan) -> str:
    """Ensures a Langganan record has an assigned kode_pelanggan."""
    if not langganan.kode_pelanggan:
        langganan.save()
    return langganan.kode_pelanggan or f"MBR{langganan.pk:05d}"


@login_required
def langganan_qr_svg(request: HttpRequest, pk: int) -> HttpResponse:
    """Returns SVG QR code image for a Langganan's kode_pelanggan."""
    langganan = get_object_or_404(Langganan, pk=pk)
    code = _ensure_kode_pelanggan(langganan)
    buffer = generate_qr_svg_bytes(code, size=180)
    return HttpResponse(buffer.getvalue(), content_type="image/svg+xml")


@login_required
def cetak_kartu_member(request: HttpRequest, pk: int) -> HttpResponse:
    """Renders printable Kartu Member / Pelanggan with QR code, customer name, house, phone, and tariff."""
    langganan = get_object_or_404(
        Langganan.objects.select_related(
            "pelanggan",
            "pelanggan__rumah",
            "jenis_layanan",
            "jenis_layanan__layanan",
        ),
        pk=pk,
    )
    _ensure_kode_pelanggan(langganan)
    context = {
        "langganan": langganan,
        "pelanggan": langganan.pelanggan,
        "rumah": langganan.pelanggan.rumah,
        "jenis_layanan": langganan.jenis_layanan,
        "autoprint": request.GET.get("autoprint") == "1",
    }
    return render(request, "pelanggan/kartu_member_print.html", context)
