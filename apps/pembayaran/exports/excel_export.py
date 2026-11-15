"""Excel export generator for pembayaran (ADR 002 §1.6 - returns io.BytesIO)."""

import io
from typing import Optional
from django.db.models import QuerySet
from openpyxl import Workbook
from apps.pembayaran.models import Pembayaran
from apps.pembayaran.selectors.payment_selectors import get_pembayaran_export_queryset


def export_pembayaran_to_excel(
    queryset: Optional[QuerySet[Pembayaran]] = None,
) -> io.BytesIO:
    """
    Generates an in-memory .xlsx workbook for payment records.
    Returns io.BytesIO buffer.
    Fixes latent bug by using `p.kasir.username` (Kasir is AbstractUser).
    """
    if queryset is None:
        queryset = get_pembayaran_export_queryset()

    wb = Workbook()
    ws = wb.active
    ws.title = "Pembayaran"

    headers = [
        "ID", "Nama", "No. Rumah", "Layanan",
        "Bulan", "Tahun", "Status", "Tanggal Bayar",
        "Kasir", "Jumlah"
    ]
    ws.append(headers)

    for p in queryset:
        no_rumah = p.pelanggan.rumah.no_rumah if (p.pelanggan and p.pelanggan.rumah) else "-"
        nama_pelanggan = p.pelanggan.nama if p.pelanggan else "-"
        nama_layanan = p.jenis_layanan.nama_jenis if p.jenis_layanan else "-"
        tgl_bayar = p.tgl_pembayaran.strftime("%d-%m-%Y") if p.tgl_pembayaran else "-"
        # Kasir inherits directly from AbstractUser; access p.kasir.username
        kasir_name = p.kasir.username if p.kasir else "-"
        jumlah = float(p.jumlah_bayar) if p.jumlah_bayar is not None else 0.0

        ws.append([
            p.id_pembayaran,
            nama_pelanggan,
            no_rumah,
            nama_layanan,
            p.bulan,
            p.tahun,
            p.status_bayar,
            tgl_bayar,
            kasir_name,
            jumlah,
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# Alias for backward compatibility with existing tests and scripts
generate_pembayaran_excel = export_pembayaran_to_excel
