from django.db import models
from pelanggan.models import Pelanggan
from layanan.models import JenisLayanan
from users.models import Kasir
from pembayaran.choices import StatusChoice, BulanChoice


class Pembayaran(models.Model):
    id_pembayaran = models.AutoField(primary_key=True)
    pelanggan = models.ForeignKey(Pelanggan, on_delete=models.CASCADE, related_name="pembayaran")
    jenis_layanan = models.ForeignKey(JenisLayanan, on_delete=models.CASCADE)
    kasir = models.ForeignKey(Kasir, on_delete=models.SET_NULL, null=True, blank=True)

    bulan = models.PositiveSmallIntegerField(choices=BulanChoice.choices)  # 1 = Jan, 2 = Feb ...
    tahun = models.PositiveSmallIntegerField()
    status_bayar = models.CharField(max_length=10, choices=StatusChoice.choices, default="Belum")
    tgl_pembayaran = models.DateTimeField(null=True, blank=True)
    jumlah_bayar = models.IntegerField()

    def __str__(self):
        return f"{self.pelanggan.nama} - {self.jenis_layanan} - {self.bulan}/{self.tahun}"
