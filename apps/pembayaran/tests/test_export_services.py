"""Unit tests for Excel and PDF export services (Milestone 1)."""

import io
import openpyxl
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.layanan.models import JenisLayanan, Layanan
from apps.pelanggan.models import Langganan, Pelanggan
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.exports.excel_export import (
    export_laporan_tahunan_excel,
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
        from apps.core.permissions import sync_default_groups
        groups = sync_default_groups()
        self.kasir = Kasir.objects.create_user(
            username="kasir_export",
            password="password",
        )
        self.kasir.groups.add(groups["Kasir"])
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
        self.langganan = Langganan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis,
            harga=25000,
            aktif=True,
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

    def test_annual_report_excel_export_contains_payment_nominals(self):
        """Annual report Excel export fills month columns with actual payment nominals, not 'Lunas'."""
        buffer = export_laporan_tahunan_excel(layanan="AIR", tahun=2026)
        self.assertIsInstance(buffer, io.BytesIO)
        wb = openpyxl.load_workbook(buffer)
        ws = wb.active
        self.assertEqual(ws.title, "AIR_2026")

        # Row 3 contains headers: No, Nama Pelanggan, No. Rumah, Jan, Feb, ... Total
        header_vals = [cell.value for cell in ws[3]]
        self.assertEqual(header_vals[0], "No")
        self.assertEqual(header_vals[1], "Nama Pelanggan")
        self.assertEqual(header_vals[3], "Jan")
        self.assertEqual(header_vals[4], "Feb")

        # Row 4 contains Hasan's data: Jan should be 25000 (nominal), Feb should be 0
        row_vals = [cell.value for cell in ws[4]]
        self.assertEqual(row_vals[1], "Hasan")
        self.assertEqual(row_vals[2], "A-01")
        self.assertEqual(row_vals[3], 25000)  # Month 1 paid nominal
        self.assertEqual(row_vals[4], 0)      # Month 2 unpaid
        self.assertEqual(row_vals[15], 25000) # Total row

    def test_annual_report_excel_view_endpoint(self):
        """HTTP endpoint /pembayaran/export/excel/<layanan>/<tahun>/ returns 200 with Excel content."""
        self.client.force_login(self.kasir)
        url = reverse("export_laporan_tahunan_excel", kwargs={"layanan": "AIR", "tahun": 2026})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn("Laporan_Pembayaran_AIR_2026.xlsx", response["Content-Disposition"])
