"""Revenue aggregation selectors for water and wifi reports (ADR 002 §1.3)."""

from typing import List, Optional
from django.db.models import Sum
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.models import Pembayaran


def get_annual_revenue(layanan: str, tahun: int) -> int:
    """Calculates total annual revenue sum for a given service ('AIR' or 'WIFI') and year."""
    if not layanan:
        return 0
    total = (
        Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan__iexact=layanan.strip(),
            tahun=tahun,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total=Sum("jumlah_bayar"))["total"]
    )
    return int(total or 0)


def get_monthly_revenue_breakdown(layanan: str, tahun: int) -> List[int]:
    """
    Returns a 12-element list of monthly revenue totals [Jan..Dec] for a service and year
    in a single grouped database query.
    """
    if not layanan:
        return [0] * 12

    rows = (
        Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan__iexact=layanan.strip(),
            tahun=tahun,
            status_bayar=StatusChoice.Lunas,
        )
        .values("bulan")
        .annotate(total=Sum("jumlah_bayar"))
    )
    totals_by_month = {
        int(row["bulan"]): int(row["total"] or 0)
        for row in rows
        if row.get("bulan") is not None
    }
    return [totals_by_month.get(month, 0) for month in range(1, 13)]


def get_monthly_revenue_for_month(
    layanan: str, tahun: int, bulan: Optional[int]
) -> int:
    """Returns revenue for a specific month (1..12) or full annual revenue if bulan is None."""
    if bulan is None or not (1 <= int(bulan) <= 12):
        return get_annual_revenue(layanan=layanan, tahun=tahun)
    breakdown = get_monthly_revenue_breakdown(layanan=layanan, tahun=tahun)
    return breakdown[int(bulan) - 1]
