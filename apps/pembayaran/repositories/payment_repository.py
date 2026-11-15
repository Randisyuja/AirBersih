"""Database mutation layer (Repositories) for pembayaran module (ADR 002 §1.4)."""

from datetime import datetime
from typing import Optional, Tuple
from django.utils import timezone
from apps.pembayaran.models import Pembayaran
from apps.pelanggan.models import Pelanggan, Tagihan
from apps.layanan.models import JenisLayanan
from apps.users.models import Kasir
from apps.pembayaran.choices import StatusChoice


def create_pembayaran(
    pelanggan: Pelanggan,
    jenis_layanan: JenisLayanan,
    bulan: int,
    tahun: int,
    jumlah_bayar: int,
    status_bayar: str = StatusChoice.Lunas,
    tgl_pembayaran: Optional[datetime] = None,
    kasir: Optional[Kasir] = None,
) -> Pembayaran:
    """Creates and persists a Pembayaran instance."""
    if tgl_pembayaran is None and status_bayar == StatusChoice.Lunas:
        tgl_pembayaran = timezone.now()

    return Pembayaran.objects.create(
        pelanggan=pelanggan,
        jenis_layanan=jenis_layanan,
        bulan=bulan,
        tahun=tahun,
        jumlah_bayar=jumlah_bayar,
        status_bayar=status_bayar,
        tgl_pembayaran=tgl_pembayaran,
        kasir=kasir,
    )


def update_pembayaran_status(
    pembayaran: Pembayaran,
    status_bayar: str,
    tgl_pembayaran: Optional[datetime] = None,
) -> Pembayaran:
    """Updates status and payment date of a Pembayaran instance."""
    pembayaran.status_bayar = status_bayar
    if tgl_pembayaran is not None:
        pembayaran.tgl_pembayaran = tgl_pembayaran
    elif status_bayar == StatusChoice.Lunas and not pembayaran.tgl_pembayaran:
        pembayaran.tgl_pembayaran = timezone.now()

    pembayaran.save(update_fields=["status_bayar", "tgl_pembayaran"])
    return pembayaran


def delete_pembayaran_by_id(pk: int) -> bool:
    """Deletes a Pembayaran record by its primary key. Returns True if deleted."""
    deleted_count, _ = Pembayaran.objects.filter(pk=pk).delete()
    return deleted_count > 0


def update_tagihan_status(
    tagihan: Tagihan,
    status_tagihan: str,
) -> Tagihan:
    """Updates status_tagihan of a Tagihan instance."""
    tagihan.status_tagihan = status_tagihan
    tagihan.save(update_fields=["status_tagihan"])
    return tagihan


def upsert_pembayaran_for_tagihan(
    tagihan: Tagihan,
    kasir: Optional[Kasir] = None,
    jumlah_bayar: Optional[int] = None,
    tgl_pembayaran: Optional[datetime] = None,
    status_bayar: str = StatusChoice.Lunas,
) -> Tuple[Pembayaran, bool]:
    """Finds existing Pembayaran for tagihan's customer/service/month/year or creates a new one."""
    if jumlah_bayar is None:
        jumlah_bayar = tagihan.jumlah_bayar
    if tgl_pembayaran is None:
        tgl_pembayaran = timezone.now()

    pembayaran, created = Pembayaran.objects.update_or_create(
        pelanggan=tagihan.pelanggan,
        jenis_layanan=tagihan.jenis_layanan,
        bulan=tagihan.bulan,
        tahun=tagihan.tahun,
        defaults={
            "jumlah_bayar": jumlah_bayar,
            "status_bayar": status_bayar,
            "tgl_pembayaran": tgl_pembayaran,
            "kasir": kasir,
        },
    )
    return pembayaran, created
