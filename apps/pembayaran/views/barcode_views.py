"""Barcode scanner API views for pembayaran (ADR 002 §1.1)."""

import json
from typing import Any, Dict
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.urls import reverse
from apps.pembayaran.exceptions.payment_exceptions import (
    CustomerNotFoundError,
    PaymentAlreadySettledError,
    PaymentValidationError,
    TagihanNotFoundError,
)
from apps.pembayaran.selectors.barcode_selectors import get_customer_dues_by_barcode
from apps.pembayaran.services.barcode_service import (
    pay_all_dues_by_barcode,
    pay_due_by_barcode,
)


def _extract_post_payload(request: HttpRequest) -> Dict[str, Any]:
    """Extracts POST data from either JSON body or standard form-encoded POST."""
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return {}
    return request.POST.dict()


@login_required
def scan_barcode_api(request: HttpRequest) -> JsonResponse:
    """
    GET /pembayaran/api/scan-barcode/?code=<string>
    Resolves customer profile, matched Langganan (service & tariff), and pending dues
    by scanned Langganan.kode_pelanggan or Pelanggan.barcode.
    """
    code = request.GET.get("code", "").strip()
    if not code:
        return JsonResponse(
            {
                "status": "error",
                "message": "Parameter kode barcode / kode pelanggan wajib disertakan.",
            },
            status=400,
        )

    dto = get_customer_dues_by_barcode(code)
    if not dto:
        return JsonResponse(
            {
                "status": "error",
                "message": "Pelanggan atau langganan dengan kode tersebut tidak ditemukan.",
            },
            status=404,
        )

    return JsonResponse(dto.to_dict())


@login_required
def pay_by_barcode_api(request: HttpRequest) -> JsonResponse:
    """
    POST /pembayaran/api/pay-barcode/
    Settles a single tagihan_id or all pending dues (`pay_all=true`) for a scanned barcode,
    and returns `receipt_url` for thermal receipt printing.
    """
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Metode HTTP harus POST."},
            status=405,
        )

    payload = _extract_post_payload(request)
    barcode = str(payload.get("barcode") or "").strip()
    pay_all = str(payload.get("pay_all") or "").lower() in ("true", "1", "yes")
    tagihan_id_raw = payload.get("tagihan_id")

    if not barcode:
        return JsonResponse(
            {"status": "error", "message": "Kode barcode wajib diisi."},
            status=400,
        )

    try:
        if pay_all:
            settled = pay_all_dues_by_barcode(barcode=barcode, kasir=request.user)
            last_payment = settled[-1]
            msg = f"Berhasil melunasi {len(settled)} tagihan."
        else:
            if not tagihan_id_raw:
                return JsonResponse(
                    {"status": "error", "message": "ID tagihan wajib dipilih."},
                    status=400,
                )
            last_payment = pay_due_by_barcode(
                barcode=barcode,
                tagihan_id=int(tagihan_id_raw),
                kasir=request.user,
            )
            msg = (
                f"Pembayaran {last_payment.pelanggan.nama} periode "
                f"{last_payment.bulan}/{last_payment.tahun} berhasil dicatat."
            )

        updated_dto = get_customer_dues_by_barcode(barcode)
        receipt_url = reverse(
            "cetak_struk_thermal", kwargs={"pk": last_payment.id_pembayaran}
        )
        return JsonResponse(
            {
                "status": "success",
                "message": msg,
                "receipt_id": last_payment.id_pembayaran,
                "receipt_url": receipt_url,
                "data": updated_dto.to_dict() if updated_dto else None,
            }
        )
    except CustomerNotFoundError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=404)
    except (
        PaymentValidationError,
        PaymentAlreadySettledError,
        TagihanNotFoundError,
        ValueError,
    ) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
