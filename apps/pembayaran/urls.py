from django.urls import path
from apps.pembayaran.views import (
    DaftarPembayaran,
    TambahPembayaran,
    UpdatePembayaran,
    hapus_pembayaran,
    load_jenis_layanan,
    export_pembayaran_excel,
    export_pembayaran_pdf,
    laporan_tahunan,
    PembayaranBulananView,
)

urlpatterns = [
    # Daftar & Form Pembayaran
    path("", DaftarPembayaran.as_view(), name="daftar_pembayaran"),
    path("tambah/", TambahPembayaran.as_view(), name="tambah_pembayaran"),
    path("<int:pk>/edit/", UpdatePembayaran.as_view(), name="edit_pembayaran"),
    path("<int:pk>/update/", UpdatePembayaran.as_view(), name="update_pembayaran"),
    path("<int:pk>/hapus/", hapus_pembayaran, name="hapus_pembayaran"),
    path("<int:pk>/delete/", hapus_pembayaran, name="delete_pembayaran"),

    # AJAX Load Jenis Layanan (mendukung kedua format url)
    path("ajax/load-jenis-layanan/", load_jenis_layanan, name="ajax_load_jenis_layanan"),

    # Export Excel (mendukung /export/excel/ dan /pembayaran/export/excel/)
    path("export/excel/", export_pembayaran_excel, name="export_pembayaran_excel"),
    path("pembayaran/export/excel/", export_pembayaran_excel),

    # Export PDF (mendukung dengan dan tanpa trailing slash)
    path("export/pdf/<str:layanan>/<int:tahun>/", export_pembayaran_pdf, name="export_pembayaran_pdf"),
    path("export/pdf/<str:layanan>/<int:tahun>", export_pembayaran_pdf),
    path("pembayaran/export/pdf/<str:layanan>/<int:tahun>/", export_pembayaran_pdf),
    path("pembayaran/export/pdf/<str:layanan>/<int:tahun>", export_pembayaran_pdf),

    # Laporan Tahunan
    path("laporan/<str:layanan>/", laporan_tahunan, name="laporan_tahunan"),

    # Pembayaran Bulanan (mendukung kedua format nama dan URL)
    path("bulanan/", PembayaranBulananView.as_view(), name="pembayaran-bulanan"),
    path("pembayaran/bulanan/", PembayaranBulananView.as_view(), name="pembayaran_bulanan"),
]
