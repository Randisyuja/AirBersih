from django.urls import path
from apps.layanan.views import (
    DaftarLayanan,
    TambahLayanan,
    UpdateLayanan,
    hapus_layanan,
    DaftarJenisLayanan,
    TambahJenisLayanan,
    UpdateJenisLayanan,
    hapus_jenis_layanan,
)
from apps.layanan.views.excel_views import (
    export_jenis_layanan_excel,
    export_layanan_excel,
    import_jenis_layanan_excel,
    import_layanan_excel,
    template_jenis_layanan_excel,
    template_layanan_excel,
)

urlpatterns = [
    # Layanan Kategori
    path("", DaftarLayanan.as_view(), name="daftar_layanan"),
    path("export/", export_layanan_excel, name="export_layanan"),
    path("import/", import_layanan_excel, name="import_layanan"),
    path("template/", template_layanan_excel, name="template_layanan"),
    path("tambah/", TambahLayanan.as_view(), name="tambah_layanan"),
    path("<int:pk>/edit/", UpdateLayanan.as_view(), name="edit_layanan"),
    path("<int:pk>/update/", UpdateLayanan.as_view(), name="update_layanan"),
    path("<int:pk>/hapus/", hapus_layanan, name="hapus_layanan"),
    path("<int:pk>/delete/", hapus_layanan, name="delete_layanan"),

    # Jenis Layanan (Paket)
    path("jenis-layanan/", DaftarJenisLayanan.as_view(), name="daftar_jenis_layanan"),
    path("jenis-layanan/export/", export_jenis_layanan_excel, name="export_jenis_layanan"),
    path("jenis-layanan/import/", import_jenis_layanan_excel, name="import_jenis_layanan"),
    path("jenis-layanan/template/", template_jenis_layanan_excel, name="template_jenis_layanan"),
    path("jenis-layanan/tambah/", TambahJenisLayanan.as_view(), name="tambah_jenis_layanan"),
    path("jenis-layanan/<int:pk>/edit/", UpdateJenisLayanan.as_view(), name="edit_jenis_layanan"),
    path("jenis-layanan/<int:pk>/update/", UpdateJenisLayanan.as_view(), name="update_jenis_layanan"),
    path("jenis-layanan/<int:pk>/hapus/", hapus_jenis_layanan),
    path("jenis-layanan/hapus/<int:pk>/", hapus_jenis_layanan, name="hapus_jenis_layanan"),
    path("jenis-layanan/<int:pk>/delete/", hapus_jenis_layanan, name="delete_jenis_layanan"),
]
