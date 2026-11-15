from django.test import TestCase
from django.db import IntegrityError
from apps.pelanggan.models import Pelanggan
from apps.pelanggan.forms import PelangganForm
from apps.rumah.models import Rumah


class PelangganBarcodeTests(TestCase):
    def setUp(self):
        self.rumah = Rumah.objects.create(rt="01", no_rumah="A-01")

    def test_barcode_auto_generation_on_save(self):
        """Pelanggan created without barcode receives auto-generated PLG{pk:05d}."""
        p = Pelanggan.objects.create(nama="Ahmad", no_hp="081111", rumah=self.rumah)
        self.assertIsNotNone(p.barcode)
        self.assertEqual(p.barcode, f"PLG{p.id_pelanggan:05d}")

    def test_explicit_barcode_preserved(self):
        """Custom barcode provided at creation is preserved."""
        p = Pelanggan.objects.create(nama="Budi", barcode="CUSTOM_BARCODE_123")
        self.assertEqual(p.barcode, "CUSTOM_BARCODE_123")
        p.nama = "Budi Updated"
        p.save()
        p.refresh_from_db()
        self.assertEqual(p.barcode, "CUSTOM_BARCODE_123")

    def test_barcode_uniqueness_enforced(self):
        """Duplicate barcode raises IntegrityError."""
        Pelanggan.objects.create(nama="User 1", barcode="DUP_001")
        with self.assertRaises(IntegrityError):
            Pelanggan.objects.create(nama="User 2", barcode="DUP_001")

    def test_barcode_indexed(self):
        """Pelanggan.barcode field has db_index=True or unique=True."""
        field = Pelanggan._meta.get_field("barcode")
        self.assertTrue(field.unique)
        self.assertTrue(field.db_index)

    def test_pelanggan_form_barcode_optional(self):
        """PelangganForm allows barcode to be optional."""
        form = PelangganForm(data={"rumah": self.rumah.id_rumah, "nama": "Citra", "no_hp": "0819999", "barcode": ""})
        self.assertTrue(form.is_valid(), form.errors)
        saved_pelanggan = form.save()
        self.assertTrue(saved_pelanggan.barcode.startswith("PLG"))
