from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from apps.pelanggan.models import Pelanggan
from apps.rumah.models import Rumah
from apps.users.models import Kasir


class HapusRumahProtectedErrorTests(TestCase):
    def setUp(self):
        self.kasir = Kasir.objects.create_user(username="kasir_rumah", password="password")
        self.client.force_login(self.kasir)
        self.rumah = Rumah.objects.create(rt="06", no_rumah="D3NO2")
        self.pelanggan = Pelanggan.objects.create(
            nama="YONRIZAL",
            rumah=self.rumah,
            barcode="PLG00004",
        )

    def test_hapus_rumah_with_active_pelanggan_catches_protected_error(self):
        """Deleting a Rumah referenced by Pelanggan should catch ProtectedError and set error message."""
        url = reverse("hapus_rumah", kwargs={"pk": self.rumah.pk})
        response = self.client.post(url, follow=True)

        self.assertEqual(response.status_code, 200)
        # Verify the rumah was not deleted
        self.assertTrue(Rumah.objects.filter(pk=self.rumah.pk).exists())

        # Verify friendly error message was dispatched
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Gagal menghapus" in str(m) or "terhubung" in str(m) for m in messages_list))
