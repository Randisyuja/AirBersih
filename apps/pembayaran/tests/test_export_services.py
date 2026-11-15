"""Unit tests for Excel and PDF export services (Milestone 1)."""

import io
import openpyxl
from django.test import TestCase
from django.utils import timezone
from apps.layanan.models import JenisLayanan, Layanan
from apps.pelanggan.models import Pelanggan
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.exports.excel_export import (
    export_pembayaran_to_excel,
    generate_pembayaran_excel,
)
from apps.pembayaran.exports.pdf_export import (
    generate_laporan_pembayaran_pdf,
    generate_pembayaran_pdf,
)
from apps.pembayaran.models import Pembayaran
from apps.rumah.models import Rumah
from apps.users.models import Kasir


class PembayaranExportServiceTests(TestCase):
    def setUp(self):
        self.kasir = Kasir.objects.create_user(
            username="kasir_export",
            password="password",
        )
        self.rumah = Rumah.objects.create(rt="01", no_rumah="A-01")
        self.pelanggan = Pelanggan.objects.create(
            nama="Hasan",
            rumah=self.rumah,
            barcode="PLG00001",
        )
        self.layanan = Layanan.objects.create(nama_layanan="AIR")
        self.jenis = JenisLayanan.objects.create(
            layanan=self.layanan,
            nama_jenis="Warga",
            tarif=25000,
        )
        self.pembayaran = Pembayaran.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis,
            bulan=1,
            tahun=2026,
            status_bayar=StatusChoice.Lunas,
            tgl_pembayaran=timezone.now(),
            kasir=self.kasir,
            jumlah_bayar=25000,
        )

    def test_excel_export_returns_valid_bytesio(self):
        """generate_pembayaran_excel returns io.BytesIO containing valid Excel workbook."""
        buffer = generate_pembayaran_excel(Pembayaran.objects.all())
        self.assertIsInstance(buffer, io.BytesIO)
        self.assertGreater(buffer.getbuffer().nbytes, 0)

        wb = openpyxl.load_workbook(buffer)
        self.assertEqual(wb.active.title, "Pembayaran")
        headers = [cell.value for cell in wb.active[1]]
        self.assertIn("ID", headers)
        self.assertIn("Nama", headers)
        self.assertIn("No. Rumah", headers)
        self.assertIn("Layanan", headers)
        self.assertIn("Kasir", headers)

    def test_excel_export_kasir_username_no_attribute_error(self):
        """Excel export reads cashier username directly from AbstractUser without AttributeError."""
        buffer = export_pembayaran_to_excel(Pembayaran.objects.filter(pk=self.pembayaran.pk))
        wb = openpyxl.load_workbook(buffer)
        ws = wb.active
        # Row 2 contains the data
        row_values = [cell.value for cell in ws[2]]
        self.assertIn("kasir_export", row_values)

    def test_pdf_export_returns_valid_bytesio(self):
        """generate_pembayaran_pdf returns io.BytesIO containing valid PDF bytes."""
        data = [
            [
                "Nama Pelanggan", "Alamat Rumah",
                "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                "Jul", "Aug", "Sep", "Okt", "Nov", "Des",
            ],
            ["Hasan", "A-01", "Lunas", "", "", "", "", "", "", "", "", "", "", ""],
        ]
        buffer = generate_pembayaran_pdf(
            layanan="AIR",
            tahun=2026,
            data=data,
            total_pemasukan=25000,
        )
        self.assertIsInstance(buffer, io.BytesIO)
        content = buffer.getvalue()
        self.assertTrue(content.startswith(b"%PDF"))
        self.assertGreater(len(content), 500)

    def test_pdf_export_without_precomputed_data(self):
        """generate_laporan_pembayaran_pdf constructs data from DB query when data=None."""
        buffer = generate_laporan_pembayaran_pdf(layanan="AIR", tahun=2026)
        self.assertIsInstance(buffer, io.BytesIO)
        content = buffer.getvalue()
        self.assertTrue(content.startswith(b"%PDF"))
