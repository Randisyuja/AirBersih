from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.core.tests_e2e.base import (
    BaseExcelE2ETestCase,
    make_corrupt_xlsx_file,
    make_empty_xlsx_file,
    make_xlsx_file,
)
from apps.layanan.models import JenisLayanan, Layanan
from apps.pelanggan.models import Langganan, Pelanggan
from apps.rumah.models import Rumah

User = get_user_model()


class ExcelEmptyFileBoundaryTests(BaseExcelE2ETestCase):
    """Tier 2: Empty files, header-only files, and corrupt payloads."""

    def test_import_empty_file_without_rows_rejected(self) -> None:
        initial_count = Rumah.objects.count()
        empty_upload = make_empty_xlsx_file(include_headers=False)
        resp = self.client.post(reverse("import_rumah"), {"file": empty_upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Rumah.objects.count(), initial_count)
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("kosong" in m.lower() or "header" in m.lower() or "gagal" in m.lower() for m in msgs))

    def test_import_header_only_file_handled_cleanly(self) -> None:
        initial_count = Layanan.objects.count()
        header_only = make_empty_xlsx_file(include_headers=True, headers=["nama_layanan"])
        resp = self.client.post(reverse("import_layanan"), {"file": header_only}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Layanan.objects.count(), initial_count)
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("0 ditambahkan" in m or "selesai" in m.lower() for m in msgs))

    def test_import_corrupted_file_rejected(self) -> None:
        initial_count = Rumah.objects.count()
        corrupt = make_corrupt_xlsx_file()
        resp = self.client.post(reverse("import_rumah"), {"file": corrupt}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Rumah.objects.count(), initial_count)
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("tidak valid" in m.lower() or "rusak" in m.lower() or "gagal" in m.lower() for m in msgs))

    def test_import_file_with_blank_rows_ignored(self) -> None:
        upload = make_xlsx_file(
            ["rt", "no_rumah"],
            [["01", "B-10"], [None, ""], ["  ", None], ["01", "B-11"]],
        )
        resp = self.client.post(reverse("import_rumah"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Rumah.objects.filter(no_rumah="B-10").exists())
        self.assertTrue(Rumah.objects.filter(no_rumah="B-11").exists())


class ExcelHeaderIntegrityTests(BaseExcelE2ETestCase):
    """Tier 2: Missing mandatory columns, malformed headers, and case normalization."""

    def test_import_rumah_missing_no_rumah_column_rejected(self) -> None:
        upload = make_xlsx_file(["rt"], [["01"]])
        resp = self.client.post(reverse("import_rumah"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("kolom wajib tidak ditemukan" in m.lower() or "no_rumah" in m.lower() for m in msgs))

    def test_import_layanan_missing_nama_layanan_column_rejected(self) -> None:
        upload = make_xlsx_file(["kategori_salah"], [["Air"]])
        resp = self.client.post(reverse("import_layanan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("kolom wajib" in m.lower() or "nama_layanan" in m.lower() for m in msgs))

    def test_import_jenis_layanan_missing_tarif_column_rejected(self) -> None:
        upload = make_xlsx_file(["layanan", "nama_jenis"], [["Air Bersih", "Paket A"]])
        resp = self.client.post(reverse("import_jenis_layanan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("kolom wajib" in m.lower() or "tarif" in m.lower() for m in msgs))

    def test_import_pelanggan_missing_nama_column_rejected(self) -> None:
        upload = make_xlsx_file(["no_hp", "no_rumah"], [["08111", "A-01"]])
        resp = self.client.post(reverse("import_pelanggan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("kolom wajib" in m.lower() or "nama" in m.lower() for m in msgs))

    def test_import_case_insensitive_and_padded_headers_succeed(self) -> None:
        upload = make_xlsx_file(["  RT  ", "NO_RUMAH "], [["07", "X-99"]])
        resp = self.client.post(reverse("import_rumah"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Rumah.objects.filter(rt="07", no_rumah="X-99").exists())


class ExcelDataTypeValidationTests(BaseExcelE2ETestCase):
    """Tier 2: Validation of numeric fields, negative values, and empty values."""

    def test_import_jenis_layanan_text_in_numeric_tarif_skipped(self) -> None:
        layanan = Layanan.objects.create(nama_layanan="AIR BERSIH")
        upload = make_xlsx_file(
            ["layanan", "nama_jenis", "tarif"],
            [["Air Bersih", "Paket Typo", "LIMA PULUH RIBU"]],
        )
        resp = self.client.post(reverse("import_jenis_layanan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(JenisLayanan.objects.filter(nama_jenis="Paket Typo").exists())
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("angka" in m.lower() or "tarif" in m.lower() for m in msgs))

    def test_import_jenis_layanan_negative_tarif_skipped(self) -> None:
        layanan = Layanan.objects.create(nama_layanan="AIR BERSIH")
        upload = make_xlsx_file(
            ["layanan", "nama_jenis", "tarif"],
            [["Air Bersih", "Paket Minus", -25000]],
        )
        resp = self.client.post(reverse("import_jenis_layanan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(JenisLayanan.objects.filter(nama_jenis="Paket Minus").exists())
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("negatif" in m.lower() for m in msgs))

    def test_import_langganan_text_in_numeric_harga_skipped(self) -> None:
        rumah = Rumah.objects.create(rt="01", no_rumah="H-01")
        pelanggan = Pelanggan.objects.create(nama="Budi Hartono", rumah=rumah)
        layanan = Layanan.objects.create(nama_layanan="AIR BERSIH")
        jenis = JenisLayanan.objects.create(layanan=layanan, nama_jenis="Paket Budi", tarif=30000)

        upload = make_xlsx_file(
            ["pelanggan", "jenis_layanan", "harga", "aktif"],
            [["Budi Hartono", "Paket Budi", "Gratis", "Ya"]],
        )
        resp = self.client.post(reverse("import_langganan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Langganan.objects.filter(pelanggan=pelanggan).exists())
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("angka" in m.lower() or "harga" in m.lower() for m in msgs))

    def test_import_langganan_negative_harga_skipped(self) -> None:
        rumah = Rumah.objects.create(rt="01", no_rumah="H-02")
        pelanggan = Pelanggan.objects.create(nama="Siti Hartati", rumah=rumah)
        layanan = Layanan.objects.create(nama_layanan="AIR BERSIH")
        jenis = JenisLayanan.objects.create(layanan=layanan, nama_jenis="Paket Siti", tarif=30000)

        upload = make_xlsx_file(
            ["pelanggan", "jenis_layanan", "harga", "aktif"],
            [["Siti Hartati", "Paket Siti", -10000, "Ya"]],
        )
        resp = self.client.post(reverse("import_langganan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Langganan.objects.filter(pelanggan=pelanggan).exists())
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("negatif" in m.lower() for m in msgs))

    def test_import_empty_mandatory_field_values_skipped(self) -> None:
        upload = make_xlsx_file(
            ["rt", "no_rumah"],
            [["", "NO_RT_EMPTY"], ["01", ""]],
        )
        resp = self.client.post(reverse("import_rumah"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Rumah.objects.filter(no_rumah="NO_RT_EMPTY").exists())
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("dilewati" in m.lower() or "error" in m.lower() for m in msgs))


class ExcelForeignKeyAndDomainConstraintTests(BaseExcelE2ETestCase):
    """Tier 2: Foreign key validation and domain rules (occupied rumah)."""

    def test_import_pelanggan_non_existent_rumah_skipped(self) -> None:
        upload = make_xlsx_file(
            ["nama", "no_hp", "no_rumah"],
            [["Pelanggan Fiktif", "08129999", "RUMAH_HANTU_999"]],
        )
        resp = self.client.post(reverse("import_pelanggan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Pelanggan.objects.filter(nama="Pelanggan Fiktif").exists())
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("tidak ditemukan" in m.lower() for m in msgs))

    def test_import_jenis_layanan_non_existent_layanan_skipped(self) -> None:
        upload = make_xlsx_file(
            ["layanan", "nama_jenis", "tarif"],
            [["LAYANAN_TIDAK_ADA", "Paket Gaib", 50000]],
        )
        resp = self.client.post(reverse("import_jenis_layanan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(JenisLayanan.objects.filter(nama_jenis="Paket Gaib").exists())
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("tidak ditemukan" in m.lower() for m in msgs))

    def test_import_langganan_non_existent_pelanggan_skipped(self) -> None:
        layanan = Layanan.objects.create(nama_layanan="AIR BERSIH")
        jenis = JenisLayanan.objects.create(layanan=layanan, nama_jenis="Paket Normal", tarif=50000)
        upload = make_xlsx_file(
            ["pelanggan", "jenis_layanan", "harga", "aktif"],
            [["Orang Tidak Terdaftar", "Paket Normal", 50000, "Ya"]],
        )
        resp = self.client.post(reverse("import_langganan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Langganan.objects.filter(jenis_layanan=jenis).exists())
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("tidak ditemukan" in m.lower() for m in msgs))

    def test_import_langganan_non_existent_jenis_layanan_skipped(self) -> None:
        rumah = Rumah.objects.create(rt="01", no_rumah="L-01")
        pelanggan = Pelanggan.objects.create(nama="Hendra Gunawan", rumah=rumah)
        upload = make_xlsx_file(
            ["pelanggan", "jenis_layanan", "harga", "aktif"],
            [["Hendra Gunawan", "PAKET_TIDAK_TERDAFTAR", 50000, "Ya"]],
        )
        resp = self.client.post(reverse("import_langganan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Langganan.objects.filter(pelanggan=pelanggan).exists())
        msgs = self.get_flash_messages(resp)
        self.assertTrue(any("tidak ditemukan" in m.lower() for m in msgs))

    def test_import_pelanggan_occupied_rumah_preserves_existing_resident(self) -> None:
        rumah = Rumah.objects.create(rt="01", no_rumah="OCCUPIED-01")
        existing_pelanggan = Pelanggan.objects.create(
            nama="Penghuni Sah", no_hp="0811111111", rumah=rumah
        )

        upload = make_xlsx_file(
            ["nama", "no_hp", "no_rumah"],
            [["Penghuni Penyerobot", "0822222222", "OCCUPIED-01"]],
        )
        resp = self.client.post(reverse("import_pelanggan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)

        # Existing resident must be preserved in database
        existing_pelanggan.refresh_from_db()
        self.assertEqual(
            existing_pelanggan.nama,
            "Penghuni Sah",
            "Existing Pelanggan name must not be overwritten by occupied house import",
        )
        self.assertEqual(
            existing_pelanggan.no_hp,
            "0811111111",
            "Existing Pelanggan phone must not be overwritten",
        )
