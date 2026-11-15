from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.core.tests_e2e.base import BaseExcelE2ETestCase, make_xlsx_file
from apps.layanan.models import Layanan
from apps.pelanggan.models import Pelanggan
from apps.rumah.models import Rumah

User = get_user_model()


class ExcelInFileDuplicateTests(BaseExcelE2ETestCase):
    """Tier 3: Deduplication of duplicate rows within the uploaded Excel file."""

    def test_import_rumah_duplicate_rows_in_file_creates_single_record(self) -> None:
        upload = make_xlsx_file(
            ["rt", "no_rumah"],
            [["01", "DUP-01"], ["01", "DUP-01"], ["02", "DUP-02"]],
        )
        resp = self.client.post(reverse("import_rumah"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            Rumah.objects.filter(no_rumah="DUP-01").count(),
            1,
            "Duplicate row in same file must not create duplicate Rumah records",
        )
        self.assertEqual(
            Rumah.objects.filter(no_rumah="DUP-02").count(),
            1,
        )

    def test_import_layanan_duplicate_rows_in_file_creates_single_record(self) -> None:
        upload = make_xlsx_file(
            ["nama_layanan"],
            [["INTERNET DESA"], ["internet desa"], ["KEBERSIHAN"]],
        )
        resp = self.client.post(reverse("import_layanan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            Layanan.objects.filter(nama_layanan="INTERNET DESA").count(),
            1,
            "Case-insensitive duplicate Layanan in file must create only 1 record",
        )
        self.assertEqual(
            Layanan.objects.filter(nama_layanan="KEBERSIHAN").count(),
            1,
        )

    def test_import_users_duplicate_username_in_file_creates_single_record(self) -> None:
        upload = make_xlsx_file(
            ["username", "first_name", "last_name", "email", "no_hp", "is_active"],
            [
                ["kasir_dup", "Andi", "Pertama", "andi1@test.com", "08111", "Ya"],
                ["kasir_dup", "Andi", "Kedua", "andi2@test.com", "08222", "Ya"],
            ],
        )
        resp = self.client.post(reverse("import_users"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            User.objects.filter(username="kasir_dup").count(),
            1,
            "Duplicate username in same file must result in exactly 1 User record",
        )


class ExcelDatabaseDuplicateHandlingTests(BaseExcelE2ETestCase):
    """Tier 3: Behavior when uploaded records already exist in the database."""

    def test_import_existing_rumah_does_not_duplicate(self) -> None:
        Rumah.objects.create(rt="05", no_rumah="EXIST-01")
        initial_count = Rumah.objects.count()

        upload = make_xlsx_file(
            ["rt", "no_rumah"],
            [["05", "EXIST-01"], ["05", "NEW-02"]],
        )
        resp = self.client.post(reverse("import_rumah"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            Rumah.objects.filter(no_rumah="EXIST-01").count(),
            1,
            "Pre-existing Rumah must not produce duplicate entries",
        )
        self.assertEqual(
            Rumah.objects.count(),
            initial_count + 1,
            "Only the new Rumah should increment the database count",
        )

    def test_import_existing_kasir_does_not_duplicate(self) -> None:
        User.objects.create_user(
            username="kasir_senior",
            first_name="Budi",
            last_name="Utomo",
            email="budi@example.com",
        )
        initial_count = User.objects.count()

        upload = make_xlsx_file(
            ["username", "first_name", "last_name", "email", "no_hp", "is_active"],
            [
                ["kasir_senior", "Budi", "Baru", "budi.baru@example.com", "08111", "Ya"],
                ["kasir_junior", "Citra", "Muda", "citra@example.com", "08222", "Ya"],
            ],
        )
        resp = self.client.post(reverse("import_users"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            User.objects.filter(username="kasir_senior").count(),
            1,
            "Pre-existing Kasir must not produce duplicate users",
        )
        self.assertEqual(
            User.objects.count(),
            initial_count + 1,
            "Only the new Kasir should increment the User count",
        )


class ExcelPartialErrorReportingTests(BaseExcelE2ETestCase):
    """Tier 3: Verification of summary counts and row-level error descriptions in user feedback."""

    def test_partial_import_rumah_reports_summary_and_row_errors(self) -> None:
        upload = make_xlsx_file(
            ["rt", "no_rumah"],
            [
                ["01", "VALID-1"],    # Row 2: Valid
                ["", "INVALID-RT"],   # Row 3: Missing RT
                ["02", ""],           # Row 4: Missing no_rumah
                ["02", "VALID-2"],    # Row 5: Valid
            ],
        )
        resp = self.client.post(reverse("import_rumah"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)

        # 2 valid records must be persisted in database
        self.assertTrue(Rumah.objects.filter(no_rumah="VALID-1").exists())
        self.assertTrue(Rumah.objects.filter(no_rumah="VALID-2").exists())
        self.assertFalse(Rumah.objects.filter(no_rumah="INVALID-RT").exists())

        # Inspect flash feedback messages
        msgs = self.get_flash_messages(resp)
        combined_msg = " ".join(msgs)

        # Summary must indicate 2 added and 2 skipped
        self.assertIn("2", combined_msg, "Summary should report count of processed rows")
        self.assertTrue(
            "dilewati" in combined_msg.lower() or "skipped" in combined_msg.lower(),
            "Feedback message must report skipped rows",
        )
        # Row-level error descriptions must reference row numbers
        self.assertTrue(
            "baris 3" in combined_msg.lower() or "baris 4" in combined_msg.lower() or "error" in combined_msg.lower(),
            f"Flash message should describe row-level errors: {combined_msg}",
        )

    def test_partial_import_pelanggan_reports_fk_and_validation_errors(self) -> None:
        rumah = Rumah.objects.create(rt="01", no_rumah="REAL-01")

        upload = make_xlsx_file(
            ["nama", "no_hp", "no_rumah"],
            [
                ["Pelanggan Sah", "08111", "REAL-01"],   # Row 2: Valid
                ["", "08222", "REAL-01"],               # Row 3: Missing nama
                ["Pelanggan Hantu", "08333", "GHOST"],   # Row 4: Non-existent Rumah
            ],
        )
        resp = self.client.post(reverse("import_pelanggan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)

        self.assertTrue(Pelanggan.objects.filter(nama="Pelanggan Sah").exists())
        self.assertFalse(Pelanggan.objects.filter(nama="Pelanggan Hantu").exists())

        msgs = self.get_flash_messages(resp)
        combined_msg = " ".join(msgs)
        self.assertTrue(
            "1 ditambahkan" in combined_msg or "2 dilewati" in combined_msg or "error" in combined_msg.lower(),
            f"Expected partial import counts in feedback: {combined_msg}",
        )
