"""Barcode scanner API views for pembayaran (ADR 002 §1.1)."""

import json
import logging
from typing import Any, Dict
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError, IntegrityError
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
    pay_selected_dues_by_barcode,
)

logger = logging.getLogger(__name__)


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

    try:
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
    except CustomerNotFoundError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=404)
    except DatabaseError as exc:
        logger.exception("Database error while scanning barcode %s: %s", code, exc)
        return JsonResponse(
            {"status": "error", "message": "Terjadi kesalahan database saat membaca data pelanggan."},
            status=500,
        )
    except Exception as exc:
        logger.exception("Unexpected error while scanning barcode %s: %s", code, exc)
        return JsonResponse(
            {"status": "error", "message": f"Terjadi kendala sistem: {str(exc)}"},
            status=500,
        )


@login_required
def pay_by_barcode_api(request: HttpRequest) -> JsonResponse:
    """
    POST /pembayaran/api/pay-barcode/
    Settles a single tagihan_id, selected tagihan_ids, or all pending dues (`pay_all=true`)
    for a scanned barcode, and returns `receipt_url` for thermal receipt printing.
    """
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Metode HTTP harus POST."},
            status=405,
        )

    payload = _extract_post_payload(request)
    barcode = str(payload.get("barcode") or "").strip()
    pay_all = str(payload.get("pay_all") or "").lower() in ("true", "1", "yes")
    tagihan_ids_raw = payload.get("tagihan_ids")
    tagihan_id_raw = payload.get("tagihan_id")
    custom_amounts_raw = payload.get("custom_amounts")
    custom_amounts = custom_amounts_raw if isinstance(custom_amounts_raw, dict) else {}
    jumlah_bayar_raw = payload.get("jumlah_bayar")
    jumlah_bayar = int(jumlah_bayar_raw) if (jumlah_bayar_raw is not None and str(jumlah_bayar_raw).isdigit()) else None

    if not barcode:
        return JsonResponse(
            {"status": "error", "message": "Kode barcode wajib diisi."},
            status=400,
        )

    try:
        if pay_all:
            settled = pay_all_dues_by_barcode(
                barcode=barcode,
                kasir=request.user,
                custom_amounts=custom_amounts,
            )
            last_payment = settled[-1]
            settled_list = settled
            msg = f"Berhasil melunasi seluruh ({len(settled)}) tagihan."
        elif tagihan_ids_raw and isinstance(tagihan_ids_raw, list) and len(tagihan_ids_raw) > 0:
            tagihan_ids = [int(tid) for tid in tagihan_ids_raw if str(tid).isdigit()]
            if not tagihan_ids:
                return JsonResponse(
                    {"status": "error", "message": "Daftar tagihan yang dipilih tidak valid."},
                    status=400,
                )
            settled = pay_selected_dues_by_barcode(
                barcode=barcode,
                tagihan_ids=tagihan_ids,
                kasir=request.user,
                custom_amounts=custom_amounts,
            )
            last_payment = settled[-1]
            settled_list = settled
            msg = f"Berhasil melunasi {len(settled)} tagihan terpilih."
        else:
            if not tagihan_id_raw:
                return JsonResponse(
                    {"status": "error", "message": "ID tagihan wajib dipilih."},
                    status=400,
                )
            tid_int = int(tagihan_id_raw)
            single_amount = jumlah_bayar or (
                int(custom_amounts[str(tid_int)])
                if str(tid_int) in custom_amounts and str(custom_amounts[str(tid_int)]).isdigit()
                else None
            )
            last_payment = pay_due_by_barcode(
                barcode=barcode,
                tagihan_id=tid_int,
                kasir=request.user,
                jumlah_bayar=single_amount,
            )
            settled_list = [last_payment]
            msg = (
                f"Pembayaran {last_payment.pelanggan.nama} periode "
                f"{last_payment.bulan}/{last_payment.tahun} berhasil dicatat."
            )

        updated_dto = get_customer_dues_by_barcode(barcode)
        primary_payment = settled_list[0]
        receipt_url = reverse(
            "cetak_struk_thermal", kwargs={"pk": primary_payment.id_pembayaran}
        )
        if len(settled_list) > 1:
            ids_str = ",".join(str(p.id_pembayaran) for p in settled_list)
            receipt_url = f"{receipt_url}?ids={ids_str}"
        settled_total = sum(p.jumlah_bayar for p in settled_list)
        cust_name = primary_payment.pelanggan.nama if primary_payment.pelanggan else "-"

        return JsonResponse(
            {
                "status": "success",
                "message": msg,
                "receipt_id": primary_payment.id_pembayaran,
                "receipt_ids": [p.id_pembayaran for p in settled_list],
                "receipt_url": receipt_url,
                "customer_name": cust_name,
                "settled_count": len(settled_list),
                "settled_total": settled_total,
                "data": updated_dto.to_dict() if updated_dto else None,
            }
        )
    except CustomerNotFoundError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=404)
    except TagihanNotFoundError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=404)
    except PaymentAlreadySettledError as exc:
        return JsonResponse({"status": "error", "message": f"Tagihan sudah lunas: {str(exc)}"}, status=400)
    except PaymentValidationError as exc:
        return JsonResponse({"status": "error", "message": f"Validasi pembayaran gagal: {str(exc)}"}, status=400)
    except ValidationError as exc:
        err_msg = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
        return JsonResponse({"status": "error", "message": f"Data tidak valid: {err_msg}"}, status=400)
    except ValueError as exc:
        return JsonResponse({"status": "error", "message": f"Format nilai tidak valid: {str(exc)}"}, status=400)
    except IntegrityError as exc:
        logger.exception("Integrity error during barcode payment for %s: %s", barcode, exc)
        return JsonResponse({"status": "error", "message": "Terjadi konflik data transaksi (kemungkinan pembayaran ganda)."}, status=400)
    except DatabaseError as exc:
        logger.exception("Database error during barcode payment for %s: %s", barcode, exc)
        return JsonResponse({"status": "error", "message": "Terjadi kesalahan pada database saat menyimpan pembayaran."}, status=500)
    except PermissionDenied as exc:
        return JsonResponse({"status": "error", "message": f"Akses ditolak: {str(exc)}"}, status=403)
    except Exception as exc:
        logger.exception("Unhandled error during barcode payment for %s: %s", barcode, exc)
        return JsonResponse({"status": "error", "message": f"Terjadi kesalahan tidak terduga pada server: {str(exc)}"}, status=500)
