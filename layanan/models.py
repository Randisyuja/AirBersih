from django.db import models


class Layanan(models.Model):
    id_layanan = models.AutoField(primary_key=True)
    nama_layanan = models.CharField(max_length=50)  # WiFi, Air

    def __str__(self):
        return self.nama_layanan


class JenisLayanan(models.Model):
    id_jenis = models.AutoField(primary_key=True)
    layanan = models.ForeignKey(Layanan, on_delete=models.CASCADE, related_name="jenis_layanan")
    nama_jenis = models.CharField(max_length=50)  # Contoh: WiFi Paket 115
    tarif = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.layanan.nama_layanan} - {self.nama_jenis}"
