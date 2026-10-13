from django.contrib.auth.models import AbstractUser
from django.db import models


class Kasir(AbstractUser):
    no_hp = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.first_name + " " + self.last_name
