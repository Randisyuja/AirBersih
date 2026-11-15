"""Optimized report matrix selectors eliminating N+1 queries (ADR 002 §1.3)."""

from typing import Any, Dict, List
from apps.pelanggan.models import Pelanggan
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.models import Pembayaran


def get_service_payment_matrix(layanan: str, tahun: int) -> List[Dict[str, Any]]:
    """
    Builds 12-month payment status matrix for active subscribers of `layanan` in `tahun`
    using a single bulk query for payments instead of O(12*N) per-month queries.
    """
    nama_layanan = (layanan or "").strip().upper()
    pelanggan_aktif = list(
        Pelanggan.objects.filter(
            langganan__jenis_layanan__layanan__nama_layanan__iexact=nama_layanan,
            langganan__aktif=True,
        )
        .select_related("rumah")
        .distinct()
    )

    if not pelanggan_aktif:
        return []

    pelanggan_ids = [p.id_pelanggan for p in pelanggan_aktif]
    paid_pairs = set(
        Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan__iexact=nama_layanan,
            pelanggan_id__in=pelanggan_ids,
            tahun=tahun,
            status_bayar=StatusChoice.Lunas,
        ).values_list("pelanggan_id", "bulan")
    )

    data_laporan: List[Dict[str, Any]] = []
    for pelanggan in pelanggan_aktif:
        status_bulan = [
            "Lunas" if (pelanggan.id_pelanggan, bulan) in paid_pairs else "Belum"
            for bulan in range(1, 13)
        ]
        alamat = pelanggan.rumah.no_rumah if pelanggan.rumah else "-"
        data_laporan.append(
            {
                "pelanggan": pelanggan.nama,
                "alamat": alamat,
                "barcode": pelanggan.barcode or "-",
                "status_bulan": status_bulan,
            }
        )

    return data_laporan
