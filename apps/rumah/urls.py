from django.urls import path
from apps.rumah.views import (
    DaftarRumah,
    TambahRumah,
    UpdateRumah,
    hapus_rumah,
    tambah_rumah_ajax,
)
from apps.rumah.views.excel_views import (
    export_rumah_excel,
    import_rumah_excel,
    template_rumah_excel,
)

urlpatterns = [
    path("", DaftarRumah.as_view(), name="daftar_rumah"),
    path("export/", export_rumah_excel, name="export_rumah"),
    path("import/", import_rumah_excel, name="import_rumah"),
    path("template/", template_rumah_excel, name="template_rumah"),
    path("tambah/", TambahRumah.as_view(), name="tambah_rumah"),
    path("ajax/tambah/", tambah_rumah_ajax, name="tambah_rumah_ajax"),
    path("<int:pk>/edit/", UpdateRumah.as_view(), name="edit_rumah"),
    path("<int:pk>/update/", UpdateRumah.as_view(), name="update_rumah"),
    path("<int:pk>/hapus/", hapus_rumah, name="hapus_rumah"),
    path("<int:pk>/delete/", hapus_rumah, name="delete_rumah"),
]