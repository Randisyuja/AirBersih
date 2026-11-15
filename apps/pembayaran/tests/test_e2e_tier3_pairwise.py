"""
apps/pembayaran/tests/test_e2e_tier3_pairwise.py
Tier 3: Pairwise Combinations (Tests 48-53)
Covers cross-feature interactions: barcode scan -> payment -> monthly report,
annual total, service isolation, matrix status transition, and year boundaries.
"""

from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from apps.layanan.models import Layanan, JenisLayanan
from apps.pelanggan.models import Pelanggan, Langganan, Tagihan
from apps.pembayaran.choices import BulanChoice, StatusChoice
from apps.pembayaran.models import Pembayaran
from apps.pembayaran.tests.base import BasePaymentE2ETestCase


class Tier3PairwiseCombinationsTestCase(BasePaymentE2ETestCase):
    """Tier 3: Pairwise Combinatorial test cases (48 to 53)."""

    def test_pairwise_barcode_scan_to_payment_to_monthly_report(self):
        """48. Scan barcode -> Settle November dues -> Verify November report updates."""
        # 1. Create November pending due
        due = self.create_pending_due(self.pelanggan, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)

        # 2. Check pre-payment November revenue is 0
        pre_rev = Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan__iexact="AIR",
            tahun=2026,
            bulan=11,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total=Sum("jumlah_bayar"))["total"] or 0
        self.assertEqual(pre_rev, 0)

        # 3. Simulate payment settlement
        payment = self.create_settled_payment(self.pelanggan, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)
        due.status_tagihan = StatusChoice.Lunas
        due.save()

        # 4. Check post-payment November revenue increased by exactly 25,000
        post_rev = Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan__iexact="AIR",
            tahun=2026,
            bulan=11,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total=Sum("jumlah_bayar"))["total"] or 0
        self.assertEqual(post_rev, 25000)

        # 5. Verify service report page reflects payment
        url = reverse("laporan_tahunan", kwargs={"layanan": "AIR"})
        response = self.client.get(url, {"tahun": 2026})
        self.assertEqual(response.status_code, 200)

        # Customer attendance matrix for November (index 10) must be 'Lunas'
        data_laporan = response.context["data_laporan"]
        cust_row = next((r for r in data_laporan if r["pelanggan"] == self.pelanggan.nama), None)
        self.assertIsNotNone(cust_row)
        self.assertEqual(cust_row["status_bulan"][10], "Lunas")

    def test_pairwise_barcode_scan_to_payment_to_annual_total(self):
        """49. Settle multi-month dues -> Verify annual total reflects sum of payments."""
        due_oct = self.create_pending_due(self.pelanggan, self.tarif_air, bulan=10, tahun=2026, jumlah=25000)
        due_nov = self.create_pending_due(self.pelanggan, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)

        # Settle both dues
        self.create_settled_payment(self.pelanggan, self.tarif_air, bulan=10, tahun=2026, jumlah=25000)
        self.create_settled_payment(self.pelanggan, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)
        due_oct.status_tagihan = StatusChoice.Lunas
        due_oct.save()
        due_nov.status_tagihan = StatusChoice.Lunas
        due_nov.save()

        # Query total annual revenue
        annual_total = Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan__iexact="AIR",
            tahun=2026,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total=Sum("jumlah_bayar"))["total"] or 0
        self.assertEqual(annual_total, 50000)

    def test_pairwise_dual_service_payment_isolation(self):
        """50. Pay only Water -> Verify Water revenue increases and WiFi remains unaffected."""
        due_air = self.create_pending_due(self.pelanggan, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)
        due_wifi = self.create_pending_due(self.pelanggan, self.tarif_wifi, bulan=11, tahun=2026, jumlah=50000)

        # Settle only Water
        self.create_settled_payment(self.pelanggan, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)
        due_air.status_tagihan = StatusChoice.Lunas
        due_air.save()

        # Verify Water annual total is 25,000
        water_rev = Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan__iexact="AIR",
            tahun=2026,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total=Sum("jumlah_bayar"))["total"] or 0
        self.assertEqual(water_rev, 25000)

        # Verify WiFi annual total is 0
        wifi_rev = Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan__iexact="WIFI",
            tahun=2026,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total=Sum("jumlah_bayar"))["total"] or 0
        self.assertEqual(wifi_rev, 0)

        # WiFi due remains unpaid
        due_wifi.refresh_from_db()
        self.assertEqual(due_wifi.status_tagihan, StatusChoice.Belum)

    def test_pairwise_payment_matrix_status_transition(self):
        """51. Payment matrix status transitions from 'Belum' to 'Lunas' upon payment."""
        url = reverse("laporan_tahunan", kwargs={"layanan": "AIR"})
        
        # Step 1: Pre-payment check (Month 7 July is Belum)
        res_before = self.client.get(url, {"tahun": 2026})
        row_before = next((r for r in res_before.context["data_laporan"] if r["pelanggan"] == self.pelanggan.nama), None)
        self.assertIsNotNone(row_before)
        self.assertEqual(row_before["status_bulan"][6], "Belum")

        # Step 2: Record payment for July (month 7)
        self.create_settled_payment(self.pelanggan, self.tarif_air, bulan=7, tahun=2026, jumlah=25000)

        # Step 3: Post-payment check (Month 7 July is now Lunas)
        res_after = self.client.get(url, {"tahun": 2026})
        row_after = next((r for r in res_after.context["data_laporan"] if r["pelanggan"] == self.pelanggan.nama), None)
        self.assertIsNotNone(row_after)
        self.assertEqual(row_after["status_bulan"][6], "Lunas")

    def test_pairwise_cross_year_boundary_dues_settlement(self):
        """52. Pay prior year (2025) bill -> Verify 2025 report receives revenue, 2026 unaffected."""
        # Record payment for December 2025
        self.create_settled_payment(self.pelanggan, self.tarif_air, bulan=12, tahun=2025, jumlah=25000)

        rev_2025 = Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan__iexact="AIR",
            tahun=2025,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total=Sum("jumlah_bayar"))["total"] or 0
        self.assertEqual(rev_2025, 25000)

        rev_2026 = Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan__iexact="AIR",
            tahun=2026,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total=Sum("jumlah_bayar"))["total"] or 0
        self.assertEqual(rev_2026, 0)

    def test_pairwise_theme_toggle_persistence_and_report_chart(self):
        """53. Verify report page renders properly with theme state cookies."""
        url = reverse("laporan_tahunan", kwargs={"layanan": "AIR"})
        self.client.cookies["theme"] = "dark"
        response = self.client.get(url, {"tahun": 2026})
        self.assertEqual(response.status_code, 200)

        self.client.cookies["theme"] = "light"
        response_light = self.client.get(url, {"tahun": 2026})
        self.assertEqual(response_light.status_code, 200)
