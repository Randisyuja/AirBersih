from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.core.tests_e2e.base import BaseExcelE2ETestCase, make_xlsx_file
from apps.layanan.models import JenisLayanan, Layanan
from apps.pelanggan.models import Langganan, Pelanggan
from apps.rumah.models import Rumah

User = get_user_model()


class ExcelRealWorldPipelineTests(BaseExcelE2ETestCase):
    """Tier 4: Sequential master data import pipeline and full export verification."""

    def test_sequential_full_master_data_import_and_export_verification(self) -> None:
        """Simulate complete onboarding: Rumah -> Pelanggan -> Layanan -> Jenis -> Langganan -> Kasir."""
        # ======================================================================
        # Step 1: Import Rumah
        # ======================================================================
        rumah_upload = make_xlsx_file(
            ["rt", "no_rumah"],
            [["05", "RW-01"], ["05", "RW-02"], ["06", "RW-03"]],
            filename="01_rumah.xlsx",
        )
        resp_rumah = self.client.post(reverse("import_rumah"), {"file": rumah_upload}, follow=True)
        self.assertEqual(resp_rumah.status_code, 200)
        self.assertEqual(Rumah.objects.filter(no_rumah__startswith="RW-").count(), 3)

        # ======================================================================
        # Step 2: Import Pelanggan (referencing newly imported Rumah)
        # ======================================================================
        pelanggan_upload = make_xlsx_file(
            ["nama", "no_hp", "no_rumah"],
            [
                ["Agus Riyadi", "08111222333", "RW-01"],
                ["Bambang Pamungkas", "08222333444", "RW-02"],
            ],
            filename="02_pelanggan.xlsx",
        )
        resp_pel = self.client.post(reverse("import_pelanggan"), {"file": pelanggan_upload}, follow=True)
        self.assertEqual(resp_pel.status_code, 200)
        self.assertTrue(Pelanggan.objects.filter(nama="Agus Riyadi", rumah__no_rumah="RW-01").exists())
        self.assertTrue(Pelanggan.objects.filter(nama="Bambang Pamungkas", rumah__no_rumah="RW-02").exists())

        # ======================================================================
        # Step 3: Import Layanan
        # ======================================================================
        layanan_upload = make_xlsx_file(
            ["nama_layanan"],
            [["AIR BERSIH"], ["PENGELOLAAN SAMPAH"]],
            filename="03_layanan.xlsx",
        )
        resp_lay = self.client.post(reverse("import_layanan"), {"file": layanan_upload}, follow=True)
        self.assertEqual(resp_lay.status_code, 200)
        self.assertTrue(Layanan.objects.filter(nama_layanan="AIR BERSIH").exists())
        self.assertTrue(Layanan.objects.filter(nama_layanan="PENGELOLAAN SAMPAH").exists())

        # ======================================================================
        # Step 4: Import Jenis Layanan (referencing newly imported Layanan)
        # ======================================================================
        jenis_upload = make_xlsx_file(
            ["layanan", "nama_jenis", "tarif"],
            [
                ["Air Bersih", "Paket Standar", 30000],
                ["Air Bersih", "Paket Premium", 60000],
            ],
            filename="04_jenis_layanan.xlsx",
        )
        resp_jen = self.client.post(reverse("import_jenis_layanan"), {"file": jenis_upload}, follow=True)
        self.assertEqual(resp_jen.status_code, 200)
        self.assertTrue(JenisLayanan.objects.filter(nama_jenis="Paket Standar", tarif=30000).exists())
        self.assertTrue(JenisLayanan.objects.filter(nama_jenis="Paket Premium", tarif=60000).exists())

        # ======================================================================
        # Step 5: Import Langganan (linking Pelanggan to Jenis Layanan)
        # ======================================================================
        langganan_upload = make_xlsx_file(
            ["pelanggan", "jenis_layanan", "harga", "aktif"],
            [
                ["Agus Riyadi", "Paket Standar", 30000, "Ya"],
                ["Bambang Pamungkas", "Paket Premium", 60000, "Ya"],
            ],
            filename="05_langganan.xlsx",
        )
        resp_lang = self.client.post(reverse("import_langganan"), {"file": langganan_upload}, follow=True)
        self.assertEqual(resp_lang.status_code, 200)
        self.assertTrue(
            Langganan.objects.filter(
                pelanggan__nama="Agus Riyadi", jenis_layanan__nama_jenis="Paket Standar", harga=30000
            ).exists()
        )
        self.assertTrue(
            Langganan.objects.filter(
                pelanggan__nama="Bambang Pamungkas", jenis_layanan__nama_jenis="Paket Premium", harga=60000
            ).exists()
        )

        # ======================================================================
        # Step 6: Import Kasir / Users
        # ======================================================================
        kasir_upload = make_xlsx_file(
            ["username", "first_name", "last_name", "email", "no_hp", "is_active"],
            [
                ["kasir_shift_1", "Doni", "Kusuma", "doni@tirto.id", "08555666777", "Ya"],
                ["kasir_shift_2", "Eka", "Prasetya", "eka@tirto.id", "08777888999", "Ya"],
            ],
            filename="06_kasir.xlsx",
        )
        resp_kas = self.client.post(reverse("import_users"), {"file": kasir_upload}, follow=True)
        self.assertEqual(resp_kas.status_code, 200)
        self.assertTrue(User.objects.filter(username="kasir_shift_1").exists())
        self.assertTrue(User.objects.filter(username="kasir_shift_2").exists())

        # ======================================================================
        # Step 7: Verify Subsequent Excel Exports Reflect Complete Data
        # ======================================================================
        # 1. Export Rumah
        resp_exp_rumah = self.client.get(reverse("export_rumah"))
        rows_rumah = self.assert_excel_download_response(
            resp_exp_rumah, expected_headers=["rt", "no_rumah"], min_data_rows=3
        )
        unit_names = {r[1] for r in rows_rumah}
        self.assertTrue({"RW-01", "RW-02", "RW-03"}.issubset(unit_names))

        # 2. Export Pelanggan
        resp_exp_pel = self.client.get(reverse("export_pelanggan"))
        rows_pel = self.assert_excel_download_response(
            resp_exp_pel, expected_headers=["nama", "no_hp", "no_rumah"], min_data_rows=2
        )
        pel_names = {r[0] for r in rows_pel}
        self.assertTrue({"Agus Riyadi", "Bambang Pamungkas"}.issubset(pel_names))

        # 3. Export Layanan
        resp_exp_lay = self.client.get(reverse("export_layanan"))
        rows_lay = self.assert_excel_download_response(
            resp_exp_lay, expected_headers=["nama_layanan"], min_data_rows=2
        )
        lay_names = {r[0] for r in rows_lay}
        self.assertTrue({"AIR BERSIH", "PENGELOLAAN SAMPAH"}.issubset(lay_names))

        # 4. Export Jenis Layanan
        resp_exp_jen = self.client.get(reverse("export_jenis_layanan"))
        rows_jen = self.assert_excel_download_response(
            resp_exp_jen, expected_headers=["layanan", "nama_jenis", "tarif"], min_data_rows=2
        )
        pkg_names = {r[1] for r in rows_jen}
        self.assertTrue({"Paket Standar", "Paket Premium"}.issubset(pkg_names))

        # 5. Export Langganan
        resp_exp_lang = self.client.get(reverse("export_langganan"))
        rows_lang = self.assert_excel_download_response(
            resp_exp_lang, expected_headers=["pelanggan", "jenis_layanan", "harga", "aktif"], min_data_rows=2
        )
        sub_pels = {r[0] for r in rows_lang}
        self.assertTrue({"Agus Riyadi", "Bambang Pamungkas"}.issubset(sub_pels))

        # 6. Export Kasir
        resp_exp_kas = self.client.get(reverse("export_users"))
        rows_kas = self.assert_excel_download_response(
            resp_exp_kas,
            expected_headers=["username", "first_name", "last_name", "email", "no_hp", "is_active"],
            min_data_rows=2,
        )
        kas_users = {r[0] for r in rows_kas}
        self.assertTrue({"kasir_shift_1", "kasir_shift_2"}.issubset(kas_users))
