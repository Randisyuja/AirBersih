from django.urls import path
from .views import (DaftarPembayaran, TambahPembayaran, UpdatePembayaran, hapus_pembayaran, load_jenis_layanan,
                    export_pembayaran_excel, export_pembayaran_pdf, laporan_tahunan)

urlpatterns = [
    path("", DaftarPembayaran.as_view(), name="daftar_pembayaran"),
    path("tambah/", TambahPembayaran.as_view(), name="tambah_pembayaran"),
    path("<int:pk>/edit/", UpdatePembayaran.as_view(), name="edit_pembayaran"),
    path("<int:pk>/hapus/", hapus_pembayaran, name="hapus_pembayaran"),
    path("ajax/load-jenis-layanan/", load_jenis_layanan, name="ajax_load_jenis_layanan"),
    path("pembayaran/export/excel/", export_pembayaran_excel, name="export_pembayaran_excel"),
    path("pembayaran/export/pdf/", export_pembayaran_pdf, name="export_pembayaran_pdf"),
    path("laporan/", laporan_tahunan, name="laporan_tahunan"),

]
