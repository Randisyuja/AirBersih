"""Annual payment report views for services (ADR 002 §1.1)."""

import json
from typing import Optional
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from apps.core.permissions import feature_permission_required
from apps.pembayaran.forms import TahunForm
from apps.pembayaran.selectors.report_selectors import get_service_payment_matrix
from apps.pembayaran.selectors.revenue_selectors import (
    get_annual_revenue,
    get_monthly_revenue_breakdown,
)

BULAN_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
]


def _parse_optional_bulan(raw_bulan: Optional[str]) -> Optional[int]:
    """Parses optional month filter parameter (1..12), returning None if invalid/empty."""
    if not raw_bulan:
        return None
    try:
        val = int(raw_bulan)
        return val if 1 <= val <= 12 else None
    except (ValueError, TypeError):
        return None


@feature_permission_required("pembayaran.view_pembayaran")
def laporan_tahunan(request: HttpRequest, layanan: str) -> HttpResponse:
    """Renders annual matrix payment report, monthly revenue chart, and annual KPI for AIR/WIFI."""
    current_year = timezone.now().year
    form = TahunForm(request.GET or None)

    if form.is_valid():
        tahun = int(form.cleaned_data.get("tahun") or current_year)
    else:
        tahun = current_year

    selected_bulan = _parse_optional_bulan(request.GET.get("bulan"))
    data_laporan = get_service_payment_matrix(layanan=layanan, tahun=tahun)
    total_pemasukan_tahunan = get_annual_revenue(layanan=layanan, tahun=tahun)
    monthly_revenue = get_monthly_revenue_breakdown(layanan=layanan, tahun=tahun)

    if selected_bulan is not None:
        selected_month_revenue = monthly_revenue[selected_bulan - 1]
        selected_bulan_label = f"Bulan {BULAN_LABELS[selected_bulan - 1]} {tahun}"
    else:
        selected_month_revenue = total_pemasukan_tahunan
        selected_bulan_label = f"Semua Bulan ({tahun})"

    context = {
        "layanan": layanan,
        "data_laporan": data_laporan,
        "tahun": tahun,
        "form": form,
        "bulan_labels": BULAN_LABELS,
        "bulan_choices": list(enumerate(BULAN_LABELS, start=1)),
        "selected_bulan": selected_bulan,
        "selected_bulan_label": selected_bulan_label,
        "total_pemasukan_tahunan": total_pemasukan_tahunan,
        "annual_revenue": total_pemasukan_tahunan,
        "selected_month_revenue": selected_month_revenue,
        "monthly_revenue": monthly_revenue,
        "monthly_revenue_json": json.dumps(monthly_revenue),
        "bulan_labels_json": json.dumps(BULAN_LABELS),
    }

    return render(request, "pembayaran/laporan_pembayaran_layanan.html", context)
