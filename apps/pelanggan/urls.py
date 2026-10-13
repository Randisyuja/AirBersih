from django.urls import path, include
from apps.pelanggan.views import (
    DaftarPelanggan,
    TambahPelanggan,
    UpdatePelanggan,
    hapus_pelanggan,
    DaftarLangganan,
    DetailLangganan,
    TambahLangganan,
    UpdateLangganan,
    hapus_langganan,
    get_harga_jenis,
    DaftarTagihan,
    TambahTagihan,
    UpdateTagihan,
    hapus_tagihan,
    generate_tagihan,
)

urlpatterns = [
    # Pelanggan
    path("", DaftarPelanggan.as_view(), name="daftar_pelanggan"),
    path("tambah/", TambahPelanggan.as_view(), name="tambah_pelanggan"),
    path("<int:pk>/edit/", UpdatePelanggan.as_view(), name="edit_pelanggan"),
    path("<int:pk>/update/", UpdatePelanggan.as_view(), name="update_pelanggan"),
    path("<int:pk>/hapus/", hapus_pelanggan, name="hapus_pelanggan"),
    path("<int:pk>/delete/", hapus_pelanggan, name="delete_pelanggan"),

    # Langganan (mendukung nama langganan_create & tambah_langganan, dsb)
    path("langganan/", DaftarLangganan.as_view(), name="daftar_langganan"),
    path("langganan/tambah/", TambahLangganan.as_view(), name="langganan_create"),
    path("langganan/create/", TambahLangganan.as_view(), name="tambah_langganan"),
    path("langganan/<int:pk>/", DetailLangganan.as_view(), name="langganan_detail"),
    path("langganan/<int:pk>/detail/", DetailLangganan.as_view(), name="detail_langganan"),
    path("langganan/<int:pk>/edit/", UpdateLangganan.as_view(), name="langganan_update"),
    path("langganan/<int:pk>/update/", UpdateLangganan.as_view(), name="update_langganan"),
    path("langganan/<int:pk>/hapus/", hapus_langganan, name="langganan_delete"),
    path("langganan/<int:pk>/delete/", hapus_langganan, name="delete_langganan"),

    # AJAX Get Harga Jenis Layanan
    path("jenis-layanan/get-harga-jenis/", get_harga_jenis, name="get_harga_jenis"),
    path("get-harga-jenis/", get_harga_jenis),

    # Tagihan
    path("tagihan/", DaftarTagihan.as_view(), name="daftar_tagihan"),
    path("tagihan/tambah/", TambahTagihan.as_view(), name="tambah_tagihan"),
    path("tagihan/<int:pk>/edit/", UpdateTagihan.as_view(), name="edit_tagihan"),
    path("tagihan/<int:pk>/update/", UpdateTagihan.as_view(), name="update_tagihan"),
    path("tagihan/<int:pk>/hapus/", hapus_tagihan, name="hapus_tagihan"),
    path("tagihan/<int:pk>/delete/", hapus_tagihan, name="delete_tagihan"),
    path("generate-tagihan/", generate_tagihan, name="generate_tagihan"),
]
