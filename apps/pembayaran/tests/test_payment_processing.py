"""Unit tests for payment processing service and atomic settlement (Milestone 1)."""

from django.test import TestCase
from django.utils import timezone
from apps.layanan.models import JenisLayanan, Layanan
from apps.pelanggan.models import Pelanggan, Tagihan
from apps.pembayaran.choices import StatusChoice
from apps.pembayaran.exceptions.payment_exceptions import (
    CustomerNotFoundError,
    PaymentAlreadySettledError,
    PaymentValidationError,
    TagihanNotFoundError,
)
from apps.pembayaran.models import Pembayaran
from apps.pembayaran.services.barcode_service import pay_due_by_barcode
from apps.pembayaran.services.payment_service import (
    delete_payment,
    record_direct_pembayaran,
    record_payment,
)
from apps.users.models import Kasir


class PaymentServiceTests(TestCase):
    def setUp(self):
        self.kasir = Kasir.objects.create_user(username="kasir1", password="password")
        self.pelanggan = Pelanggan.objects.create(nama="Rahmat", barcode="PLG00100")
        self.layanan = Layanan.objects.create(nama_layanan="AIR")
        self.jenis = JenisLayanan.objects.create(
            layanan=self.layanan,
            nama_jenis="Standar",
            tarif=20000,
        )
        self.tagihan = Tagihan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis,
            bulan=11,
            tahun=2026,
            status_tagihan=StatusChoice.Belum,
            jumlah_bayar=20000,
        )

    def test_record_payment_success_atomic(self):
        """record_payment atomically creates Pembayaran and updates Tagihan to Lunas."""
        pembayaran = record_payment(
            tagihan_id=self.tagihan.id_tagihan,
            jumlah_dibayar=20000,
            metode_pembayaran="TUNAI",
            user=self.kasir,
        )
        self.assertIsNotNone(pembayaran)
        self.assertEqual(pembayaran.status_bayar, StatusChoice.Lunas)
        self.assertEqual(pembayaran.jumlah_bayar, 20000)
        self.assertEqual(pembayaran.kasir, self.kasir)
        self.assertEqual(pembayaran.bulan, 11)
        self.assertEqual(pembayaran.tahun, 2026)

        # Verify Tagihan synchronization
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.status_tagihan, StatusChoice.Lunas)

    def test_record_payment_already_lunas_rejected(self):
        """Attempting to pay an already paid tagihan raises validation error."""
        self.tagihan.status_tagihan = StatusChoice.Lunas
        self.tagihan.save()
        with self.assertRaises(PaymentValidationError):
            record_payment(
                tagihan_id=self.tagihan.id_tagihan,
                jumlah_dibayar=20000,
                metode_pembayaran="TUNAI",
                user=self.kasir,
            )
        # Ensure no orphan Pembayaran was created
        self.assertFalse(Pembayaran.objects.filter(pelanggan=self.pelanggan).exists())

    def test_record_payment_nonexistent_tagihan_raises_error(self):
        """Paying a non-existent tagihan ID raises TagihanNotFoundError."""
        with self.assertRaises(TagihanNotFoundError):
            record_payment(tagihan_id=999999, user=self.kasir)

    def test_record_payment_zero_amount_raises_error(self):
        """Paying with <= 0 amount raises PaymentValidationError."""
        with self.assertRaises(PaymentValidationError):
            record_payment(
                tagihan_id=self.tagihan.id_tagihan,
                jumlah_dibayar=0,
                user=self.kasir,
            )

    def test_record_direct_pembayaran_syncs_tagihan(self):
        """record_direct_pembayaran creates receipt and syncs matching tagihan to Lunas."""
        pembayaran = record_direct_pembayaran(
            pelanggan_id=self.pelanggan.id_pelanggan,
            jenis_layanan_id=self.jenis.id_jenis,
            bulan=11,
            tahun=2026,
            jumlah_bayar=20000,
            kasir=self.kasir,
        )
        self.assertEqual(pembayaran.status_bayar, StatusChoice.Lunas)
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.status_tagihan, StatusChoice.Lunas)

    def test_delete_payment_reverts_tagihan_to_belum(self):
        """delete_payment removes Pembayaran and reverts Tagihan to Belum."""
        pembayaran = record_payment(
            tagihan_id=self.tagihan.id_tagihan,
            user=self.kasir,
        )
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.status_tagihan, StatusChoice.Lunas)

        deleted = delete_payment(pembayaran.id_pembayaran)
        self.assertTrue(deleted)
        self.assertFalse(Pembayaran.objects.filter(pk=pembayaran.id_pembayaran).exists())

        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.status_tagihan, StatusChoice.Belum)

    def test_pay_due_by_barcode_success(self):
        """pay_due_by_barcode verifies barcode and records payment."""
        pembayaran = pay_due_by_barcode(
            barcode="PLG00100",
            tagihan_id=self.tagihan.id_tagihan,
            kasir=self.kasir,
        )
        self.assertEqual(pembayaran.status_bayar, StatusChoice.Lunas)
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.status_tagihan, StatusChoice.Lunas)

    def test_pay_due_by_barcode_mismatch_raises_error(self):
        """pay_due_by_barcode with another customer barcode raises PaymentValidationError."""
        p2 = Pelanggan.objects.create(nama="Other", barcode="PLG00999")
        with self.assertRaises(PaymentValidationError):
            pay_due_by_barcode(
                barcode="PLG00999",
                tagihan_id=self.tagihan.id_tagihan,
                kasir=self.kasir,
            )
