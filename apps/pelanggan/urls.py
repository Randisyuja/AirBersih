from django.urls import path
from apps.pelanggan.views import (
    DaftarLangganan,
    DaftarPelanggan,
    DaftarTagihan,
    DetailLangganan,
    TambahLangganan,
    TambahPelanggan,
    TambahTagihan,
    UpdateLangganan,
    UpdatePelanggan,
    UpdateTagihan,
    cetak_kartu_member,
    generate_tagihan,
    get_harga_jenis,
    hapus_langganan,
    hapus_pelanggan,
    hapus_tagihan,
    langganan_qr_svg,
)
from apps.pelanggan.views.excel_views import (
    export_langganan_excel,
    export_pelanggan_excel,
    import_langganan_excel,
    import_pelanggan_excel,
    template_langganan_excel,
    template_pelanggan_excel,
)

urlpatterns = [
    # Pelanggan
    path("", DaftarPelanggan.as_view(), name="daftar_pelanggan"),
    path("export/", export_pelanggan_excel, name="export_pelanggan"),
    path("import/", import_pelanggan_excel, name="import_pelanggan"),
    path("template/", template_pelanggan_excel, name="template_pelanggan"),
    path("tambah/", TambahPelanggan.as_view(), name="tambah_pelanggan"),
    path("<int:pk>/edit/", UpdatePelanggan.as_view(), name="edit_pelanggan"),
    path("<int:pk>/update/", UpdatePelanggan.as_view(), name="update_pelanggan"),
    path("<int:pk>/hapus/", hapus_pelanggan, name="hapus_pelanggan"),
    path("<int:pk>/delete/", hapus_pelanggan, name="delete_pelanggan"),

    # Langganan (mendukung nama langganan_create & tambah_langganan, QR & Kartu Member)
    path("langganan/", DaftarLangganan.as_view(), name="daftar_langganan"),
    path("langganan/export/", export_langganan_excel, name="export_langganan"),
    path("langganan/import/", import_langganan_excel, name="import_langganan"),
    path("langganan/template/", template_langganan_excel, name="template_langganan"),
    path("langganan/tambah/", TambahLangganan.as_view(), name="langganan_create"),
    path("langganan/create/", TambahLangganan.as_view(), name="tambah_langganan"),
    path("langganan/<int:pk>/", DetailLangganan.as_view(), name="langganan_detail"),
    path("langganan/<int:pk>/detail/", DetailLangganan.as_view(), name="detail_langganan"),
    path("langganan/<int:pk>/edit/", UpdateLangganan.as_view(), name="langganan_update"),
    path("langganan/<int:pk>/update/", UpdateLangganan.as_view(), name="update_langganan"),
    path("langganan/<int:pk>/hapus/", hapus_langganan, name="langganan_delete"),
    path("langganan/<int:pk>/delete/", hapus_langganan, name="delete_langganan"),
    path("langganan/<int:pk>/qr.svg", langganan_qr_svg, name="langganan_qr_svg"),
    path("langganan/<int:pk>/kartu-member/", cetak_kartu_member, name="cetak_kartu_member"),

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
