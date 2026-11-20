from django.contrib.auth.hashers import identify_hasher
from django.test import TestCase
from django.urls import reverse
from apps.users.models import Kasir


class UserPasswordHashingAndLoginTests(TestCase):
    def setUp(self):
        self.admin = Kasir.objects.create_user(
            username="admin_test",
            password="adminpassword123",
            is_superuser=True,
            is_staff=True,
        )

    def test_tambah_kasir_hashes_password_and_allows_login(self):
        """Creating an account via TambahKasir hashes the password and allows the user to log in."""
        self.client.force_login(self.admin)
        res = self.client.post(
            reverse("tambah_users"),
            {
                "username": "petugas_baru",
                "first_name": "Petugas",
                "last_name": "Satu",
                "email": "petugas@example.com",
                "no_hp": "08123456789",
                "password": "secretpassword123",
                "is_active": True,
            },
        )
        self.assertEqual(res.status_code, 302)

        user = Kasir.objects.get(username="petugas_baru")
        # Password stored in DB must be hashed (identifiable by Django hasher)
        hasher = identify_hasher(user.password)
        self.assertIsNotNone(hasher)
        self.assertNotEqual(user.password, "secretpassword123")
        self.assertTrue(user.check_password("secretpassword123"))

        # Must be able to log in with username and password
        self.client.logout()
        login_ok = self.client.login(username="petugas_baru", password="secretpassword123")
        self.assertTrue(login_ok)

    def test_update_kasir_hashes_new_password_and_allows_login(self):
        """Updating a Kasir via UpdateKasir hashes the password instead of storing plain text."""
        kasir = Kasir.objects.create_user(username="revaaprina", password="oldpassword")
        self.client.force_login(self.admin)

        res = self.client.post(
            reverse("update_users", kwargs={"pk": kasir.pk}),
            {
                "username": "revaaprina",
                "first_name": "Reva",
                "last_name": "Aprina",
                "email": "reva@example.com",
                "no_hp": "0811223344",
                "password": "123456",
                "is_active": True,
            },
        )
        self.assertEqual(res.status_code, 302)

        kasir.refresh_from_db()
        self.assertNotEqual(kasir.password, "123456")
        self.assertTrue(kasir.check_password("123456"))

        self.client.logout()
        login_ok = self.client.login(username="revaaprina", password="123456")
        self.assertTrue(login_ok)

    def test_direct_model_save_hashes_plaintext_password(self):
        """Saving a Kasir instance with a plain-text password automatically hashes it before DB storage."""
        kasir = Kasir(username="direct_user", password="123456")
        kasir.save()
        kasir.refresh_from_db()
        self.assertNotEqual(kasir.password, "123456")
        self.assertTrue(kasir.check_password("123456"))

    def test_dashboard_tunggakan_modals_and_auto_refresh_endpoint(self):
        """Dashboard renders unpaid customer modals per service and /laporan-recent/ returns live KPI JSON."""
        from django.utils import timezone
        from apps.layanan.models import JenisLayanan, Layanan
        from apps.pelanggan.models import Pelanggan, Tagihan
        from apps.pembayaran.choices import StatusChoice
        from apps.rumah.models import Rumah

        rumah = Rumah.objects.create(rt="05", no_rumah="D1-01")
        pelanggan = Pelanggan.objects.create(nama="Warga Belum Bayar", rumah=rumah, barcode="PLG00999")
        layanan_wifi = Layanan.objects.create(nama_layanan="WIFI")
        jenis_wifi = JenisLayanan.objects.create(layanan=layanan_wifi, nama_jenis="WiFi 165", tarif=165000)

        now = timezone.now()
        Tagihan.objects.create(
            pelanggan=pelanggan,
            jenis_layanan=jenis_wifi,
            bulan=now.month,
            tahun=now.year,
            status_tagihan=StatusChoice.Belum,
            jumlah_bayar=165000,
        )

        self.client.force_login(self.admin)
        dash_res = self.client.get(reverse("dashboard"))
        self.assertEqual(dash_res.status_code, 200)
        self.assertContains(dash_res, "modalTunggakan_WIFI")
        self.assertContains(dash_res, "Warga Belum Bayar")
        self.assertNotContains(dash_res, 'id="formLoketBayar"')

        recent_res = self.client.get(reverse("laporan_recent"))
        self.assertEqual(recent_res.status_code, 200)
        data = recent_res.json()
        self.assertIn("html", data)
        self.assertIn("latest_id", data)
        self.assertIn("uang_bulan_ini", data)
        self.assertIn("tunggakan_counts", data)
        self.assertEqual(data["tunggakan_counts"].get("WIFI"), 1)
