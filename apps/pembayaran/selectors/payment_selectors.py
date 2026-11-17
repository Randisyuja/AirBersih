"""Payment selectors (ADR 002 §1.3 - Read-only query layer)."""

from typing import Any, Dict, List, Optional
from django.db.models import Q, QuerySet, Sum
from apps.layanan.models import JenisLayanan, Layanan
from apps.pelanggan.models import Langganan
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.models import Pembayaran
from apps.pembayaran.selectors.report_selectors import get_service_payment_matrix
from apps.pembayaran.selectors.revenue_selectors import get_annual_revenue


def get_pembayaran_list_queryset(
    q: Optional[str] = None,
    layanan: Optional[str] = None,
    jenis_layanan_id: Optional[str] = None,
    tgl_mulai: Optional[str] = None,
    tgl_akhir: Optional[str] = None,
) -> QuerySet[Pembayaran]:
    """Returns Pembayaran records with preloaded relations and optional search/filter criteria."""
    qs = Pembayaran.objects.select_related(
        "pelanggan",
        "pelanggan__rumah",
        "jenis_layanan",
        "jenis_layanan__layanan",
        "kasir",
    )

    if q and q.strip():
        clean_q = q.strip()
        qs = qs.filter(
            Q(pelanggan__nama__icontains=clean_q)
            | Q(pelanggan__barcode__icontains=clean_q)
            | Q(pelanggan__rumah__no_rumah__icontains=clean_q)
            | Q(pelanggan__rumah__rt__icontains=clean_q)
            | Q(jenis_layanan__nama_jenis__icontains=clean_q)
            | Q(jenis_layanan__layanan__nama_layanan__icontains=clean_q)
            | Q(kasir__username__icontains=clean_q)
        )

    if layanan and layanan.strip():
        qs = qs.filter(jenis_layanan__layanan__nama_layanan__iexact=layanan.strip())

    if jenis_layanan_id and str(jenis_layanan_id).strip().isdigit():
        qs = qs.filter(jenis_layanan_id=int(str(jenis_layanan_id).strip()))

    if tgl_mulai and tgl_mulai.strip():
        qs = qs.filter(tgl_pembayaran__date__gte=tgl_mulai.strip())

    if tgl_akhir and tgl_akhir.strip():
        qs = qs.filter(tgl_pembayaran__date__lte=tgl_akhir.strip())

    return qs.order_by("-tahun", "-bulan", "-id_pembayaran")


def get_all_layanan_options() -> QuerySet[Layanan]:
    return Layanan.objects.all().order_by("nama_layanan")


def get_all_jenis_layanan_options() -> QuerySet[JenisLayanan]:
    return JenisLayanan.objects.select_related("layanan").order_by("layanan__nama_layanan", "nama_jenis")


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


def get_pembayaran_by_ids(pks: List[int]) -> List[Pembayaran]:
    """Retrieves multiple Pembayaran records ordered by period for combined receipt printing."""
    if not pks:
        return []
    return list(
        Pembayaran.objects.filter(pk__in=pks)
        .select_related(
            "pelanggan",
            "pelanggan__rumah",
            "jenis_layanan",
            "jenis_layanan__layanan",
            "kasir",
        )
        .order_by("tahun", "bulan", "id_pembayaran")
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
