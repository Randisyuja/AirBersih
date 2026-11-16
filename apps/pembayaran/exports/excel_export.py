"""Excel export generator for pembayaran (ADR 002 §1.6 - returns io.BytesIO)."""

import io
from typing import Optional
from django.db.models import QuerySet
from openpyxl import Workbook
from apps.pembayaran.models import Pembayaran
from apps.pembayaran.selectors.payment_selectors import get_pembayaran_export_queryset
from apps.pembayaran.selectors.report_selectors import get_service_payment_matrix


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


def export_laporan_tahunan_excel(layanan: str, tahun: int) -> io.BytesIO:
    """
    Generates an Excel workbook for the annual service payment matrix (Air / WiFi).
    Each month column is filled with the actual payment amount (iuran) paid for that month.
    """
    nama_layanan = (layanan or "").strip().upper()
    matrix_rows = get_service_payment_matrix(layanan=nama_layanan, tahun=tahun)

    wb = Workbook()
    ws = wb.active
    ws.title = f"{nama_layanan}_{tahun}"

    ws.append([f"LAPORAN PEMBAYARAN IURAN {nama_layanan} - TAHUN {tahun}"])
    ws.append([])

    headers = [
        "No", "Nama Pelanggan", "No. Rumah",
        "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
        "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
        "Total Bayar"
    ]
    ws.append(headers)

    monthly_totals = [0] * 12
    grand_total = 0

    for idx, row in enumerate(matrix_rows, start=1):
        nominals = row.get("nominal_bulan") or [0] * 12
        row_total = sum(nominals)
        grand_total += row_total
        for m_idx, nom in enumerate(nominals):
            monthly_totals[m_idx] += nom

        ws.append([
            idx,
            row.get("pelanggan", "-"),
            row.get("alamat", "-"),
            *nominals,
            row_total,
        ])

    ws.append([
        "TOTAL", "Pemasukan Bulanan", "-",
        *monthly_totals,
        grand_total,
    ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
