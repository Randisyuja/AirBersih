from django.urls import path, include
from .views import (DaftarPembayaran, TambahPembayaran, UpdatePembayaran, hapus_pembayaran, load_jenis_layanan,
                    export_pembayaran_excel, export_pembayaran_pdf, laporan_tahunan_air, laporan_tahunan_wifi)

urlpatterns = [
    path("", DaftarPembayaran.as_view(), name="daftar_pembayaran"),
    path("tambah/", TambahPembayaran.as_view(), name="tambah_pembayaran"),
    path("<int:pk>/edit/", UpdatePembayaran.as_view(), name="edit_pembayaran"),
    path("<int:pk>/hapus/", hapus_pembayaran, name="hapus_pembayaran"),
    path("ajax/load-jenis-layanan/", load_jenis_layanan, name="ajax_load_jenis_layanan"),
    path("pembayaran/export/excel/", export_pembayaran_excel, name="export_pembayaran_excel"),
    path("pembayaran/export/pdf/", export_pembayaran_pdf, name="export_pembayaran_pdf"),
    path("laporan/", include([
        path("air/", laporan_tahunan_air, name="laporan_air"),
        path("wifi/", laporan_tahunan_wifi, name="laporan_wifi"),
    ]))

]
