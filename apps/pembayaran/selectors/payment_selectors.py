"""Payment selectors (ADR 002 §1.3 - Read-only query layer)."""

from typing import Any, Dict, List, Optional
from django.db.models import QuerySet, Sum
from apps.pelanggan.models import Langganan
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.models import Pembayaran
from apps.pembayaran.selectors.report_selectors import get_service_payment_matrix
from apps.pembayaran.selectors.revenue_selectors import get_annual_revenue


def get_pembayaran_list_queryset() -> QuerySet[Pembayaran]:
    """Returns all Pembayaran records with preloaded relations to eliminate N+1."""
    return (
        Pembayaran.objects.select_related(
            "pelanggan", "pelanggan__rumah", "jenis_layanan", "kasir"
        ).order_by("-tahun", "-bulan", "-id_pembayaran")
    )


def get_pembayaran_bulanan_queryset(bulan: int, tahun: int) -> QuerySet[Pembayaran]:
    """Returns paid Pembayaran records for given month & year."""
    return (
        Pembayaran.objects.filter(
            bulan=bulan,
            tahun=tahun,
            status_bayar=StatusChoice.Lunas,
        )
        .select_related("pelanggan", "pelanggan__rumah", "jenis_layanan", "kasir")
        .order_by("-tgl_pembayaran")
    )


def get_total_pemasukan_bulanan(bulan: int, tahun: int) -> int:
    """Calculates sum of paid amount for given month & year."""
    total = (
        Pembayaran.objects.filter(
            bulan=bulan,
            tahun=tahun,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total=Sum("jumlah_bayar"))["total"]
    )
    return total or 0


def get_pembayaran_by_id(pk: int) -> Optional[Pembayaran]:
    """Retrieves single Pembayaran instance by pk or None."""
    return (
        Pembayaran.objects.filter(pk=pk)
        .select_related("pelanggan", "pelanggan__rumah", "jenis_layanan", "kasir")
        .first()
    )


def get_active_langganan_by_pelanggan_id(pelanggan_id: int) -> QuerySet[Langganan]:
    """Retrieves active subscriptions for a customer with joined service types."""
    return (
        Langganan.objects.filter(pelanggan_id=pelanggan_id, aktif=True)
        .select_related("jenis_layanan", "jenis_layanan__layanan")
    )


def get_pembayaran_export_queryset() -> QuerySet[Pembayaran]:
    """Queryset optimized for Excel export."""
    return (
        Pembayaran.objects.select_related(
            "pelanggan", "pelanggan__rumah", "jenis_layanan", "kasir"
        ).order_by("-tahun", "-bulan")
    )


def get_laporan_tahunan_matrix(layanan: str, tahun: int) -> List[Dict[str, Any]]:
    """Builds matrix of payment status (Jan-Dec) using bulk prefetch selector."""
    return get_service_payment_matrix(layanan=layanan, tahun=tahun)


def get_total_pemasukan_tahunan(layanan: str, tahun: int) -> int:
    """Calculates total revenue sum for given service and year."""
    return get_annual_revenue(layanan=layanan, tahun=tahun)
