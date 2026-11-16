from django.core.exceptions import ValidationError
from django.db import models


class Layanan(models.Model):
    id_layanan = models.AutoField(primary_key=True)
    nama_layanan = models.CharField(max_length=50)  # WiFi, Air

    def __str__(self):
        return self.nama_layanan

    def clean(self):
        if Layanan.objects.filter(
                nama_layanan__iexact=self.nama_layanan
        ).exclude(pk=self.pk).exists():
            raise ValidationError({
                "nama_layanan": "Nama layanan sudah ada."
            })

    def save(self, *args, **kwargs):
        if self.nama_layanan:
            self.nama_layanan = self.nama_layanan.upper()
        super().save(*args, **kwargs)


class JenisLayanan(models.Model):
    id_jenis = models.AutoField(primary_key=True)
    layanan = models.ForeignKey(Layanan, on_delete=models.CASCADE, related_name="jenis_layanan")
    nama_jenis = models.CharField(max_length=50)  # Contoh: WiFi Paket 115
    tarif = models.IntegerField(null=True, blank=True, default=0)

    def save(self, *args, **kwargs):
        if self.tarif is None:
            self.tarif = 0
        super().save(*args, **kwargs)

    def __str__(self):
        if self.tarif and self.tarif > 0:
            return f"{self.layanan.nama_layanan} - {self.nama_jenis} (Rp {self.tarif:,})".replace(",", ".")
        return f"{self.layanan.nama_layanan} - {self.nama_jenis} (Tarif Manual / Meteran)"
