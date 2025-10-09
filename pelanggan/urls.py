from django.urls import path
from pelanggan.views import (DaftarPelanggan, TambahPelanggan, UpdatePelanggan, DeletePelanggan, DaftarLangganan,
                             DetailLangganan, TambahLangganan, UpdateLangganan, DeleteLangganan, get_harga_jenis)

urlpatterns = [
    path("", DaftarPelanggan.as_view(), name="daftar_pelanggan"),
    path("tambah/", TambahPelanggan.as_view(), name="tambah_pelanggan"),
    path("<int:pk>/edit/", UpdatePelanggan.as_view(), name="edit_pelanggan"),
    path("<int:pk>/hapus/", DeletePelanggan.as_view(), name="hapus_pelanggan"),
    path("langganan/", DaftarLangganan.as_view(), name="daftar_langganan"),
    path("langganan/<int:pk>/", DetailLangganan.as_view(), name="langganan_detail"),
    path("langganan/tambah/", TambahLangganan.as_view(), name="langganan_create"),
    path("langganan/<int:pk>/edit/", UpdateLangganan.as_view(), name="langganan_update"),
    path("langganan/<int:pk>/hapus/", DeleteLangganan.as_view(), name="langganan_delete"),
    path("jenis-layanan/get-harga-jenis/", get_harga_jenis, name="get_harga_jenis"),
]
