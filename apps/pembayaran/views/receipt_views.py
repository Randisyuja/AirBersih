"""Thermal printer receipt views for Pembayaran transactions (ADR 002 §1.1)."""

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from apps.pelanggan.exports.qr_export import generate_qr_svg_bytes
from apps.pelanggan.models import Langganan
from apps.pembayaran.choices import BulanChoice
from apps.pembayaran.selectors.payment_selectors import get_pembayaran_by_id


@login_required
def cetak_struk_thermal(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Renders a 58mm / 80mm thermal POS receipt for a completed Pembayaran record.
    Supports `?autoprint=1` to automatically open the browser print dialog.
    """
    pembayaran = get_pembayaran_by_id(pk)
    if not pembayaran:
        raise Http404("Data pembayaran tidak ditemukan.")

    langganan = (
        Langganan.objects.filter(
            pelanggan=pembayaran.pelanggan,
            jenis_layanan=pembayaran.jenis_layanan,
        )
        .first()
    )
    kode_member = (
        (langganan.kode_pelanggan if langganan and langganan.kode_pelanggan else None)
        or pembayaran.pelanggan.barcode
        or f"PLG{pembayaran.pelanggan_id:05d}"
    )

    bulan_dict = dict(BulanChoice.choices)
    nama_bulan = bulan_dict.get(pembayaran.bulan, str(pembayaran.bulan))

    context = {
        "pembayaran": pembayaran,
        "pelanggan": pembayaran.pelanggan,
        "rumah": pembayaran.pelanggan.rumah,
        "jenis_layanan": pembayaran.jenis_layanan,
        "kode_member": kode_member,
        "nama_bulan": nama_bulan,
        "no_struk": f"TRX-{pembayaran.tahun}{pembayaran.bulan:02d}-{pembayaran.id_pembayaran:05d}",
        "autoprint": request.GET.get("autoprint") == "1",
    }
    return render(request, "pembayaran/struk_thermal.html", context)


@login_required
def pembayaran_qr_svg(request: HttpRequest, pk: int) -> HttpResponse:
    """Returns SVG QR code for a payment receipt's customer/member code."""
    pembayaran = get_pembayaran_by_id(pk)
    if not pembayaran:
        raise Http404("Data pembayaran tidak ditemukan.")

    langganan = Langganan.objects.filter(
        pelanggan=pembayaran.pelanggan,
        jenis_layanan=pembayaran.jenis_layanan,
    ).first()
    code = (
        (langganan.kode_pelanggan if langganan and langganan.kode_pelanggan else None)
        or pembayaran.pelanggan.barcode
        or f"PLG{pembayaran.pelanggan_id:05d}"
    )
    buffer = generate_qr_svg_bytes(code, size=140)
    return HttpResponse(buffer.getvalue(), content_type="image/svg+xml")
