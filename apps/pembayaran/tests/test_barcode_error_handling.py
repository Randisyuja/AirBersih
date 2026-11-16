"""Tests for barcode payment API error handling and notification payloads (ADR 002)."""

import json
from django.test import TestCase
from django.urls import reverse
from apps.layanan.models import JenisLayanan, Layanan
from apps.pelanggan.models import Langganan, Pelanggan, Tagihan
from apps.pembayaran.choices import StatusChoice
from apps.rumah.models import Rumah
from apps.users.models import Kasir


class BarcodePaymentErrorHandlingTests(TestCase):
    def setUp(self):
        self.kasir = Kasir.objects.create_user(username="kasir_test", password="password")
        self.client.force_login(self.kasir)

        self.rumah = Rumah.objects.create(rt="05", no_rumah="C-01")
        self.pelanggan = Pelanggan.objects.create(nama="Budi Santoso", rumah=self.rumah, barcode="PLG00100")
        self.layanan = Layanan.objects.create(nama_layanan="AIR")
        self.jenis = JenisLayanan.objects.create(layanan=self.layanan, nama_jenis="Rumah Tangga", tarif=35000)
        self.langganan = Langganan.objects.create(pelanggan=self.pelanggan, jenis_layanan=self.jenis, harga=35000, aktif=True)

        self.tagihan = Tagihan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis,
            bulan=1,
            tahun=2026,
            jumlah_bayar=35000,
            status_tagihan=StatusChoice.Belum,
        )

    def test_scan_barcode_empty_code_returns_400(self):
        url = reverse("scan_barcode_api")
        res = self.client.get(url, {"code": ""})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["status"], "error")

    def test_scan_barcode_nonexistent_code_returns_404(self):
        url = reverse("scan_barcode_api")
        res = self.client.get(url, {"code": "NONEXISTENT"})
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["status"], "error")

    def test_pay_barcode_non_post_returns_405(self):
        url = reverse("pay_by_barcode_api")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 405)

    def test_pay_barcode_empty_barcode_returns_400(self):
        url = reverse("pay_by_barcode_api")
        res = self.client.post(url, data=json.dumps({"barcode": ""}), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_pay_barcode_nonexistent_tagihan_id_returns_404(self):
        url = reverse("pay_by_barcode_api")
        payload = {"barcode": self.pelanggan.barcode, "tagihan_id": 99999}
        res = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["status"], "error")

    def test_pay_barcode_already_settled_tagihan_returns_400(self):
        self.tagihan.status_tagihan = StatusChoice.Lunas
        self.tagihan.save()
        url = reverse("pay_by_barcode_api")
        payload = {"barcode": self.pelanggan.barcode, "tagihan_id": self.tagihan.id_tagihan}
        res = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["status"], "error")
        self.assertIn("Tagihan sudah lunas", res.json()["message"])

    def test_pay_barcode_success_returns_summary_for_modal(self):
        url = reverse("pay_by_barcode_api")
        payload = {"barcode": self.pelanggan.barcode, "tagihan_id": self.tagihan.id_tagihan}
        res = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["customer_name"], "Budi Santoso")
        self.assertEqual(body["settled_count"], 1)
        self.assertEqual(body["settled_total"], 35000)
        self.assertIn("receipt_url", body)

    def test_pay_barcode_dynamic_metered_tariff_manual_amount(self):
        """Metered service with 0 default tariff accepts manual monthly nominal via custom_amounts."""
        jenis_meteran = JenisLayanan.objects.create(
            layanan=self.layanan, nama_jenis="Air Meteran", tarif=0
        )
        tagihan_meteran = Tagihan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=jenis_meteran,
            bulan=2,
            tahun=2026,
            jumlah_bayar=0,
            status_tagihan=StatusChoice.Belum,
        )
        url = reverse("pay_by_barcode_api")

        # Paying without manual nominal should fail validation
        res_fail = self.client.post(
            url,
            data=json.dumps({"barcode": self.pelanggan.barcode, "tagihan_id": tagihan_meteran.id_tagihan}),
            content_type="application/json",
        )
        self.assertEqual(res_fail.status_code, 400)

        # Paying with manual nominal succeeds and records exact manual amount
        res_ok = self.client.post(
            url,
            data=json.dumps({
                "barcode": self.pelanggan.barcode,
                "tagihan_ids": [tagihan_meteran.id_tagihan],
                "custom_amounts": {str(tagihan_meteran.id_tagihan): 47500},
            }),
            content_type="application/json",
        )
        self.assertEqual(res_ok.status_code, 200)
        body = res_ok.json()
        self.assertEqual(body["settled_total"], 47500)
        tagihan_meteran.refresh_from_db()
        self.assertEqual(tagihan_meteran.status_tagihan, StatusChoice.Lunas)
        self.assertEqual(tagihan_meteran.jumlah_bayar, 47500)

    def test_daftar_pembayaran_search_and_date_filter(self):
        """DaftarPembayaran supports search by name/house/service and date range filtering."""
        from django.utils import timezone
        from apps.pembayaran.models import Pembayaran

        Pembayaran.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis,
            bulan=1,
            tahun=2026,
            status_bayar=StatusChoice.Lunas,
            tgl_pembayaran=timezone.now(),
            jumlah_bayar=35000,
            kasir=self.kasir,
        )
        today_str = timezone.now().strftime("%Y-%m-%d")
        res = self.client.get(
            reverse("daftar_pembayaran"),
            {
                "q": "Budi",
                "layanan": "AIR",
                "jenis_layanan": str(self.jenis.id_jenis),
                "tgl_mulai": today_str,
                "tgl_akhir": today_str,
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Budi Santoso")
        self.assertContains(res, "C-01")

        res_empty = self.client.get(reverse("daftar_pembayaran"), {"q": "TidakAdaNamaIni"})
        self.assertEqual(res_empty.status_code, 200)
        self.assertNotContains(res_empty, "Budi Santoso")

    def test_laporan_tahunan_matrix_has_sticky_columns(self):
        """Annual report matrix table renders sticky classes for Nama Pelanggan and No. Rumah."""
        res = self.client.get(reverse("laporan_tahunan", kwargs={"layanan": "AIR"}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "sticky-col-1")
        self.assertContains(res, "sticky-col-2")
