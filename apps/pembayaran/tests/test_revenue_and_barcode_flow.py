"""Automated tests for M2 (Revenue Analytics & Reports) and M4 (Barcode Payment UI & API)."""

import json
from django.test import TestCase
from django.urls import reverse
from apps.layanan.models import JenisLayanan, Layanan
from apps.pelanggan.models import Langganan, Pelanggan, Tagihan
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.models import Pembayaran
from apps.pembayaran.selectors.report_selectors import get_service_payment_matrix
from apps.pembayaran.selectors.revenue_selectors import (
    get_annual_revenue,
    get_monthly_revenue_breakdown,
    get_monthly_revenue_for_month,
)
from apps.rumah.models import Rumah
from apps.users.models import Kasir


class RevenueAndBarcodeFlowTests(TestCase):
    """Verifies revenue selectors, report views, and barcode scan-to-pay endpoints."""

    def setUp(self):
        self.user = Kasir.objects.create_user(
            username="kasir_argon", password="password123"
        )
        self.client.force_login(self.user)

        self.layanan_air = Layanan.objects.create(nama_layanan="AIR")
        self.layanan_wifi = Layanan.objects.create(nama_layanan="WIFI")

        self.jenis_air = JenisLayanan.objects.create(
            layanan=self.layanan_air, nama_jenis="Air Rumah Tangga", tarif=30000
        )
        self.jenis_wifi = JenisLayanan.objects.create(
            layanan=self.layanan_wifi, nama_jenis="WiFi 20Mbps", tarif=100000
        )

        self.rumah = Rumah.objects.create(rt="05", no_rumah="B-10")
        self.pelanggan = Pelanggan.objects.create(
            nama="Siti Aminah",
            no_hp="081234567890",
            rumah=self.rumah,
            barcode="PLG99001",
        )

        self.langganan_air = Langganan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_air,
            harga=30000,
            aktif=True,
        )
        self.langganan_wifi = Langganan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_wifi,
            harga=100000,
            aktif=True,
        )

        self.tagihan_air_jan = Tagihan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_air,
            bulan=1,
            tahun=2026,
            jumlah_bayar=30000,
            status_tagihan=StatusChoice.Belum,
        )
        self.tagihan_wifi_feb = Tagihan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_wifi,
            bulan=2,
            tahun=2026,
            jumlah_bayar=100000,
            status_tagihan=StatusChoice.Belum,
        )

    def test_revenue_selectors_monthly_and_annual_calculations(self):
        """get_annual_revenue and get_monthly_revenue_breakdown compute exact totals per service."""
        Pembayaran.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_air,
            bulan=1,
            tahun=2026,
            jumlah_bayar=30000,
            status_bayar=StatusChoice.Lunas,
            kasir=self.user,
        )
        Pembayaran.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_air,
            bulan=3,
            tahun=2026,
            jumlah_bayar=30000,
            status_bayar=StatusChoice.Lunas,
            kasir=self.user,
        )
        Pembayaran.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_wifi,
            bulan=2,
            tahun=2026,
            jumlah_bayar=100000,
            status_bayar=StatusChoice.Lunas,
            kasir=self.user,
        )

        self.assertEqual(get_annual_revenue("AIR", 2026), 60000)
        self.assertEqual(get_annual_revenue("WIFI", 2026), 100000)

        air_monthly = get_monthly_revenue_breakdown("AIR", 2026)
        self.assertEqual(len(air_monthly), 12)
        self.assertEqual(air_monthly[0], 30000)
        self.assertEqual(air_monthly[1], 0)
        self.assertEqual(air_monthly[2], 30000)
        self.assertEqual(get_monthly_revenue_for_month("AIR", 2026, 3), 30000)

    def test_service_payment_matrix_reflects_paid_and_unpaid_months(self):
        """get_service_payment_matrix marks paid months as Lunas and unpaid as Belum."""
        Pembayaran.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_air,
            bulan=1,
            tahun=2026,
            jumlah_bayar=30000,
            status_bayar=StatusChoice.Lunas,
            kasir=self.user,
        )
        matrix = get_service_payment_matrix("AIR", 2026)
        self.assertEqual(len(matrix), 1)
        self.assertEqual(matrix[0]["pelanggan"], "Siti Aminah")
        self.assertEqual(matrix[0]["status_bulan"][0], "Lunas")
        self.assertEqual(matrix[0]["status_bulan"][1], "Belum")

    def test_laporan_tahunan_renders_chart_month_filter_and_annual_total(self):
        """GET /pembayaran/laporan/AIR/?tahun=2026&bulan=1 renders chart, filter, and KPIs."""
        Pembayaran.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_air,
            bulan=1,
            tahun=2026,
            jumlah_bayar=30000,
            status_bayar=StatusChoice.Lunas,
            kasir=self.user,
        )
        url = reverse("laporan_tahunan", kwargs={"layanan": "AIR"})
        response = self.client.get(url, {"tahun": 2026, "bulan": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_pemasukan_tahunan"], 30000)
        self.assertEqual(response.context["selected_bulan"], 1)
        self.assertEqual(response.context["selected_month_revenue"], 30000)
        self.assertContains(response, 'id="monthlyRevenueChart"')
        self.assertContains(response, 'id="filterBulanSelect"')
        self.assertContains(response, 'id="cardTotalPemasukanTahunan"')

    def test_pay_by_barcode_api_single_and_pay_all(self):
        """POST /pembayaran/api/pay-barcode/ settles single due and pay_all=true."""
        url = reverse("pay_by_barcode_api")
        res1 = self.client.post(
            url,
            data=json.dumps(
                {"barcode": "PLG99001", "tagihan_id": self.tagihan_air_jan.id_tagihan}
            ),
            content_type="application/json",
        )
        self.assertEqual(res1.status_code, 200)
        body1 = res1.json()
        self.assertEqual(body1["status"], "success")
        self.tagihan_air_jan.refresh_from_db()
        self.assertEqual(self.tagihan_air_jan.status_tagihan, StatusChoice.Lunas)
        self.assertEqual(len(body1["data"]["dues"]), 1)

        res2 = self.client.post(
            url,
            data=json.dumps({"barcode": "PLG99001", "pay_all": True}),
            content_type="application/json",
        )
        self.assertEqual(res2.status_code, 200)
        body2 = res2.json()
        self.assertEqual(body2["status"], "success")
        self.assertEqual(body2["data"]["total_due"], 0)
        self.tagihan_wifi_feb.refresh_from_db()
        self.assertEqual(self.tagihan_wifi_feb.status_tagihan, StatusChoice.Lunas)

    def test_barcode_scanner_modal_rendered_on_payment_pages(self):
        """Dashboard, Tambah Pembayaran, and Daftar Pembayaran include #barcodeScannerModal."""
        for route_name in ("dashboard", "tambah_pembayaran", "daftar_pembayaran"):
            res = self.client.get(reverse(route_name))
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, 'id="barcodeScannerModal"')

    def test_langganan_kode_pelanggan_auto_generated_and_member_card_qr(self):
        """Langganan auto-generates unique kode_pelanggan (MBR...) and serves QR SVG & Member Card."""
        self.assertTrue(self.langganan_air.kode_pelanggan.startswith("MBR"))
        self.assertTrue(self.langganan_wifi.kode_pelanggan.startswith("MBR"))
        self.assertNotEqual(
            self.langganan_air.kode_pelanggan, self.langganan_wifi.kode_pelanggan
        )

        qr_res = self.client.get(
            reverse("langganan_qr_svg", kwargs={"pk": self.langganan_air.pk})
        )
        self.assertEqual(qr_res.status_code, 200)
        self.assertEqual(qr_res["Content-Type"], "image/svg+xml")
        self.assertIn(b"<svg", qr_res.content)

        card_res = self.client.get(
            reverse("cetak_kartu_member", kwargs={"pk": self.langganan_air.pk})
        )
        self.assertEqual(card_res.status_code, 200)
        self.assertContains(card_res, self.pelanggan.nama)
        self.assertContains(card_res, self.rumah.no_rumah)
        self.assertContains(card_res, self.pelanggan.no_hp)
        self.assertContains(card_res, self.langganan_air.kode_pelanggan)

    def test_scan_and_pay_by_langganan_kode_pelanggan_and_thermal_receipt(self):
        """Scanning Langganan.kode_pelanggan resolves subscription details and payment returns thermal receipt."""
        scan_url = reverse("scan_barcode_api")
        res_scan = self.client.get(
            scan_url, {"code": self.langganan_wifi.kode_pelanggan}
        )
        self.assertEqual(res_scan.status_code, 200)
        scan_data = res_scan.json()
        self.assertEqual(scan_data["customer"]["nama"], "Siti Aminah")
        self.assertIsNotNone(scan_data["subscription"])
        self.assertEqual(
            scan_data["subscription"]["kode_pelanggan"],
            self.langganan_wifi.kode_pelanggan,
        )
        self.assertEqual(
            scan_data["subscription"]["jenis_layanan_id"], self.jenis_wifi.id_jenis
        )
        self.assertEqual(scan_data["subscription"]["harga"], 100000)

        pay_url = reverse("pay_by_barcode_api")
        res_pay = self.client.post(
            pay_url,
            data=json.dumps(
                {
                    "barcode": self.langganan_wifi.kode_pelanggan,
                    "tagihan_id": self.tagihan_wifi_feb.id_tagihan,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(res_pay.status_code, 200)
        pay_body = res_pay.json()
        self.assertIn("receipt_url", pay_body)
        self.assertIn("receipt_id", pay_body)

        struk_res = self.client.get(pay_body["receipt_url"])
        self.assertEqual(struk_res.status_code, 200)
        self.assertContains(struk_res, "Siti Aminah")
        self.assertContains(struk_res, "WiFi 20Mbps")
        self.assertContains(struk_res, "Print Struk Thermal")

        struk_qr_res = self.client.get(
            reverse("pembayaran_qr_svg", kwargs={"pk": pay_body["receipt_id"]})
        )
        self.assertEqual(struk_qr_res.status_code, 200)
        self.assertEqual(struk_qr_res["Content-Type"], "image/svg+xml")
