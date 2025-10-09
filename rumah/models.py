from django.db import models


class Rumah(models.Model):
    id_rumah = models.AutoField(primary_key=True)
    rt = models.CharField(max_length=5)               # contoh: "01", "02"
    no_rumah = models.CharField(max_length=10, unique=True)        # contoh: "A1", "B12"

    class Meta:
        unique_together = ("rt", "no_rumah")  # RT + Nomor Rumah harus unik

    def __str__(self):
        return f"RT {self.rt} - No {self.no_rumah}"

    @property
    def status(self):
        """Status dihitung otomatis"""
        return "Dihuni" if hasattr(self, "penghuni") else "Kosong"
