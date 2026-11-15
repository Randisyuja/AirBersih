"""Barcode domain services (ADR 002 §1.2 - Business Logic Engine)."""

from typing import List, Optional
from django.db import transaction
from apps.pelanggan.models import Tagihan
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.dto.barcode_dto import BarcodeResolutionDTO
from apps.pembayaran.exceptions.payment_exceptions import (
    CustomerNotFoundError,
    PaymentValidationError,
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


def pay_due_by_barcode(
    barcode: str,
    tagihan_id: int,
    user: Optional[Kasir] = None,
    kasir: Optional[Kasir] = None,
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
        raise PaymentValidationError(f"Tagihan {tagihan_id} tidak ditemukan.")

    if tagihan.pelanggan_id != pelanggan.id_pelanggan:
        raise PaymentValidationError(
            f"Tagihan {tagihan_id} bukan milik pelanggan dengan barcode {barcode}."
        )

    return record_payment(
        tagihan_id=tagihan_id,
        user=user,
        kasir=kasir,
    )


@transaction.atomic
def pay_all_dues_by_barcode(
    barcode: str,
    user: Optional[Kasir] = None,
    kasir: Optional[Kasir] = None,
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
        pembayaran = record_payment(
            tagihan_id=tagihan.id_tagihan,
            user=user,
            kasir=kasir,
        )
        settled.append(pembayaran)
    return settled
