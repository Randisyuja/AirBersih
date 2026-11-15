"""Unit tests for barcode resolution selector and scan API (Milestone 1)."""

from django.test import TestCase
from django.urls import reverse
from apps.layanan.models import JenisLayanan, Layanan
from apps.pelanggan.models import Langganan, Pelanggan, Tagihan
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.selectors.barcode_selectors import (
    get_customer_dues_by_barcode,
    get_pelanggan_by_barcode,
)
from apps.rumah.models import Rumah
from apps.users.models import Kasir


class BarcodeResolutionSelectorTests(TestCase):
    def setUp(self):
        self.rumah = Rumah.objects.create(rt="01", no_rumah="B-05")
        self.pelanggan = Pelanggan.objects.create(
            nama="Dewi Sartika",
            no_hp="08123456",
            rumah=self.rumah,
            barcode="PLG00050",
        )
        self.layanan_air = Layanan.objects.create(nama_layanan="AIR")
        self.layanan_wifi = Layanan.objects.create(nama_layanan="WIFI")
        self.jenis_air = JenisLayanan.objects.create(
            layanan=self.layanan_air,
            nama_jenis="Rumah Tangga",
            tarif=25000,
        )
        self.jenis_wifi = JenisLayanan.objects.create(
            layanan=self.layanan_wifi,
            nama_jenis="20 Mbps",
            tarif=100000,
        )
        # Active subscriptions
        Langganan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_air,
            harga=25000,
            aktif=True,
        )
        Langganan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_wifi,
            harga=100000,
            aktif=True,
        )
        # Pending dues
        self.tagihan1 = Tagihan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_air,
            bulan=10,
            tahun=2026,
            status_tagihan=StatusChoice.Belum,
            jumlah_bayar=25000,
        )
        self.tagihan2 = Tagihan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_wifi,
            bulan=10,
            tahun=2026,
            status_tagihan=StatusChoice.Belum,
            jumlah_bayar=100000,
        )

    def test_get_customer_dues_by_barcode_with_pending_dues(self):
        """Selector resolves customer info, active tariffs, pending dues, and total sum."""
        dto = get_customer_dues_by_barcode("PLG00050")
        self.assertIsNotNone(dto)
        self.assertEqual(dto.pelanggan_id, self.pelanggan.id_pelanggan)
        self.assertEqual(dto.nama, "Dewi Sartika")
        self.assertEqual(dto.alamat, "B-05")
        self.assertEqual(dto.barcode, "PLG00050")
        self.assertEqual(len(dto.tariffs), 2)
        self.assertEqual(len(dto.pending_dues), 2)
        self.assertEqual(dto.total_due, 125000)

    def test_paid_dues_excluded_from_pending_dues(self):
        """Paid tagihan records are not included in pending dues."""
        self.tagihan1.status_tagihan = StatusChoice.Lunas
        self.tagihan1.save()
        dto = get_customer_dues_by_barcode("PLG00050")
        self.assertIsNotNone(dto)
        self.assertEqual(len(dto.pending_dues), 1)
        self.assertEqual(dto.pending_dues[0].id, self.tagihan2.id_tagihan)
        self.assertEqual(dto.total_due, 100000)

    def test_no_pending_dues_returns_empty_list_and_zero_total(self):
        """Customer with no unpaid tagihan returns empty dues list and total_due 0."""
        self.tagihan1.status_tagihan = StatusChoice.Lunas
        self.tagihan1.save()
        self.tagihan2.status_tagihan = StatusChoice.Lunas
        self.tagihan2.save()
        dto = get_customer_dues_by_barcode("PLG00050")
        self.assertIsNotNone(dto)
        self.assertEqual(dto.pending_dues, [])
        self.assertEqual(dto.total_due, 0)

    def test_non_existent_barcode_returns_none(self):
        """Non-existent barcode returns None."""
        dto = get_customer_dues_by_barcode("NONEXISTENT_999")
        self.assertIsNone(dto)

    def test_customer_without_rumah_handles_gracefully(self):
        """Customer without associated rumah returns fallback address without AttributeError."""
        p_no_house = Pelanggan.objects.create(
            nama="Eko",
            rumah=None,
            barcode="PLG_NOHOUSE",
        )
        dto = get_customer_dues_by_barcode("PLG_NOHOUSE")
        self.assertIsNotNone(dto)
        self.assertEqual(dto.alamat, "-")


class BarcodeScanAPITests(TestCase):
    def setUp(self):
        self.user = Kasir.objects.create_user(
            username="kasir_test",
            password="password123",
        )
        self.rumah = Rumah.objects.create(rt="02", no_rumah="C-12")
        self.pelanggan = Pelanggan.objects.create(
            nama="Budi Santoso",
            rumah=self.rumah,
            barcode="PLG00012",
        )
        self.layanan = Layanan.objects.create(nama_layanan="AIR")
        self.jenis = JenisLayanan.objects.create(
            layanan=self.layanan,
            nama_jenis="Rumah Tangga",
            tarif=30000,
        )
        Langganan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis,
            harga=30000,
            aktif=True,
        )
        self.tagihan = Tagihan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis,
            bulan=11,
            tahun=2026,
            status_tagihan=StatusChoice.Belum,
            jumlah_bayar=30000,
        )

    def test_scan_barcode_success_json_contract(self):
        """GET /pembayaran/api/scan-barcode/?code=PLG00012 returns exact expected JSON structure."""
        self.client.force_login(self.user)
        resp = self.client.get(reverse("api_scan_barcode"), {"code": "PLG00012"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["customer"]["nama"], "Budi Santoso")
        self.assertEqual(data["customer"]["alamat"], "C-12")
        self.assertEqual(data["customer"]["barcode"], "PLG00012")
        self.assertEqual(len(data["tariffs"]), 1)
        self.assertEqual(len(data["dues"]), 1)
        self.assertEqual(data["dues"][0]["id"], self.tagihan.id_tagihan)
        self.assertEqual(data["total_due"], 30000)

    def test_scan_barcode_alias_name(self):
        """reverse('scan_barcode_api') also resolves and returns 200."""
        self.client.force_login(self.user)
        resp = self.client.get(reverse("scan_barcode_api"), {"code": "PLG00012"})
        self.assertEqual(resp.status_code, 200)

    def test_scan_barcode_not_found(self):
        """GET /pembayaran/api/scan-barcode/ with invalid code returns 404 with error message."""
        self.client.force_login(self.user)
        resp = self.client.get(reverse("api_scan_barcode"), {"code": "UNKNOWN_CODE"})
        self.assertEqual(resp.status_code, 404)
        data = resp.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("tidak ditemukan", data["message"].lower())

    def test_scan_barcode_missing_param_returns_error(self):
        """GET /pembayaran/api/scan-barcode/ without code returns 400 bad request."""
        self.client.force_login(self.user)
        resp = self.client.get(reverse("api_scan_barcode"))
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data["status"], "error")

    def test_scan_barcode_login_required(self):
        """Unauthenticated user accessing scan API is redirected to login."""
        resp = self.client.get(reverse("api_scan_barcode"), {"code": "PLG00012"})
        self.assertEqual(resp.status_code, 302)
