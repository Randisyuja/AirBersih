from django.urls import path, include
from pelanggan.views import (DaftarPelanggan, TambahPelanggan, UpdatePelanggan, hapus_pelanggan, DaftarLangganan,
                             DetailLangganan, TambahLangganan, UpdateLangganan, hapus_langganan, get_harga_jenis,
                             DaftarTagihan, TambahTagihan, UpdateTagihan, hapus_tagihan, generate_tagihan)

urlpatterns = [
    path("", DaftarPelanggan.as_view(), name="daftar_pelanggan"),
    path("tambah/", TambahPelanggan.as_view(), name="tambah_pelanggan"),
    path("<int:pk>/", include([
        path("edit/", UpdatePelanggan.as_view(), name="edit_pelanggan"),
        path("hapus/", hapus_pelanggan, name="hapus_pelanggan"),
    ])),
    path("langganan/", DaftarLangganan.as_view(), name="daftar_langganan"),
    path("langganan/tambah/", TambahLangganan.as_view(), name="langganan_create"),
    path("langganan/<int:pk>/", include([
        path("", DetailLangganan.as_view(), name="langganan_detail"),
        path("edit/", UpdateLangganan.as_view(), name="langganan_update"),
        path("hapus/", hapus_langganan, name="langganan_delete"),
    ])),
    path("jenis-layanan/get-harga-jenis/", get_harga_jenis, name="get_harga_jenis"),
    path("tagihan/", DaftarTagihan.as_view(), name="daftar_tagihan"),

    path("tagihan/tambah/", TambahTagihan.as_view(), name="tambah_tagihan"),
    path("tagihan/<int:pk>/", include([
        path("edit/", UpdateTagihan.as_view(), name="edit_tagihan"),
        path("hapus/", hapus_tagihan, name="hapus_tagihan"),
    ])),
    path("generate-tagihan/", generate_tagihan, name="generate_tagihan"),
]
