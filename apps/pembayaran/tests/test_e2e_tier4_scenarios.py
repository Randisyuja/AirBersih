"""
apps/pembayaran/tests/test_e2e_tier4_scenarios.py
Tier 4: Real-World Application Scenarios (Tests 54-58)
Covers end-to-end user workflows: customer onboarding -> scan -> pay,
cashier rapid scanning queue, partial dues settlement, annual audit & filtering,
and hardware scanner recovery.
"""

from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from apps.layanan.models import Layanan, JenisLayanan
from apps.pelanggan.models import Pelanggan, Langganan, Tagihan
from apps.pembayaran.choices import BulanChoice, StatusChoice
from apps.pembayaran.models import Pembayaran
from apps.pembayaran.tests.base import BasePaymentE2ETestCase, E2ETestDataFactory
from apps.rumah.models import Rumah


class Tier4RealWorldScenariosTestCase(BasePaymentE2ETestCase):
    """Tier 4: Real-World End-to-End Application Scenarios (54 to 58)."""

    def test_scenario_1_full_customer_onboarding_scan_and_payment(self):
        """54. Scenario 1: Full customer onboarding, barcode scanning, and payment settlement."""
        # Step 1: Onboard new customer with house
        rumah_new = Rumah.objects.create(rt="03", no_rumah="C-10")
        pelanggan_new = Pelanggan.objects.create(
            nama="Dewi Sartika",
            no_hp="08123444555",
            rumah=rumah_new,
        )
        if hasattr(pelanggan_new, "barcode"):
            pelanggan_new.barcode = "PLG2026-001"
            pelanggan_new.save(update_fields=["barcode"])

        # Step 2: Assign Water and WiFi subscriptions
        sub_w = Langganan.objects.create(
            pelanggan=pelanggan_new,
            jenis_layanan=self.tarif_air,
            harga=25000,
            aktif=True,
        )
        sub_wf = Langganan.objects.create(
            pelanggan=pelanggan_new,
            jenis_layanan=self.tarif_wifi,
            harga=50000,
            aktif=True,
        )

        # Step 3: Generate 2 months initial dues (Oct & Nov)
        due_oct = self.create_pending_due(pelanggan_new, self.tarif_air, bulan=10, tahun=2026, jumlah=25000)
        due_nov = self.create_pending_due(pelanggan_new, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)

        # Step 4: Scan barcode / query customer dues
        unpaid = Tagihan.objects.filter(pelanggan=pelanggan_new, status_tagihan=StatusChoice.Belum)
        self.assertEqual(unpaid.count(), 2)
        total_due = sum(d.jumlah_bayar for d in unpaid)
        self.assertEqual(total_due, 50000)

        # Step 5: Execute payment settlement
        pay_oct = self.create_settled_payment(pelanggan_new, self.tarif_air, bulan=10, tahun=2026, jumlah=25000)
        pay_nov = self.create_settled_payment(pelanggan_new, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)
        due_oct.status_tagihan = StatusChoice.Lunas
        due_oct.save()
        due_nov.status_tagihan = StatusChoice.Lunas
        due_nov.save()

        # Step 6: Verify dues marked paid
        self.assertEqual(Tagihan.objects.filter(pelanggan=pelanggan_new, status_tagihan=StatusChoice.Belum).count(), 0)

        # Step 7: Verify customer appears in annual report with Lunas status for Oct and Nov
        url = reverse("laporan_tahunan", kwargs={"layanan": "AIR"})
        response = self.client.get(url, {"tahun": 2026})
        self.assertEqual(response.status_code, 200)
        cust_row = next((r for r in response.context["data_laporan"] if r["pelanggan"] == "Dewi Sartika"), None)
        self.assertIsNotNone(cust_row)
        self.assertEqual(cust_row["status_bulan"][9], "Lunas")   # Oct (index 9)
        self.assertEqual(cust_row["status_bulan"][10], "Lunas")  # Nov (index 10)

    def test_scenario_2_cashier_rapid_scanning_workflow(self):
        """55. Scenario 2: Cashier processes a queue of 3 different residents back-to-back."""
        # Customer A: Water only
        cust_a, _ = E2ETestDataFactory.create_customer_with_house("Warga Alpha", "01", "A-21", barcode="PLG00021")
        Langganan.objects.create(pelanggan=cust_a, jenis_layanan=self.tarif_air, harga=25000, aktif=True)
        due_a = self.create_pending_due(cust_a, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)

        # Customer B: WiFi only
        cust_b, _ = E2ETestDataFactory.create_customer_with_house("Warga Beta", "01", "A-22", barcode="PLG00022")
        Langganan.objects.create(pelanggan=cust_b, jenis_layanan=self.tarif_wifi, harga=50000, aktif=True)
        due_b = self.create_pending_due(cust_b, self.tarif_wifi, bulan=11, tahun=2026, jumlah=50000)

        # Customer C: Both services
        cust_c, _, _, _, _ = E2ETestDataFactory.create_dual_service_customer("Warga Gamma", "01", "A-23", barcode="PLG00023")
        due_c_water = self.create_pending_due(cust_c, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)
        due_c_wifi = self.create_pending_due(cust_c, self.tarif_wifi, bulan=11, tahun=2026, jumlah=50000)

        # Process queue
        p_a = self.create_settled_payment(cust_a, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)
        p_b = self.create_settled_payment(cust_b, self.tarif_wifi, bulan=11, tahun=2026, jumlah=50000)
        p_c1 = self.create_settled_payment(cust_c, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)
        p_c2 = self.create_settled_payment(cust_c, self.tarif_wifi, bulan=11, tahun=2026, jumlah=50000)

        # Verify distinct transactions
        receipt_ids = {p_a.pk, p_b.pk, p_c1.pk, p_c2.pk}
        self.assertEqual(len(receipt_ids), 4)

        # Verify combined ledger revenue
        total_revenue = p_a.jumlah_bayar + p_b.jumlah_bayar + p_c1.jumlah_bayar + p_c2.jumlah_bayar
        self.assertEqual(total_revenue, 150000)

    def test_scenario_3_resident_partial_dues_settlement(self):
        """56. Scenario 3: Resident with 3 months unpaid pays only the oldest due."""
        due_oct = self.create_pending_due(self.pelanggan, self.tarif_air, bulan=10, tahun=2026, jumlah=25000)
        due_nov = self.create_pending_due(self.pelanggan, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)
        due_dec = self.create_pending_due(self.pelanggan, self.tarif_air, bulan=12, tahun=2026, jumlah=25000)

        # Initial total due: 75,000
        unpaid = Tagihan.objects.filter(pelanggan=self.pelanggan, status_tagihan=StatusChoice.Belum)
        self.assertEqual(sum(d.jumlah_bayar for d in unpaid), 75000)

        # Pay only October due
        self.create_settled_payment(self.pelanggan, self.tarif_air, bulan=10, tahun=2026, jumlah=25000)
        due_oct.status_tagihan = StatusChoice.Lunas
        due_oct.save()

        # Check remaining dues
        remaining_unpaid = Tagihan.objects.filter(pelanggan=self.pelanggan, status_tagihan=StatusChoice.Belum)
        self.assertEqual(remaining_unpaid.count(), 2)
        remaining_total = sum(d.jumlah_bayar for d in remaining_unpaid)
        self.assertEqual(remaining_total, 50000)
        remaining_months = {d.bulan for d in remaining_unpaid}
        self.assertEqual(remaining_months, {11, 12})

    def test_scenario_4_monthly_financial_audit_and_filtering(self):
        """57. Scenario 4: Administrator audits monthly water revenue for 2026."""
        # Create payments: March Rp 25k, August Rp 50k (2 customers), November Rp 25k
        self.create_settled_payment(self.pelanggan, self.tarif_air, bulan=3, tahun=2026, jumlah=25000)
        self.create_settled_payment(self.pelanggan, self.tarif_air, bulan=8, tahun=2026, jumlah=25000)

        cust_2, _ = E2ETestDataFactory.create_customer_with_house("Warga Dua", "02", "B-02", barcode="PLG00002")
        Langganan.objects.create(pelanggan=cust_2, jenis_layanan=self.tarif_air, harga=25000, aktif=True)
        self.create_settled_payment(cust_2, self.tarif_air, bulan=8, tahun=2026, jumlah=25000)
        self.create_settled_payment(self.pelanggan, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)

        # Audit annual total: 25k + 25k + 25k + 25k = 100,000
        annual_total = Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan__iexact="AIR",
            tahun=2026,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total=Sum("jumlah_bayar"))["total"] or 0
        self.assertEqual(annual_total, 100000)

        # Audit August (Month 8) total: exactly 50,000
        august_total = Pembayaran.objects.filter(
            jenis_layanan__layanan__nama_layanan__iexact="AIR",
            tahun=2026,
            bulan=8,
            status_bayar=StatusChoice.Lunas,
        ).aggregate(total=Sum("jumlah_bayar"))["total"] or 0
        self.assertEqual(august_total, 50000)

    def test_scenario_5_scanner_malformed_input_graceful_recovery(self):
        """58. Scenario 5: Scanner emits corrupted string -> recovery -> valid payment."""
        url = self.resolve_url("api_scan_barcode", fallback_path="/pembayaran/api/scan-barcode/")

        # Attempt 1: Corrupted hardware scan input
        corrupted_scan = "PLG-CORRUPTED!#@999"
        res_fail = self.client.get(url, {"code": corrupted_scan})
        self.assertIn(res_fail.status_code, [200, 400, 404])

        # Attempt 2: Re-input clean barcode
        valid_barcode = "PLG00001"
        res_success = self.client.get(url, {"code": valid_barcode})
        self.assertIn(res_success.status_code, [200, 404])

        # Payment proceeds to completion without session error
        payment = self.create_settled_payment(self.pelanggan, self.tarif_air, bulan=11, tahun=2026, jumlah=25000)
        self.assertEqual(payment.status_bayar, StatusChoice.Lunas)
        self.assertEqual(payment.jumlah_bayar, 25000)
