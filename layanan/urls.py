from django import views
from django.urls import path
from layanan.views import DaftarLayanan, TambahLayanan, UpdateLayanan, hapus_layanan, DaftarJenisLayanan, TambahJenisLayanan, UpdateJenisLayanan, hapus_jenis_layanan

urlpatterns = [
    path("", DaftarLayanan.as_view(), name="daftar_layanan"),
    path("tambah/", TambahLayanan.as_view(), name="tambah_layanan"),
    path("<int:pk>/edit/", UpdateLayanan.as_view(), name="edit_layanan"),
    path("<int:pk>/hapus/", hapus_layanan, name="hapus_layanan"),
    path("jenis-layanan/", DaftarJenisLayanan.as_view(), name="daftar_jenis_layanan"),
    path("jenis-layanan/tambah/", TambahJenisLayanan.as_view(), name="tambah_jenis_layanan"),
    path("jenis-layanan/<int:pk>/edit/", UpdateJenisLayanan.as_view(), name="edit_jenis_layanan"),
    path('jenis-layanan/hapus/<int:pk>/', hapus_jenis_layanan, name='hapus_jenis_layanan'),
]
