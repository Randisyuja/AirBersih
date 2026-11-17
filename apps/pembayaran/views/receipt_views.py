"""Thermal printer receipt views for Pembayaran transactions (ADR 002 §1.1)."""

import json
from typing import List
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from apps.pelanggan.exports.qr_export import generate_qr_svg_bytes
from apps.pelanggan.models import Langganan
from apps.pembayaran.choices import BulanChoice
from apps.pembayaran.selectors.payment_selectors import (
    get_pembayaran_by_id,
    get_pembayaran_by_ids,
)


def _format_rp(amount: int) -> str:
    """Formats integer amount into Indonesian Rupiah display string."""
    return "Rp" + f"{int(amount or 0):,}".replace(",", ".")


def _parse_receipt_ids(raw_ids: str, fallback_pk: int) -> List[int]:
    """Parses comma-separated payment IDs from query string with fallback to primary pk."""
    if not raw_ids:
        return [fallback_pk]
    parsed: List[int] = []
    for part in raw_ids.split(","):
        cleaned = part.strip()
        if cleaned.isdigit():
            val = int(cleaned)
            if val not in parsed:
                parsed.append(val)
    return parsed or [fallback_pk]


@login_required
def cetak_struk_thermal(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Renders a 58mm / 80mm thermal POS receipt for one or multiple Pembayaran records
    (via `?ids=1,2,3` when a customer pays multiple months in one transaction).
    Supports `?autoprint=1` to automatically open the browser print dialog.
    """
    payment_ids = _parse_receipt_ids(request.GET.get("ids", ""), pk)
    payments = get_pembayaran_by_ids(payment_ids)
    if not payments:
        raise Http404("Data pembayaran tidak ditemukan.")

    primary = payments[0]
    langganan = (
        Langganan.objects.filter(
            pelanggan=primary.pelanggan,
            jenis_layanan=primary.jenis_layanan,
        )
        .first()
    )
    kode_member = (
        (langganan.kode_pelanggan if langganan and langganan.kode_pelanggan else None)
        or primary.pelanggan.barcode
        or f"PLG{primary.pelanggan_id:05d}"
    )

    bulan_dict = dict(BulanChoice.choices)
    items = []
    escpos_items = []
    total_bayar = 0

    for p in payments:
        nama_bln = bulan_dict.get(p.bulan, str(p.bulan))
        layanan_label = f"{p.jenis_layanan.layanan.nama_layanan} - {p.jenis_layanan.nama_jenis}"
        periode_label = f"{nama_bln} {p.tahun}"
        items.append(
            {
                "id": p.id_pembayaran,
                "layanan": layanan_label,
                "periode": periode_label,
                "jumlah_bayar": p.jumlah_bayar,
            }
        )
        escpos_items.append(
            {
                "layanan": layanan_label,
                "periode": periode_label,
                "total": _format_rp(p.jumlah_bayar),
            }
        )
        total_bayar += int(p.jumlah_bayar or 0)

    is_batch = len(payments) > 1
    no_struk = (
        f"TRX-{primary.tahun}-{primary.id_pembayaran:05d}x{len(payments)}"
        if is_batch
        else f"TRX-{primary.tahun}{primary.bulan:02d}-{primary.id_pembayaran:05d}"
    )

    context = {
        "pembayaran": primary,
        "payments": payments,
        "items": items,
        "items_json": json.dumps(escpos_items),
        "total_bayar": total_bayar,
        "is_batch": is_batch,
        "pelanggan": primary.pelanggan,
        "rumah": primary.pelanggan.rumah,
        "jenis_layanan": primary.jenis_layanan,
        "kode_member": kode_member,
        "nama_bulan": bulan_dict.get(primary.bulan, str(primary.bulan)),
        "no_struk": no_struk,
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
