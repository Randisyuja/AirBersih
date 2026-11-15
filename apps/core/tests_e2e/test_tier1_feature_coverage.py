from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.core.tests_e2e.base import BaseExcelE2ETestCase, make_xlsx_file
from apps.layanan.models import JenisLayanan, Layanan
from apps.pelanggan.models import Langganan, Pelanggan
from apps.rumah.models import Rumah

User = get_user_model()


class ExcelExportFeatureTests(BaseExcelE2ETestCase):
    """Tier 1: Feature Coverage for Excel Export across all 6 master entities."""

    def test_export_rumah_returns_valid_excel_with_active_records(self) -> None:
        Rumah.objects.create(rt="01", no_rumah="R-101")
        resp = self.client.get(reverse("export_rumah"))
        rows = self.assert_excel_download_response(
            resp,
            expected_headers=["rt", "no_rumah"],
            min_data_rows=1,
            expected_filename_part="rumah",
        )
        self.assertTrue(any(r[0] == "01" and r[1] == "R-101" for r in rows))

    def test_export_pelanggan_returns_valid_excel_with_active_records(self) -> None:
        rumah = Rumah.objects.create(rt="02", no_rumah="R-102")
        Pelanggan.objects.create(nama="Siti Aminah", no_hp="0812345678", rumah=rumah)
        resp = self.client.get(reverse("export_pelanggan"))
        rows = self.assert_excel_download_response(
            resp,
            expected_headers=["nama", "no_hp", "no_rumah"],
            min_data_rows=1,
            expected_filename_part="pelanggan",
        )
        self.assertTrue(any(r[0] == "Siti Aminah" and r[2] == "R-102" for r in rows))

    def test_export_layanan_returns_valid_excel_with_active_records(self) -> None:
        Layanan.objects.create(nama_layanan="AIR BERSIH")
        resp = self.client.get(reverse("export_layanan"))
        rows = self.assert_excel_download_response(
            resp,
            expected_headers=["nama_layanan"],
            min_data_rows=1,
            expected_filename_part="layanan",
        )
        self.assertTrue(any(r[0] == "AIR BERSIH" for r in rows))

    def test_export_jenis_layanan_returns_valid_excel_with_active_records(self) -> None:
        layanan = Layanan.objects.create(nama_layanan="PDAM DESA")
        JenisLayanan.objects.create(
            layanan=layanan, nama_jenis="Paket Sosial", tarif=20000
        )
        resp = self.client.get(reverse("export_jenis_layanan"))
        rows = self.assert_excel_download_response(
            resp,
            expected_headers=["layanan", "nama_jenis", "tarif"],
            min_data_rows=1,
            expected_filename_part="jenis_layanan",
        )
        self.assertTrue(
            any(r[0] == "PDAM DESA" and r[1] == "Paket Sosial" and r[2] == 20000 for r in rows)
        )

    def test_export_langganan_returns_valid_excel_with_active_records(self) -> None:
        rumah = Rumah.objects.create(rt="03", no_rumah="R-103")
        pelanggan = Pelanggan.objects.create(nama="Joko Susilo", rumah=rumah)
        layanan = Layanan.objects.create(nama_layanan="AIR BERSIH")
        jenis = JenisLayanan.objects.create(layanan=layanan, nama_jenis="Paket Warga", tarif=35000)
        Langganan.objects.create(pelanggan=pelanggan, jenis_layanan=jenis, harga=35000, aktif=True)

        resp = self.client.get(reverse("export_langganan"))
        rows = self.assert_excel_download_response(
            resp,
            expected_headers=["pelanggan", "jenis_layanan", "harga", "aktif"],
            min_data_rows=1,
            expected_filename_part="langganan",
        )
        self.assertTrue(any(r[0] == "Joko Susilo" and r[1] == "Paket Warga" for r in rows))

    def test_export_kasir_and_users_alias_returns_valid_excel(self) -> None:
        User.objects.create_user(
            username="kasir_tier1",
            first_name="Dewi",
            last_name="Lestari",
            email="dewi@example.com",
            no_hp="0899887766",
            is_active=True,
        )
        for route in ["export_users", "export_kasir"]:
            with self.subTest(route=route):
                resp = self.client.get(reverse(route))
                rows = self.assert_excel_download_response(
                    resp,
                    expected_headers=[
                        "username",
                        "first_name",
                        "last_name",
                        "email",
                        "no_hp",
                        "is_active",
                    ],
                    min_data_rows=1,
                )
                self.assertTrue(any(r[0] == "kasir_tier1" for r in rows))


class ExcelTemplateFeatureTests(BaseExcelE2ETestCase):
    """Tier 1: Feature Coverage for Excel Template Download across all 6 master entities."""

    def test_template_rumah_returns_valid_excel_with_headers_and_sample(self) -> None:
        url = self.resolve_url("template_rumah", "/rumah/template/")
        resp = self.client.get(url)
        self.assert_excel_download_response(
            resp,
            expected_headers=["rt", "no_rumah"],
            min_data_rows=1,
            expected_filename_part="template",
        )

    def test_template_pelanggan_returns_valid_excel_with_headers_and_sample(self) -> None:
        url = self.resolve_url("template_pelanggan", "/pelanggan/template/")
        resp = self.client.get(url)
        self.assert_excel_download_response(
            resp,
            expected_headers=["nama", "no_hp", "no_rumah"],
            min_data_rows=1,
            expected_filename_part="template",
        )

    def test_template_layanan_returns_valid_excel_with_headers_and_sample(self) -> None:
        url = self.resolve_url("template_layanan", "/layanan/template/")
        resp = self.client.get(url)
        self.assert_excel_download_response(
            resp,
            expected_headers=["nama_layanan"],
            min_data_rows=1,
            expected_filename_part="template",
        )

    def test_template_jenis_layanan_returns_valid_excel_with_headers_and_sample(self) -> None:
        url = self.resolve_url("template_jenis_layanan", "/layanan/jenis-layanan/template/")
        resp = self.client.get(url)
        self.assert_excel_download_response(
            resp,
            expected_headers=["layanan", "nama_jenis", "tarif"],
            min_data_rows=1,
            expected_filename_part="template",
        )

    def test_template_langganan_returns_valid_excel_with_headers_and_sample(self) -> None:
        url = self.resolve_url("template_langganan", "/pelanggan/langganan/template/")
        resp = self.client.get(url)
        self.assert_excel_download_response(
            resp,
            expected_headers=["pelanggan", "jenis_layanan", "harga", "aktif"],
            min_data_rows=1,
            expected_filename_part="template",
        )

    def test_template_kasir_and_users_alias_returns_valid_excel(self) -> None:
        for route, path in [
            ("template_users", "/users/template/"),
            ("template_kasir", "/kasir/template/"),
        ]:
            with self.subTest(route=route):
                url = self.resolve_url(route, path)
                resp = self.client.get(url)
                self.assert_excel_download_response(
                    resp,
                    expected_headers=[
                        "username",
                        "first_name",
                        "last_name",
                        "email",
                        "no_hp",
                        "is_active",
                    ],
                    min_data_rows=1,
                    expected_filename_part="template",
                )


class ExcelImportFeatureTests(BaseExcelE2ETestCase):
    """Tier 1: Feature Coverage for Excel Import across all 6 master entities."""

    def test_import_rumah_persists_records(self) -> None:
        upload = make_xlsx_file(["rt", "no_rumah"], [["05", "K-12"]])
        resp = self.client.post(reverse("import_rumah"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Rumah.objects.filter(rt="05", no_rumah="K-12").exists())

    def test_import_pelanggan_persists_records(self) -> None:
        rumah = Rumah.objects.create(rt="05", no_rumah="K-15")
        upload = make_xlsx_file(
            ["nama", "no_hp", "no_rumah"],
            [["Agus Setiawan", "0813998877", "K-15"]],
        )
        resp = self.client.post(reverse("import_pelanggan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Pelanggan.objects.filter(nama="Agus Setiawan", rumah=rumah).exists()
        )

    def test_import_layanan_persists_records(self) -> None:
        upload = make_xlsx_file(["nama_layanan"], [["Pengelolaan Sampah"]])
        resp = self.client.post(reverse("import_layanan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Layanan.objects.filter(nama_layanan="PENGELOLAAN SAMPAH").exists())

    def test_import_jenis_layanan_persists_records(self) -> None:
        layanan = Layanan.objects.create(nama_layanan="AIR BERSIH")
        upload = make_xlsx_file(
            ["layanan", "nama_jenis", "tarif"],
            [["Air Bersih", "Paket Niaga", 120000]],
        )
        resp = self.client.post(reverse("import_jenis_layanan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            JenisLayanan.objects.filter(
                layanan=layanan, nama_jenis="Paket Niaga", tarif=120000
            ).exists()
        )

    def test_import_langganan_persists_records(self) -> None:
        rumah = Rumah.objects.create(rt="04", no_rumah="K-18")
        pelanggan = Pelanggan.objects.create(nama="Rina Marlina", rumah=rumah)
        layanan = Layanan.objects.create(nama_layanan="AIR BERSIH")
        jenis = JenisLayanan.objects.create(layanan=layanan, nama_jenis="Paket Regular", tarif=40000)

        upload = make_xlsx_file(
            ["pelanggan", "jenis_layanan", "harga", "aktif"],
            [["Rina Marlina", "Paket Regular", 40000, "Ya"]],
        )
        resp = self.client.post(reverse("import_langganan"), {"file": upload}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Langganan.objects.filter(
                pelanggan=pelanggan, jenis_layanan=jenis, harga=40000, aktif=True
            ).exists()
        )

    def test_import_kasir_and_users_alias_persists_records(self) -> None:
        for route, username in [
            ("import_users", "kasir_user_1"),
            ("import_kasir", "kasir_user_2"),
        ]:
            with self.subTest(route=route):
                upload = make_xlsx_file(
                    ["username", "first_name", "last_name", "email", "no_hp", "is_active"],
                    [[username, "Petugas", "Satu", f"{username}@test.com", "0811223344", "Ya"]],
                )
                resp = self.client.post(reverse(route), {"file": upload}, follow=True)
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(User.objects.filter(username=username).exists())


class ExcelAuthSecurityTests(BaseExcelE2ETestCase):
    """Tier 1: Verify authentication protection on all export and import endpoints."""

    def setUp(self) -> None:
        super().setUp()
        self.client.logout()

    def test_unauthenticated_export_redirects_to_login(self) -> None:
        routes = [
            "export_rumah",
            "export_pelanggan",
            "export_layanan",
            "export_jenis_layanan",
            "export_langganan",
            "export_users",
            "export_kasir",
        ]
        for route in routes:
            with self.subTest(route=route):
                resp = self.client.get(reverse(route))
                self.assertEqual(resp.status_code, 302)
                self.assertIn("login", resp.url.lower())

    def test_unauthenticated_import_redirects_to_login(self) -> None:
        routes = [
            "import_rumah",
            "import_pelanggan",
            "import_layanan",
            "import_jenis_layanan",
            "import_langganan",
            "import_users",
            "import_kasir",
        ]
        upload = make_xlsx_file(["col"], [["val"]])
        for route in routes:
            with self.subTest(route=route):
                resp = self.client.post(reverse(route), {"file": upload})
                self.assertEqual(resp.status_code, 302)
                self.assertIn("login", resp.url.lower())
