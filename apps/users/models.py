from django.contrib.auth.hashers import identify_hasher, make_password
from django.contrib.auth.models import AbstractUser
from django.db import models


class Kasir(AbstractUser):
    no_hp = models.CharField(max_length=20, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("!"):
            try:
                identify_hasher(self.password)
            except ValueError:
                self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username
