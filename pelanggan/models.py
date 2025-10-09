from django.db import models
from rumah.models import Rumah
from layanan.models import JenisLayanan


class Pelanggan(models.Model):
    id_pelanggan = models.AutoField(primary_key=True)
    rumah = models.OneToOneField(Rumah, on_delete=models.PROTECT, null=True, related_name="penghuni")
    nama = models.CharField(max_length=100)
    no_hp = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.nama} - {self.rumah.no_rumah if self.rumah else 'Tanpa Rumah'}"


class Langganan(models.Model):
    pelanggan = models.ForeignKey(Pelanggan, on_delete=models.CASCADE, related_name="langganan")
    jenis_layanan = models.ForeignKey(JenisLayanan, on_delete=models.CASCADE)
    harga = models.IntegerField(blank=False, null=False)
    aktif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.pelanggan.nama} - {self.jenis_layanan.nama_jenis}"

