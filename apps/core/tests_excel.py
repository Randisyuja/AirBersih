import io

import openpyxl
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.layanan.models import JenisLayanan, Layanan
from apps.pelanggan.models import Langganan, Pelanggan
from apps.rumah.models import Rumah

User = get_user_model()

XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def make_xlsx_upload(
    headers: list[str],
    rows: list[list],
    filename: str = "test.xlsx",
) -> SimpleUploadedFile:
    """Create an in-memory .xlsx SimpleUploadedFile for import tests."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return SimpleUploadedFile(
        filename,
        buf.read(),
        content_type=XLSX_CONTENT_TYPE,
    )


class ExcelExportImportTests(TestCase):
    """Automated tests for Excel export & import across all master data."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="qa_admin",
            password="qa_password_123",
            email="qa@example.com",
            is_staff=True,
            is_superuser=True,
        )
        self.rumah = Rumah.objects.create(rt="01", no_rumah="A-01")
        self.layanan = Layanan.objects.create(nama_layanan="Air Bersih")
        self.jenis_layanan = JenisLayanan.objects.create(
            layanan=self.layanan,
            nama_jenis="Rumah Tangga",
            tarif=50000,
        )
        self.pelanggan = Pelanggan.objects.create(
            nama="Budi Santoso",
            no_hp="081234567890",
            rumah=self.rumah,
        )
        self.langganan = Langganan.objects.create(
            pelanggan=self.pelanggan,
            jenis_layanan=self.jenis_layanan,
            harga=50000,
            aktif=True,
        )
        self.kasir = User.objects.create_user(
            username="kasir_1",
            password="password123",
            first_name="Siti",
            last_name="Aminah",
            email="siti@example.com",
            no_hp="081298765432",
            is_active=True,
        )

    # ------------------------------------------------------------------
    # 1. Permissions (unauthenticated access)
    # ------------------------------------------------------------------
    def test_unauthenticated_export_redirects_to_login(self) -> None:
        export_routes = [
            "export_rumah",
            "export_layanan",
            "export_jenis_layanan",
            "export_pelanggan",
            "export_langganan",
            "export_users",
        ]
        for route in export_routes:
            with self.subTest(route=route):
                resp = self.client.get(reverse(route))
                self.assertEqual(resp.status_code, 302)
                self.assertIn("login", resp.url.lower())

    def test_unauthenticated_import_redirects_to_login(self) -> None:
        import_routes = [
            "import_rumah",
            "import_layanan",
            "import_jenis_layanan",
            "import_pelanggan",
            "import_langganan",
            "import_users",
        ]
        for route in import_routes:
            with self.subTest(route=route):
                upload = make_xlsx_upload(["col"], [["val"]])
                resp = self.client.post(reverse(route), {"file": upload})
                self.assertEqual(resp.status_code, 302)
                self.assertIn("login", resp.url.lower())

    # ------------------------------------------------------------------
    # 2. Export Happy Path
    # ------------------------------------------------------------------
    def _assert_export_xlsx(
        self, route: str, expected_headers: list[str]
    ) -> list[list]:
        self.client.force_login(self.user)
        resp = self.client.get(reverse(route))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], XLSX_CONTENT_TYPE)
        wb = openpyxl.load_workbook(io.BytesIO(resp.content))
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        self.assertGreaterEqual(len(rows), 2)
        self.assertEqual(list(rows[0]), expected_headers)
        return [list(r) for r in rows[1:]]

    def test_export_all_master_data_happy_path(self) -> None:
        cases = [
            ("export_rumah", ["rt", "no_rumah"]),
            ("export_layanan", ["nama_layanan"]),
            ("export_jenis_layanan", ["layanan", "nama_jenis", "tarif"]),
            ("export_pelanggan", ["nama", "no_hp", "no_rumah"]),
            ("export_langganan", ["pelanggan", "jenis_layanan", "harga", "aktif"]),
            (
                "export_users",
                ["username", "first_name", "last_name", "email", "no_hp", "is_active"],
            ),
        ]
        for route, headers in cases:
            with self.subTest(route=route):
                data_rows = self._assert_export_xlsx(route, headers)
                self.assertGreaterEqual(len(data_rows), 1)

    # ------------------------------------------------------------------
    # 3. Import Happy Path
    # ------------------------------------------------------------------
    def test_import_rumah_happy_path(self) -> None:
        self.client.force_login(self.user)
        upload = make_xlsx_upload(["rt", "no_rumah"], [["02", "B-02"]])
        resp = self.client.post(reverse("import_rumah"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Rumah.objects.filter(rt="02", no_rumah="B-02").exists())

    def test_import_layanan_happy_path(self) -> None:
        self.client.force_login(self.user)
        upload = make_xlsx_upload(["nama_layanan"], [["Kebersihan"]])
        resp = self.client.post(reverse("import_layanan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Layanan.objects.filter(nama_layanan="KEBERSIHAN").exists())

    def test_import_jenis_layanan_happy_path(self) -> None:
        self.client.force_login(self.user)
        upload = make_xlsx_upload(
            ["layanan", "nama_jenis", "tarif"],
            [["Air Bersih", "Komersial", 100000]],
        )
        resp = self.client.post(
            reverse("import_jenis_layanan"), {"file": upload}, follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            JenisLayanan.objects.filter(
                layanan=self.layanan, nama_jenis="Komersial", tarif=100000
            ).exists()
        )

    def test_import_pelanggan_happy_path(self) -> None:
        self.client.force_login(self.user)
        self.pelanggan.delete()
        upload = make_xlsx_upload(
            ["nama", "no_hp", "no_rumah"],
            [["Andi Wijaya", "081111222333", "A-01"]],
        )
        resp = self.client.post(
            reverse("import_pelanggan"), {"file": upload}, follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Pelanggan.objects.filter(nama="Andi Wijaya", rumah=self.rumah).exists()
        )

    def test_import_langganan_happy_path(self) -> None:
        self.client.force_login(self.user)
        rumah2 = Rumah.objects.create(rt="03", no_rumah="C-03")
        pelanggan2 = Pelanggan.objects.create(
            nama="Citra Dewi", no_hp="082222333444", rumah=rumah2
        )
        upload = make_xlsx_upload(
            ["pelanggan", "jenis_layanan", "harga", "aktif"],
            [["Citra Dewi", "Rumah Tangga", 55000, "Ya"]],
        )
        resp = self.client.post(
            reverse("import_langganan"), {"file": upload}, follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Langganan.objects.filter(
                pelanggan=pelanggan2, jenis_layanan=self.jenis_layanan, harga=55000
            ).exists()
        )

    def test_import_users_happy_path(self) -> None:
        self.client.force_login(self.user)
        upload = make_xlsx_upload(
            ["username", "first_name", "last_name", "email", "no_hp", "is_active"],
            [["kasir_2", "Budi", "Hartono", "budi@example.com", "085555666777", "Ya"]],
        )
        resp = self.client.post(reverse("import_users"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(User.objects.filter(username="kasir_2").exists())

    # ------------------------------------------------------------------
    # 4. Invalid File & Missing Columns
    # ------------------------------------------------------------------
    def test_import_invalid_file_extension_rejected(self) -> None:
        self.client.force_login(self.user)
        bad_file = SimpleUploadedFile(
            "not_excel.txt", b"hello world", content_type="text/plain"
        )
        initial_count = Rumah.objects.count()
        resp = self.client.post(reverse("import_rumah"), {"file": bad_file}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Rumah.objects.count(), initial_count)
        msgs = [str(m) for m in resp.context["messages"]]
        self.assertTrue(any(msgs), "Expected error flash message for invalid file")

    def test_import_corrupted_xlsx_rejected(self) -> None:
        self.client.force_login(self.user)
        bad_xlsx = SimpleUploadedFile(
            "corrupt.xlsx", b"not-a-zip-file", content_type=XLSX_CONTENT_TYPE
        )
        initial_count = Layanan.objects.count()
        resp = self.client.post(
            reverse("import_layanan"), {"file": bad_xlsx}, follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Layanan.objects.count(), initial_count)
        msgs = [str(m) for m in resp.context["messages"]]
        self.assertTrue(any(msgs), "Expected error flash message for corrupt xlsx")

    def test_import_missing_columns_rejected(self) -> None:
        self.client.force_login(self.user)
        upload = make_xlsx_upload(["rt"], [["03"]])  # missing 'no_rumah'
        initial_count = Rumah.objects.count()
        resp = self.client.post(reverse("import_rumah"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Rumah.objects.count(), initial_count)
        msgs = [str(m) for m in resp.context["messages"]]
        self.assertTrue(any(msgs), "Expected error flash message for missing columns")
