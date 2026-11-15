from django.db import models
from apps.rumah.models import Rumah
from apps.layanan.models import JenisLayanan
from apps.pembayaran.choices import StatusChoice, BulanChoice


class Pelanggan(models.Model):
    id_pelanggan = models.AutoField(primary_key=True)
    rumah = models.OneToOneField(Rumah, on_delete=models.PROTECT, null=True, related_name="penghuni")
    nama = models.CharField(max_length=100)
    no_hp = models.CharField(max_length=20, blank=True, null=True)
    barcode = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Barcode / Kode Pelanggan",
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.barcode:
            self.barcode = f"PLG{self.pk:05d}"
            Pelanggan.objects.filter(pk=self.pk).update(barcode=self.barcode)

    def __str__(self):
        if self.rumah:
            return f"{self.nama} (RT {self.rumah.rt} - No {self.rumah.no_rumah})"
        return f"{self.nama} (Tanpa Rumah)"


class Langganan(models.Model):
    pelanggan = models.ForeignKey(Pelanggan, on_delete=models.CASCADE, related_name="langganan")
    jenis_layanan = models.ForeignKey(JenisLayanan, on_delete=models.CASCADE)
    harga = models.IntegerField(blank=False, null=False)
    aktif = models.BooleanField(default=True)
    kode_pelanggan = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Kode Member / Pelanggan",
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.kode_pelanggan:
            self.kode_pelanggan = f"MBR{self.pk:05d}"
            Langganan.objects.filter(pk=self.pk).update(kode_pelanggan=self.kode_pelanggan)

    def __str__(self):
        return f"{self.pelanggan.nama} - {self.jenis_layanan.nama_jenis} ({self.kode_pelanggan or '-'})"


class Tagihan(models.Model):
    id_tagihan = models.AutoField(primary_key=True)
    pelanggan = models.ForeignKey(Pelanggan, on_delete=models.CASCADE, related_name="tagihan")
    jenis_layanan = models.ForeignKey(JenisLayanan, on_delete=models.CASCADE)
    bulan = models.PositiveSmallIntegerField(choices=BulanChoice.choices)
    tahun = models.PositiveSmallIntegerField()
    status_tagihan = models.CharField(max_length=10, choices=StatusChoice.choices, default="Belum")
    jumlah_bayar = models.IntegerField()

    def __str__(self):
        return f"{self.pelanggan.nama} - {self.jenis_layanan} - {self.bulan}/{self.tahun}"
