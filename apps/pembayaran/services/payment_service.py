"""Payment domain services (ADR 002 §1.2 - Business Logic Engine)."""

from datetime import datetime
from typing import Optional
from django.db import transaction
from django.utils import timezone
from apps.layanan.models import JenisLayanan
from apps.pelanggan.models import Pelanggan, Tagihan
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.exceptions.payment_exceptions import (
    PaymentAlreadySettledError,
    PaymentValidationError,
    TagihanNotFoundError,
)
from apps.pembayaran.models import Pembayaran
from apps.pembayaran.repositories.payment_repository import (
    create_pembayaran,
    delete_pembayaran_by_id,
    update_tagihan_status,
    upsert_pembayaran_for_tagihan,
)
from apps.users.models import Kasir


@transaction.atomic
def record_payment(
    tagihan_id: int,
    jumlah_dibayar: Optional[int] = None,
    metode_pembayaran: str = "Tunai",
    user: Optional[Kasir] = None,
    kasir: Optional[Kasir] = None,
) -> Pembayaran:
    """
    Atomically settles a Tagihan:
    1. Validates that the tagihan exists.
    2. Validates that the tagihan is not already paid ('Lunas').
    3. Transitions Tagihan status to 'Lunas'.
    4. Upserts Pembayaran receipt record with current timestamp.
    """
    operator = kasir or user
    try:
        tagihan = (
            Tagihan.objects.select_for_update()
            .select_related("pelanggan", "jenis_layanan")
            .get(pk=tagihan_id)
        )
    except Tagihan.DoesNotExist:
        raise TagihanNotFoundError(f"Tagihan dengan ID {tagihan_id} tidak ditemukan.")

    if tagihan.status_tagihan == StatusChoice.Lunas:
        raise PaymentAlreadySettledError(
            f"Tagihan ID {tagihan_id} untuk periode {tagihan.bulan}/{tagihan.tahun} sudah lunas."
        )

    amount = jumlah_dibayar if jumlah_dibayar is not None else tagihan.jumlah_bayar
    if amount <= 0:
        raise PaymentValidationError("Jumlah pembayaran harus lebih dari 0.")

    update_tagihan_status(tagihan, StatusChoice.Lunas)

    pembayaran, _ = upsert_pembayaran_for_tagihan(
        tagihan=tagihan,
        kasir=operator,
        jumlah_bayar=amount,
        tgl_pembayaran=timezone.now(),
        status_bayar=StatusChoice.Lunas,
    )
    return pembayaran


@transaction.atomic
def record_direct_pembayaran(
    pelanggan_id: int,
    jenis_layanan_id: int,
    bulan: int,
    tahun: int,
    jumlah_bayar: int,
    kasir: Optional[Kasir] = None,
    user: Optional[Kasir] = None,
    status_bayar: str = StatusChoice.Lunas,
    tgl_pembayaran: Optional[datetime] = None,
) -> Pembayaran:
    """Directly records a Pembayaran entry (e.g. from manual admin/form entry)."""
    operator = kasir or user
    try:
        pelanggan = Pelanggan.objects.get(pk=pelanggan_id)
        jenis_layanan = JenisLayanan.objects.get(pk=jenis_layanan_id)
    except (Pelanggan.DoesNotExist, JenisLayanan.DoesNotExist) as exc:
        raise PaymentValidationError(f"Pelanggan atau jenis layanan tidak valid: {exc}")

    pembayaran = create_pembayaran(
        pelanggan=pelanggan,
        jenis_layanan=jenis_layanan,
        bulan=bulan,
        tahun=tahun,
        jumlah_bayar=jumlah_bayar,
        status_bayar=status_bayar,
        tgl_pembayaran=tgl_pembayaran or timezone.now(),
        kasir=operator,
    )

    # Sync corresponding Tagihan if it exists
    tagihan = Tagihan.objects.filter(
        pelanggan=pelanggan,
        jenis_layanan=jenis_layanan,
        bulan=bulan,
        tahun=tahun,
    ).first()
    if tagihan and status_bayar == StatusChoice.Lunas:
        update_tagihan_status(tagihan, StatusChoice.Lunas)

    return pembayaran


@transaction.atomic
def delete_payment(payment_id: int) -> bool:
    """Deletes a payment record and reverts associated tagihan to 'Belum' if found."""
    pembayaran = Pembayaran.objects.filter(pk=payment_id).first()
    if not pembayaran:
        return False

    tagihan = Tagihan.objects.filter(
        pelanggan=pembayaran.pelanggan,
        jenis_layanan=pembayaran.jenis_layanan,
        bulan=pembayaran.bulan,
        tahun=pembayaran.tahun,
    ).first()
    if tagihan and tagihan.status_tagihan == StatusChoice.Lunas:
        update_tagihan_status(tagihan, StatusChoice.Belum)

    return delete_pembayaran_by_id(payment_id)
