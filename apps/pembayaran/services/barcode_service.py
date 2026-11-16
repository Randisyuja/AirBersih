"""Barcode domain services (ADR 002 §1.2 - Business Logic Engine)."""

from typing import Dict, List, Optional
from django.db import transaction
from apps.pelanggan.models import Tagihan
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.dto.barcode_dto import BarcodeResolutionDTO
from apps.pembayaran.exceptions.payment_exceptions import (
    CustomerNotFoundError,
    PaymentValidationError,
    TagihanNotFoundError,
)
from apps.pembayaran.models import Pembayaran
from apps.pembayaran.selectors.barcode_selectors import (
    get_customer_dues_by_barcode,
    get_pelanggan_by_barcode,
)
from apps.pembayaran.services.payment_service import record_payment
from apps.users.models import Kasir


def resolve_barcode(barcode: str) -> BarcodeResolutionDTO:
    """
    Validates barcode input and retrieves full customer profile, tariffs, and dues.
    Raises CustomerNotFoundError if not found.
    """
    cleaned_code = barcode.strip() if barcode else ""
    if not cleaned_code:
        raise PaymentValidationError("Parameter barcode tidak boleh kosong.")

    dto = get_customer_dues_by_barcode(cleaned_code)
    if not dto:
        raise CustomerNotFoundError(
            f"Pelanggan dengan barcode '{cleaned_code}' tidak ditemukan."
        )
    return dto


def _lookup_custom_amount(
    custom_amounts: Optional[Dict[str, int]], tagihan_id: int
) -> Optional[int]:
    if not custom_amounts:
        return None
    raw = custom_amounts.get(str(tagihan_id)) or custom_amounts.get(tagihan_id)
    if raw is not None:
        try:
            val = int(raw)
            return val if val > 0 else None
        except (ValueError, TypeError):
            return None
    return None


def pay_due_by_barcode(
    barcode: str,
    tagihan_id: int,
    user: Optional[Kasir] = None,
    kasir: Optional[Kasir] = None,
    jumlah_bayar: Optional[int] = None,
) -> Pembayaran:
    """
    Verifies that the tagihan belongs to the customer matching the barcode,
    then executes atomic payment recording.
    """
    pelanggan = get_pelanggan_by_barcode(barcode)
    if not pelanggan:
        raise CustomerNotFoundError(f"Barcode '{barcode}' tidak ditemukan.")

    tagihan = Tagihan.objects.filter(pk=tagihan_id).first()
    if not tagihan:
        raise TagihanNotFoundError(f"Tagihan {tagihan_id} tidak ditemukan.")

    if tagihan.pelanggan_id != pelanggan.id_pelanggan:
        raise PaymentValidationError(
            f"Tagihan {tagihan_id} bukan milik pelanggan dengan barcode {barcode}."
        )

    return record_payment(
        tagihan_id=tagihan_id,
        jumlah_dibayar=jumlah_bayar,
        user=user,
        kasir=kasir,
    )


@transaction.atomic
def pay_all_dues_by_barcode(
    barcode: str,
    user: Optional[Kasir] = None,
    kasir: Optional[Kasir] = None,
    custom_amounts: Optional[Dict[str, int]] = None,
) -> List[Pembayaran]:
    """
    Atomically settles all unpaid Tagihan ('Belum') for the customer matching `barcode`.
    """
    pelanggan = get_pelanggan_by_barcode(barcode)
    if not pelanggan:
        raise CustomerNotFoundError(f"Barcode '{barcode}' tidak ditemukan.")

    unpaid_list = list(
        Tagihan.objects.filter(
            pelanggan=pelanggan, status_tagihan=StatusChoice.Belum
        ).order_by("tahun", "bulan", "id_tagihan")
    )
    if not unpaid_list:
        raise PaymentValidationError(
            f"Tidak ada tagihan tertunggak untuk pelanggan {pelanggan.nama}."
        )

    settled: List[Pembayaran] = []
    for tagihan in unpaid_list:
        custom_val = _lookup_custom_amount(custom_amounts, tagihan.id_tagihan)
        pembayaran = record_payment(
            tagihan_id=tagihan.id_tagihan,
            jumlah_dibayar=custom_val,
            user=user,
            kasir=kasir,
        )
        settled.append(pembayaran)
    return settled


@transaction.atomic
def pay_selected_dues_by_barcode(
    barcode: str,
    tagihan_ids: List[int],
    user: Optional[Kasir] = None,
    kasir: Optional[Kasir] = None,
    custom_amounts: Optional[Dict[str, int]] = None,
) -> List[Pembayaran]:
    """
    Atomically settles specific unpaid Tagihan records by IDs for the customer matching `barcode`.
    """
    pelanggan = get_pelanggan_by_barcode(barcode)
    if not pelanggan:
        raise CustomerNotFoundError(f"Barcode '{barcode}' tidak ditemukan.")

    if not tagihan_ids:
        raise PaymentValidationError("Daftar tagihan yang dipilih kosong.")

    unpaid_list = list(
        Tagihan.objects.filter(
            id_tagihan__in=tagihan_ids,
            pelanggan=pelanggan,
            status_tagihan=StatusChoice.Belum,
        ).order_by("tahun", "bulan", "id_tagihan")
    )
    if not unpaid_list:
        raise PaymentValidationError(
            f"Tidak ada tagihan valid yang belum lunas untuk pilihan ini."
        )

    settled: List[Pembayaran] = []
    for tagihan in unpaid_list:
        custom_val = _lookup_custom_amount(custom_amounts, tagihan.id_tagihan)
        pembayaran = record_payment(
            tagihan_id=tagihan.id_tagihan,
            jumlah_dibayar=custom_val,
            user=user,
            kasir=kasir,
        )
        settled.append(pembayaran)
    return settled
