from django.contrib import admin
from .models import Layanan, JenisLayanan


@admin.register(Layanan)
class LayananAdmin(admin.ModelAdmin):
    search_fields = ('nama_layanan',)


@admin.register(JenisLayanan)
class JenisLayananAdmin(admin.ModelAdmin):
    search_fields = ('nama_jenis', 'layanan__nama_layanan')
    list_display = ('nama_jenis', 'layanan', 'tarif')
