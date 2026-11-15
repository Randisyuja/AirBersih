from django.urls import path
from apps.pembayaran.views import (
    DaftarPembayaran,
    PembayaranBulananView,
    TambahPembayaran,
    UpdatePembayaran,
    cetak_struk_thermal,
    export_pembayaran_excel,
    export_pembayaran_pdf,
    hapus_pembayaran,
    laporan_tahunan,
    load_jenis_layanan,
    pay_by_barcode_api,
    pembayaran_qr_svg,
    scan_barcode_api,
)

urlpatterns = [
    # Daftar & Form Pembayaran
    path("", DaftarPembayaran.as_view(), name="daftar_pembayaran"),
    path("tambah/", TambahPembayaran.as_view(), name="tambah_pembayaran"),
    path("<int:pk>/edit/", UpdatePembayaran.as_view(), name="edit_pembayaran"),
    path("<int:pk>/update/", UpdatePembayaran.as_view(), name="update_pembayaran"),
    path("<int:pk>/hapus/", hapus_pembayaran, name="hapus_pembayaran"),
    path("<int:pk>/delete/", hapus_pembayaran, name="delete_pembayaran"),

    # Struk Thermal Pembayaran
    path("<int:pk>/struk/", cetak_struk_thermal, name="cetak_struk_thermal"),
    path("<int:pk>/struk/qr.svg", pembayaran_qr_svg, name="pembayaran_qr_svg"),

    # Barcode Scanning & Instant Payment APIs (R2)
    path("api/scan-barcode/", scan_barcode_api, name="api_scan_barcode"),
    path("api/scan-barcode/", scan_barcode_api, name="scan_barcode_api"),
    path("api/pay-barcode/", pay_by_barcode_api, name="pay_by_barcode_api"),
    path("api/pay-barcode/", pay_by_barcode_api, name="api_pay_barcode"),

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
