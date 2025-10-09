from django.db import models


class StatusChoice(models.TextChoices):
    Lunas = "Lunas", "Lunas"
    Belum = "Belum", "Belum Lunas"


class BulanChoice(models.IntegerChoices):
    JANUARI = 1, "Januari"
    FEBRUARI = 2, "Februari"
    MARET = 3, "Maret"
    APRIL = 4, "April"
    MEI = 5, "Mei"
    JUNI = 6, "Juni"
    JULI = 7, "Juli"
    AGUSTUS = 8, "Agustus"
    SEPTEMBER = 9, "September"
    OKTOBER = 10, "Oktober"
    NOVEMBER = 11, "November"
    DESEMBER = 12, "Desember"
